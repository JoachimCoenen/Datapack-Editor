from __future__ import annotations
import os
import re
from io import BufferedIOBase
from operator import itemgetter
from typing import Callable, Literal, NamedTuple, Optional, Protocol, Union, AnyStr, TypeVar
from zipfile import BadZipFile, ZipFile

from cat.utils import PLATFORM_IS_WINDOWS
from cat.processFiles import makeSearchPath, processRecursively
from cat.utils.collections_ import Stack
from cat.utils.profiling import logWarning


FilePathStr = str
FilePathTpl = tuple[str, str]
FilePath = Union[FilePathStr, FilePathTpl]

_TFilePath = TypeVar('_TFilePath', FilePathStr, FilePathTpl)


_normalizeDirSeparatorsTrans: dict = str.maketrans({'\\': '/'})


def normalizeDirSeparatorsStr(path: FilePathStr) -> FilePathStr:
	return path.translate(_normalizeDirSeparatorsTrans)


def normalizeDirSeparatorsTpl(path: FilePathTpl) -> FilePathTpl:
	return path[0].translate(_normalizeDirSeparatorsTrans), path[1].translate(_normalizeDirSeparatorsTrans)


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


def dirFromFilePath(path: FilePath) -> FilePath:
	if isinstance(path, tuple):
		p1 = path[1].removesuffix('/').rpartition('/')[0]
		p0 = path[0]
		return p0 if not p1 else (p0, p1)
	else:
		return path.removesuffix('/').rpartition('/')[0]


def extensionFromFilePath(path: FilePath) -> str:
	pathPart = path if isinstance(path, str) else path[1]
	_, ext = os.path.splitext(pathPart)
	return ext


def splitPath(path: FilePathStr, projPath: str) -> Optional[FilePathTpl]:
	if path.startswith(projPath):
		jf = (projPath, path[len(projPath):].lstrip('/'))
		return jf
	else:
		return None


def unitePathTpl(path: FilePathTpl) -> FilePathStr:
	return f"{path[0].rstrip('/')}/{path[1].lstrip('/')}"


def unitePath(path: FilePath) -> FilePathStr:
	if isinstance(path, tuple):
		return f"{path[0].rstrip('/')}/{path[1].lstrip('/')}"
	return path


def joinFilePath(path: _TFilePath, part: str) -> _TFilePath:
	if isinstance(path, tuple):
		return path[0], f"{path[1].removesuffix('/')}/{part.removeprefix('/')}"
	else:
		return f"{path.removesuffix('/')}/{part.removeprefix('/')}"


def toDisplayPath(path: FilePath) -> str:
	if isinstance(path, tuple):
		return f"{path[0].removesuffix('/')}/!{path[1].removeprefix('/')}"
	else:
		return path


def fromDisplayPath(path: str) -> FilePath:
	l, _, r = path.partition('!')
	if r:
		return l, r
	else:
		return l


def isExcludedDirectory(relDirPath: str, excludedDirs: tuple[str, ...]) -> bool:
	if not excludedDirs:
		return False
	relDirPath = normalizeDirSeparatorsStr(relDirPath)
	relDirPath = f'/{relDirPath.strip("/")}/'
	return relDirPath.startswith(excludedDirs)


if PLATFORM_IS_WINDOWS:
	def _getShortPathName(long_name: AnyStr) -> AnyStr:
		"""
		Coerces windows into dealing with long paths.
		"""
		if isinstance(long_name, bytes):
			long_name = long_name.replace(b'/', b'\\')
			if not long_name.startswith('\\\\?\\'):
				long_name = b'\\\\?\\' + os.path.abspath(long_name)
		else:
			long_name = long_name.replace('/', '\\')
			if not long_name.startswith('\\\\?\\'):
				long_name = '\\\\?\\' + os.path.abspath(long_name)
		return long_name


	def getSafeFileName(filename: AnyStr) -> AnyStr:
		if len(filename) > 259:
			shortName = _getShortPathName(filename)
			return shortName
		return filename

	def getmtimeSafe(filename: AnyStr) -> float:
		safeFilename = getSafeFileName(filename)
		return os.path.getmtime(safeFilename)
else:
	def getSafeFileName(filename: AnyStr) -> AnyStr:
		return filename

	getmtimeSafe = os.path.getmtime


def getAllFilesFromSearchPaths(
		rootFolders: Union[str, list[str]],
		folderFilter: SearchPath,
		zipPathFilter: str,
		extensions: Union[str, tuple[str, ...]],
		excludes: Union[str, tuple[str, ...]] = None,
		*,
		onError: Optional[Callable[[OSError], None]] = logWarning
) -> list[FilePath]:

	if isinstance(rootFolders, str):
		rootFolders = (rootFolders,)

	filePaths: list[FilePath] = []
	for rootFolder in rootFolders:
		filePaths.extend(getAllFilesFromSearchPath(rootFolder, folderFilter, zipPathFilter, extensions, excludes, onError=onError))

	filePaths.sort()
	return filePaths


def getAllFilesFromSearchPath(
		rootFolder: str,
		folderFilter: SearchPath,
		zipPathFilter: str,
		extensions: Union[str, tuple[str, ...]],
		excludes: Union[str, tuple[str, ...]] = None,
		*,
		onError: Optional[Callable[[OSError], None]] = logWarning
) -> list[FilePath]:
	if not os.path.exists(rootFolder):
		return []
	if os.path.isdir(rootFolder):
		return _internalGetAllFilesFromFolder(rootFolder, folderFilter, extensions, excludes)
	elif os.path.isfile(rootFolder):
		return _internalGetAllFilesFoldersFromArchive(rootFolder, zipPathFilter, extensions, excludes, onError=onError)[0]
	return []


def getAllFilesAndTimestampsFromSearchPaths(
		rootFolders: Union[str, list[str]],
		folderFilter: SearchPath,
		zipPathFilter: str,
		extensions: Union[str, tuple[str, ...]],
		excludes: Union[str, tuple[str, ...]] = None,
		*,
		onError: Optional[Callable[[OSError], None]] = logWarning
) -> list[SimpleFileInfo]:

	if isinstance(rootFolders, str):
		rootFolders = (rootFolders,)

	filePaths: list[SimpleFileInfo] = []
	for rootFolder in rootFolders:
		filePaths.extend(getAllFilesAndTimestampsFromSearchPath(rootFolder, folderFilter, zipPathFilter, extensions, excludes, onError=onError))

	filePaths.sort()
	return filePaths


def getAllFilesAndTimestampsFromSearchPath(
		rootFolder: str,
		folderFilter: SearchPath,
		zipPathFilter: str,
		extensions: Union[str, tuple[str, ...]],
		excludes: Union[str, tuple[str, ...]] = None,
		*,
		onError: Optional[Callable[[OSError], None]] = logWarning
) -> list[SimpleFileInfo]:
	if not os.path.exists(rootFolder):
		return []
	if os.path.isdir(rootFolder):
		return _internalGetAllFilesAndTimestampsFromFolder(rootFolder, folderFilter, extensions, excludes, onError=onError)
	elif os.path.isfile(rootFolder):
		return _internalGetAllFilesAndTimestampsFromArchive(rootFolder, zipPathFilter, extensions, excludes, onError=onError)
	return []


def getAllFilesFromFolder(rootFolder: str, folderFilter: SearchPath, extensions: Union[str, tuple[str, ...]], excludes: Union[str, tuple[str, ...]] = None) -> list[FilePathTpl]:
	if not folderFilter.divider:
		raise ValueError("folderFilter.divider cannot be empty")
	if os.path.exists(rootFolder) and os.path.isdir(rootFolder):
		return _internalGetAllFilesFromFolder(rootFolder, folderFilter, extensions, excludes)
	return []


def getAllFilesFoldersFromFolder(rootFolder: str, divider: str, *, excludedDirs: tuple[str, ...]) -> tuple[list[FilePathTpl],  list[FilePathTpl]]:
	if not divider:
		raise ValueError("folderFilter.divider cannot be empty")
	if os.path.exists(rootFolder) and os.path.isdir(rootFolder):
		divider = normalizeDirSeparatorsStr(divider)
		return _internalGetAllFilesFoldersFromFolder(rootFolder, divider, excludedDirs)
	return [], []


def _internalGetAllFilesFoldersFromFolder(rootFolder: str, divider: str, excludedFolders: tuple[str, ...]) -> tuple[list[FilePathTpl],  list[FilePathTpl]]:
	filePaths = []
	folderPaths = []

	scanners = Stack()
	scanners.push(os.scandir(rootFolder))
	scanner = None
	try:
		while scanners:
			scanner = scanners.pop()
			entry: os.DirEntry
			while (entry := next(scanner, None)) is not None:
				if entry.is_file():
					prefix, div, suffix = normalizeDirSeparatorsStr(entry.path).rpartition(divider)
					filePaths.append((prefix + div, suffix.lstrip('/'),))
				elif entry.is_dir():
					prefix, div, suffix = normalizeDirSeparatorsStr(entry.path).rpartition(divider)
					if not isExcludedDirectory(suffix, excludedFolders):
						folderPaths.append((prefix + div, suffix.lstrip('/') + '/',))
						scanners.push(scanner)
						scanner = os.scandir(entry.path)
			scanner.close()
	except Exception:
		if scanner is not None:
			scanner.close()
		for scanner in scanners:
			scanner.close()
		scanners.clear()
		raise

	filePaths.sort()
	folderPaths.sort()
	return filePaths, folderPaths


def getAllFilesFoldersFromArchive(
		rootFolder: str,
		zipPathFilter: str,
		extensions: Union[str, tuple[str, ...]],
		excludes: Union[str, tuple[str, ...]] = None,
		*,
		onError: Optional[Callable[[OSError], None]] = logWarning
) -> tuple[list[FilePathTpl],  list[FilePathTpl]]:
	if os.path.exists(rootFolder) and os.path.isfile(rootFolder):
		return _internalGetAllFilesFoldersFromArchive(rootFolder, zipPathFilter, extensions, excludes, onError=onError)
	return [], []


def _internalGetAllFilesFromFolder(rootFolder: str, folderFilter: SearchPath, extensions: Union[str, tuple[str, ...]], excludes: Union[str, tuple[str, ...]] = None) -> list[FilePathTpl]:
	divider = folderFilter.divider

	filePaths = []

	def handleFile(filename: str):
		nonlocal filePaths
		if (not extensions or filename.endswith(extensions)) and (not excludes or not filename.endswith(excludes)):
			filename = normalizeDirSeparatorsStr(filename)
			prefix, div, suffix = filename.rpartition(divider)
			filePaths.append((prefix + div, suffix,))

	processRecursively(rootFolder, folderFilter.path, handleFile)
	filePaths.sort()
	return filePaths


def _internalGetAllFilesFoldersFromArchive(
		rootFolder: str,
		zipPathFilter: str,
		extensions: Union[str, tuple[str, ...]],
		excludes: Union[str, tuple[str, ...]] = None,
		*,
		onError: Optional[Callable[[OSError], None]] = logWarning
) -> tuple[list[FilePathTpl],  list[FilePathTpl]]:
	filePaths = []
	folderPaths = []

	def handleFileZip(zipPath: str, filename: str):
		nonlocal filePaths
		if (not extensions or filename.endswith(extensions)) and (not excludes or not filename.endswith(excludes)):
			filename = normalizeDirSeparatorsStr(filename)
			if filename.endswith('/'):
				folderPaths.append((zipPath, filename,))
			else:
				filePaths.append((zipPath, filename,))

	try:
		_processZip(rootFolder, zipPathFilter, handleFileZip)
	except OSError as e:
		if onError is not None:
			onError(e)
	folderPaths.sort()
	filePaths.sort()
	return filePaths, folderPaths


def _internalGetAllFilesAndTimestampsFromFolder(rootFolder: str, folderFilter: SearchPath, extensions: Union[str, tuple[str, ...]], excludes: Union[str, tuple[str, ...]] = None, *, onError: Optional[Callable[[OSError], None]] = logWarning) -> list[SimpleFileInfo]:
	divider = folderFilter.divider
	filePaths: list[SimpleFileInfo] = []

	def handleFile(filename: str):
		nonlocal filePaths
		if (not extensions or filename.endswith(extensions)) and (not excludes or not filename.endswith(excludes)):
			try:
				filename = normalizeDirSeparatorsStr(filename)
				prefix, div, suffix = filename.rpartition(divider)
				filePathTpl = (prefix + div, suffix,)
				timeStamp = getmtimeSafe(filename)
				filePaths.append(SimpleFileInfo(filePathTpl, timeStamp))
			except OSError as e:
				if onError is not None:
					onError(e)
				else:
					raise

	processRecursively(rootFolder, folderFilter.path, handleFile)
	filePaths.sort(key=itemgetter(0))
	return filePaths


def _internalGetAllFilesAndTimestampsFromArchive(
		rootFolder: str,
		zipPathFilter: str,
		extensions: Union[str, tuple[str, ...]],
		excludes: Union[str, tuple[str, ...]] = None,
		*,
		onError: Optional[Callable[[OSError], None]] = logWarning
) -> list[SimpleFileInfo]:
	timeStamp = getmtimeSafe(rootFolder)
	filePaths: list[SimpleFileInfo] = []

	def handleFileZip(zipPath: str, filename: str):
		nonlocal filePaths
		if (not extensions or filename.endswith(extensions)) and (not excludes or not filename.endswith(excludes)):
			filename = normalizeDirSeparatorsStr(filename)
			filePaths.append(SimpleFileInfo((zipPath, filename,), timeStamp))

	try:
		_processZip(rootFolder, zipPathFilter, handleFileZip)
	except OSError as e:
		if onError is not None:
			onError(e)
	filePaths.sort(key=itemgetter(0))
	return filePaths


def _processZip(rootFolder: str, zipPathFilter: str,  handleFile: Callable[[str, str], None]):
	_, finalFolderFilter = makeSearchPath('', zipPathFilter)
	finalFileFilter = re.compile(finalFolderFilter + r'[/\\]?(?!\.\.)[^/\\]*')
	library = ZipFile(rootFolder, 'r')
	for filename in library.namelist():
		if finalFileFilter.fullmatch(filename):
			handleFile(rootFolder, filename)


def getAllTimestampsFromSearchPath(
		rootFolders: Union[str, list[str]],
		folderFilter: str,
		extensions: Union[str, tuple[str, ...]],
		excludes: Union[str, tuple[str, ...]] = None,
		*,
		onError: Optional[Callable[[OSError], None]] = logWarning
) -> list[float]:
	timeStamps: dict[str, float] = {}  #OrderedMultiDict()

	def handleFile(filename: str):
		nonlocal timeStamps
		if filename.endswith(extensions) and (not excludes or not filename.endswith(excludes)):
			try:
				filename = normalizeDirSeparatorsStr(filename)
				timeStamp = getmtimeSafe(filename)
				timeStamps[filename] = timeStamp
			except OSError as e:
				if onError is not None:
					onError(e)
				else:
					raise

	if isinstance(rootFolders, str):
		rootFolders = [rootFolders]

	for rootFolder in rootFolders:
		if not os.path.exists(rootFolder):
			continue
		if os.path.isdir(rootFolder):
			processRecursively(rootFolder, folderFilter, handleFile)
		else:
			timeStamps[rootFolder] = getmtimeSafe(rootFolder)

	return list(map(itemgetter(1), sorted(timeStamps.items(), key=itemgetter(0))))


class Archive(Protocol):
	def open(self, name: str, mode: str = "r") -> BufferedIOBase:
		pass

	def remove(self, filename: str):
		pass

	def close(self):
		pass


_ZipFileMode = Literal["r", "w", "x", "a"]


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

	def _openArchive(self, normPath: str, mode: _ZipFileMode) -> Archive:
		raise NotImplementedError()

	def _getOrOpenArchive(self, path: str, mode: _ZipFileMode) -> Archive:
		safePath = getSafeFileName(os.path.abspath(path))
		if safePath not in self._openedArchives:
			os.makedirs(os.path.dirname(path), exist_ok=True)
			self._openedArchives[safePath] = self._openArchive(safePath, mode)
		return self._openedArchives[safePath]

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


class ZipFilePool(ArchiveFilePool):
	def _openArchive(self, normPath: str, mode: Literal["r", "w", "x", "a"]) -> ZipFile:
		try:
			return ZipFile(normPath, mode)
		except BadZipFile as e:
			e.args = (*e.args, normPath)
			raise


def loadTextFile(filePath: FilePath, archiveFilePool: ArchiveFilePool, encoding: str = 'utf-8', errors: str = 'ignore') -> str:
	text = None
	if isinstance(filePath, (str, bytes)):
		# path is a normal file:
		with open(filePath, encoding=encoding, errors=errors) as f:  # open file
			text = f.read()
	elif os.path.isdir(filePath[0]):
		with open(unitePathTpl(filePath), encoding=encoding, errors=errors) as f:  # open file
			text = f.read()
	else:
		# path contains a .jar file:
		zipPath = filePath[0]
		pathInZip = filePath[1]
		filePath = f'{zipPath}/{pathInZip}'
		with archiveFilePool.readFileInArchive(zipPath, pathInZip) as f:
			text = f.read()

	if isinstance(text, bytes):
		decodedText = text.decode(encoding, errors=errors)
	else:
		decodedText = text

	return decodedText


def loadBinaryFile(filePath: FilePath, archiveFilePool: ArchiveFilePool) -> bytes:
	contents = None
	if isinstance(filePath, (str, bytes)):
		# path is a normal file:
		with open(getSafeFileName(filePath), 'rb') as f:  # open file
			contents = f.read()
	elif os.path.isdir(getSafeFileName(filePath[0])):
		with open(getSafeFileName(f'{filePath[0]}/{filePath[1]}'), 'rb') as f:  # open file
			contents = f.read()
	else:
		# path contains a .jar file:
		zipPath = filePath[0]  # readFileInArchive(...) already uses getSafeFileName() so we don't need to do it here.
		pathInZip = filePath[1]
		with archiveFilePool.readFileInArchive(zipPath, pathInZip) as f:
			contents = f.read()
	return contents


class SearchPath(NamedTuple):
	path: str
	divider: str


class SimpleFileInfo(NamedTuple):
	path: FilePathTpl
	timestamp: float


def getMTimeForFilePath(filePath: FilePath) -> float:
	if isinstance(filePath, (str, bytes)):
		# path is a normal file:
		return getmtimeSafe(filePath)
	else:
		return getMTimeForFilePathTpl(filePath)


def getMTimeForFilePathTpl(filePath: FilePathTpl) -> float:
	safeDirPath = getSafeFileName(filePath[0])
	if os.path.isdir(safeDirPath):
		return getmtimeSafe(f'{filePath[0]}/{filePath[1]}')
	else:
		# path contains a .jar, .zip, etc file:
		return os.path.getmtime(safeDirPath)  # the zipPath


__all__ = [
	'FilePathStr',
	'FilePathTpl',
	'FilePath',

	'normalizeDirSeparatorsStr',
	'normalizeDirSeparatorsTpl',
	'normalizeDirSeparators',

	'fileNameFromFilePath',
	'dirFromFilePath',
	'extensionFromFilePath',

	'splitPath',
	'unitePathTpl',
	'unitePath',
	'joinFilePath',
	'toDisplayPath',
	'fromDisplayPath',

	'getAllFilesFromSearchPaths',
	'getAllFilesFromSearchPath',
	'getAllFilesAndTimestampsFromSearchPaths',
	'getAllFilesAndTimestampsFromSearchPath',
	'getAllFilesFromFolder',
	'getAllFilesFoldersFromFolder',
	'getAllFilesFoldersFromArchive',
	'getAllTimestampsFromSearchPath',

	'Archive',
	'ArchiveFilePool',
	'ZipFilePool',
	'loadTextFile',
	'loadBinaryFile',
	'SearchPath',
	'SimpleFileInfo',
	'getMTimeForFilePath',
	'getMTimeForFilePathTpl',
]