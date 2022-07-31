import os
import re
from io import BufferedIOBase
from operator import itemgetter
from typing import Union, Protocol
from zipfile import ZipFile, BadZipFile

from Cat.extensions import processRecursively, makeSearchPath
from Cat.utils.profiling import logWarning

FilePathTpl = tuple[str, str]
FilePath = Union[str, FilePathTpl]


_normalizeDirSeparatorsTrans: dict = str.maketrans({'\\': '/'})


def normalizeDirSeparators(path: FilePath) -> FilePath:
	if isinstance(path, tuple):
		return path[0].translate(_normalizeDirSeparatorsTrans), path[1].translate(_normalizeDirSeparatorsTrans)
	else:
		return path.translate(_normalizeDirSeparatorsTrans)


def fileNameFromFilePath(path: FilePath) -> str:
	if isinstance(path, tuple):
		pathPart: str = path[1].translate(_normalizeDirSeparatorsTrans)
	else:
		pathPart: str = path.translate(_normalizeDirSeparatorsTrans)

	filename = pathPart.removesuffix('/').rpartition('/')[2]
	return filename


def extensionFromFilePath(path: FilePath) -> str:
	pathPart = path if isinstance(path, str) else path[1]
	_, ext = os.path.splitext(pathPart)
	return ext


def getAllFilesFromSearchPath(rootFolders: Union[str, list[str]], folderFilter: str, zipPathFilter: str, extensions: Union[str, tuple[str, ...]], excludes: Union[str, tuple[str, ...]] = None) -> list[FilePath]:
	filePaths = []

	def handleFile(filename: str):
		nonlocal filePaths
		if (not extensions or filename.endswith(extensions)) and (not excludes or not filename.endswith(excludes)):
			try:
				filename = normalizeDirSeparators(filename)
				filePaths.append(filename)
			except (FileNotFoundError, PermissionError) as e:
				logWarning(e)

	if isinstance(rootFolders, str):
		rootFolders = [rootFolders]

	for rootFolder in rootFolders:
		if not os.path.exists(rootFolder):
			continue
		if os.path.isdir(rootFolder):
			searchResult = processRecursively(rootFolder, folderFilter, handleFile)
		else:
			srcFolder = ''
			_, finalFolderFilter = makeSearchPath(srcFolder, zipPathFilter)
			finalFileFilter = finalFolderFilter + r'[/\\]?(?!\.\.)[^/\\]*'

			try:
				library = ZipFile(rootFolder, 'r')
			except (FileNotFoundError, PermissionError) as e:
				logWarning(e)
			else:
				for filename in library.namelist():
					if re.fullmatch(finalFileFilter, filename):
						if (not extensions or filename.endswith(extensions)) and (not excludes or not filename.endswith(excludes)):
							filename = normalizeDirSeparators(filename)
							filePaths.append((rootFolder, filename,))

	filePaths.sort()
	return filePaths


def getAllTimestampsFromSearchPath(rootFolders: Union[str, list[str]], folderFilter: str, extensions: Union[str, tuple[str]], excludes: Union[str, tuple[str]] = None) -> list[float]:
	timeStamps: dict[str, float] = {}  #OrderedMultiDict()

	def handleFile(filename):
		nonlocal timeStamps
		if filename.endswith(extensions) and (not excludes or not filename.endswith(excludes)):
			try:
				filename = normalizeDirSeparators(filename)
				timeStamp = os.path.getmtime(filename)
				timeStamps[filename] = timeStamp
			except (FileNotFoundError, PermissionError) as e:
				logWarning(e)

	if isinstance(rootFolders, str):
		rootFolders = [rootFolders]

	for rootFolder in rootFolders:
		if not os.path.exists(rootFolder):
			continue
		if os.path.isdir(rootFolder):
			searchResult = processRecursively(rootFolder, folderFilter, handleFile)
		else:
			timeStamps[rootFolder] = os.path.getmtime(rootFolder)

	result: list[float] = [v[1] for v in sorted(timeStamps.items(), key=itemgetter(0))]
	return result


class Archive(Protocol):
	def open(self, name: str, mode: str = "r") -> BufferedIOBase:
		pass

	def remove(self, filename: str):
		pass

	def close(self):
		pass


class ArchiveFilePool:
	def __init__(self):
		self._openedArchives: dict[str, Archive] = {}

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.closeAll()

	def closeAll(self):
		errors = []
		for path in list(self._openedArchives.keys()):
			try:
				self.closeArchive(path)
			except Exception as e:
				errors.append(e)
		if errors:
			raise RuntimeError(errors)

	def closeArchive(self, path: str):
		absPath = os.path.abspath(path)
		normPath = absPath
		file = self._openedArchives.get(normPath, None)
		if file is None:
			return
		try:
			file.close()
		except Exception:
			raise
		else:
			del self._openedArchives[normPath]

	def _openArchive(self, normPath: str, mode: str) -> Archive:
		return NotImplemented

	def _getOrOpenArchive(self, path: str, mode: str) -> Archive:
		absPath = os.path.abspath(path)
		normPath = absPath
		if normPath not in self._openedArchives:
			os.makedirs(os.path.dirname(path), exist_ok=True)
			self._openedArchives[normPath] = self._openArchive(normPath, mode)
		return self._openedArchives[normPath]

	def readFileInArchive(self, zipPath: str, relFilePath: str) -> BufferedIOBase:
		archive = self._getOrOpenArchive(zipPath, 'r')
		return archive.open(relFilePath, 'r')

	def replaceFileInArchive(self, zipPath: str, relFilePath: str) -> BufferedIOBase:
		archive = self._getOrOpenArchive(zipPath, 'a')
		try:
			archive.remove(relFilePath)
		except KeyError:
			pass
		return archive.open(relFilePath, 'w')


# class CatContainerFilePool(ArchiveFilePool):
# 	def _openArchive(self, normPath: str, mode: str) -> CatContainerFile:
# 		try:
# 			return CatContainerFile(normPath, mode)
# 		except BadCCFile as e:
# 			e.args = (*e.args, normPath)
# 			raise


class ZipFilePool(ArchiveFilePool):
	def _openArchive(self, normPath: str, mode: str) -> ZipFile:
		try:
			return ZipFile(normPath, mode)
		except BadZipFile as e:
			e.args = (*e.args, normPath)
			raise


def loadTextFile(filePath: FilePath, archiveFilePool: ArchiveFilePool, encoding: str = 'utf-8', errors: str = 'ignore') -> str:
	text = None
	if isinstance(filePath, (str, bytes)):
		# path is a normal file:
		with open(filePath) as f:  # open file
			text = f.read()
	elif os.path.isdir(filePath[0]):
		with open(f'{filePath[0]}/{filePath[1]}', encoding=encoding, errors=errors) as f:  # open file
			text = f.read()
	else:
		# path contains a .jar file:
		zipPath = filePath[0]
		pathInZip = filePath[1]
		filePath = f'{zipPath}/{pathInZip}'
		with archiveFilePool.readFileInArchive(zipPath, pathInZip) as f:
			text = f.read()

	if isinstance(text, bytes):
		decodedText = text.decode(encoding, errors='replace')
	else:
		decodedText = text

	return decodedText


def loadBinaryFile(filePath: FilePath, archiveFilePool: ArchiveFilePool) -> bytes:
	contents = None
	if isinstance(filePath, (str, bytes)):
		# path is a normal file:
		with open(filePath, 'rb') as f:  # open file
			contents = f.read()
	elif os.path.isdir(filePath[0]):
		with open(f'{filePath[0]}/{filePath[1]}', 'rb') as f:  # open file
			contents = f.read()
	else:
		# path contains a .jar file:
		zipPath = filePath[0]
		pathInZip = filePath[1]
		filePath = f'{zipPath}/{pathInZip}'
		with archiveFilePool.readFileInArchive(zipPath, pathInZip) as f:
			contents = f.read()
	return contents


def getMTimeForFilePath(filePath: FilePath) -> float:
	if isinstance(filePath, (str, bytes)):
		# path is a normal file:
		fullFilePath = filePath
	elif os.path.isdir(filePath[0]):
		fullFilePath = f'{filePath[0]}/{filePath[1]}'
	else:
		# path contains a .jar file:
		fullFilePath = filePath[0]  # the zipPath

	return os.path.getmtime(fullFilePath)
