import os
import threading
from collections import defaultdict
from typing import Optional, Mapping

from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers import Observer
from watchdog.observers.api import ObservedWatch

from Cat.utils.logging_ import logInfo, logDebug


class _Watches:
	def __init__(self):
		self._byPath: dict[str, dict[str, FileSystemEventHandler]] = defaultdict(dict)
		self._byId: dict[str, dict[str, FileSystemEventHandler]] = defaultdict(dict)

	def getByPath(self, path: str) -> Optional[Mapping[str, FileSystemEventHandler]]:
		return self._byPath.get(path)

	def getById(self, handlerId: str) -> Optional[Mapping[str, FileSystemEventHandler]]:
		return self._byId.get(handlerId)

	def get(self, handlerId: str, path: str) -> Optional[FileSystemEventHandler]:
		return (self._byPath.get(path) or {}).get(handlerId)

	def set(self, handlerId: str, path: str, handler: FileSystemEventHandler) -> None:
		self._byPath[path][handlerId] = handler
		self._byId[handlerId][path] = handler

	def pop(self, handlerId: str, path: str) -> Optional[FileSystemEventHandler]:
		handler = self._byPath[path].pop(handlerId, None)
		self._byId[handlerId].pop(path, None)
		return handler


class _CombinedEventHandler(FileSystemEventHandler):
	def __init__(self, path: str, handlers: _Watches):
		super().__init__()
		self._path: str = path
		self._handlers: _Watches = handlers

	def dispatch(self, event: FileSystemEvent):
		handlers = self._handlers.getByPath(self._path)
		if handlers is not None:
			for handler in handlers.values():
				handler.dispatch(event)


class FilesystemObserver:
	def __init__(self):
		self.__observer = Observer()
		self._handlers: _Watches = _Watches()
		self._lock = threading.RLock()

	def _getKey(self, path: str) -> str:
		return os.path.normpath(path)

	def reschedule(self, handlerId: str, oldPath: str, newPath: str, handler: FileSystemEventHandler):
		with self._lock:
			self._reschedule(handlerId, self._getKey(oldPath), self._getKey(newPath), handler)

	def schedule(self, handlerId: str, path: str, handler: FileSystemEventHandler):
		with self._lock:
			self._schedule(handlerId, self._getKey(path), handler)

	def unschedule(self, handlerId: str, path: str):
		with self._lock:
			self._unschedule(handlerId, self._getKey(path))

	def _reschedule(self, handlerId: str, oldPath: str, newPath: str, handler: FileSystemEventHandler):
		if oldPath != newPath:
			self._unschedule(handlerId, oldPath)
			self._schedule(handlerId, newPath, handler)

	def _rescheduleAll(self, handlerId: str, path: str, handler: FileSystemEventHandler):
		self._unschedule(handlerId, path)
		oldHandlers = self._handlers.getById(handlerId)
		for oldPath in oldHandlers:
			if oldPath != path:
				self._unschedule(handlerId, oldPath)
			else:
				pass
		self._schedule(handlerId, path, handler)

	def _schedule(self, handlerId: str, path: str, handler: FileSystemEventHandler):
		self._handlers.set(handlerId, path, handler)
		if not self.__observer._handlers.get(ObservedWatch(path, True), None):
			try:
				event_handler = _CombinedEventHandler(path, self._handlers)
				self.__observer.schedule(event_handler, path, True)
			except FileNotFoundError as e:
				logDebug(e)
			except OSError as e:
				logInfo(e)

	def _unschedule(self, handlerId: str, path: str):
		handler = self._handlers.pop(handlerId, path)
		if handler is not None:
			if not self._handlers.getByPath(path):
				observedWatch = ObservedWatch(path, True)
				if observedWatch in self.__observer._emitter_for_watch:
					self.__observer.unschedule(observedWatch)
				self.__observer._handlers.pop(observedWatch, None)  # safety net, necessary when path was invalid while scheduling.

	def __del__(self):
		with self._lock:
			if self.__observer.is_alive():
				self.__observer.stop()

	def __enter__(self):
		with self._lock:
			self.__observer.start()

	def __exit__(self, exc_type, exc_val, exc_tb):
		with self._lock:
			self.__observer.stop()


FILESYSTEM_OBSERVER: FilesystemObserver = FilesystemObserver()  # only one observer per application!

__all__ = [
	'FILESYSTEM_OBSERVER'
]