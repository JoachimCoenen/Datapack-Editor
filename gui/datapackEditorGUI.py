from __future__ import annotations

import codecs
import dataclasses
import functools as ft
import os
import re
from dataclasses import dataclass
from typing import Optional, Iterable, overload, TypeVar, Callable, Any, Iterator, Collection, Mapping, Union, Pattern, NamedTuple, Protocol, Type

from PyQt5.QtCore import Qt, QItemSelectionModel, QModelIndex
from PyQt5.QtGui import QKeyEvent, QKeySequence, QIcon
from PyQt5.QtWidgets import QApplication, QSizePolicy

from Cat.CatPythonGUI.AutoGUI.propertyDecorators import ValidatorResult
from model.datapackContents import getEntryHandlerForFile, getEntryHandlersForFolder
from session import documents
from Cat.CatPythonGUI.AutoGUI.autoGUI import AutoGUI
from Cat.CatPythonGUI.GUI import Style, RoundedCorners, Overlap, adjustOverlap, maskCorners, CORNERS, NO_OVERLAP
from Cat.CatPythonGUI.GUI.Widgets import CatTextField, HTMLDelegate
from Cat.CatPythonGUI.GUI.codeEditor import SearchOptions, SearchMode, QsciBraceMatch, Error
from Cat.CatPythonGUI.GUI.pythonGUI import MenuItemData
from Cat.CatPythonGUI.GUI.treeBuilders import DataListBuilder, DataTreeBuilder
from Cat.Serializable import SerializedPropertyABC, SerializableContainer
from Cat.icons import icons
from Cat.utils import findall, FILE_BROWSER_DISPLAY_NAME, showInFileSystem, openOrCreate, CachedProperty
from Cat.utils.collections_ import AddToDictDecorator, getIfKeyIssubclassOrEqual, OrderedDict
from gui.lexers import mcFunctionLexer, jsonLexer
from session.documents import Document, ErrorCounts
from model.Model import Datapack
from model.pathUtils import FilePath
from session.session import getSession

mcFunctionLexer.init()  # don't delete!
jsonLexer.init()  # don't delete!


inputBoxStyle = Style({'CatBox': Style({'background': '#FFF2CC'})})
resultBoxStyle = Style({'CatBox': Style({'background': '#DAE8FC'})})


class DocumentGUIFunc(Protocol):
	def __call__(self, gui: DatapackEditorGUI, document: Document, **kwargs) -> Document:
		...


TT = TypeVar('TT')
TR = TypeVar('TR')
T2 = TypeVar('T2')


def createNewFileGUI(folderPath: FilePath, gui: DatapackEditorGUI, openFunc: Callable[[FilePath], None]):
	handlers = getEntryHandlersForFolder(folderPath, getSession().datapackData.byFolder)
	extensions = [h.extension for h in handlers]

	@dataclass
	class Context:
		extension: int = 0
		name: str = "untitled"

	def guiFunc(gui: DatapackEditorGUI, context: Context) -> Context:
		context.name = gui.textField(context.name, "name")
		context.extension = gui.radioButtonGroup(context.extension, extensions, "extension")
		return context

	context = Context()
	context, isOk = gui.askUserInput(f"new File", context, guiFunc)
	if not isOk or not context.name:
		return

	ext = extensions[context.extension]
	try:
		filePath = createNewFile(folderPath, context.name.removesuffix(ext) + ext)
		openFunc(filePath)
	except OSError as e:
		getSession().showAndLogError(e, "Cannot create file")


def createNewFile(folderPath: FilePath, name: str) -> FilePath:
	if isinstance(folderPath, tuple):
		filePath = folderPath[0], os.path.join(folderPath[1], name)
		joinedFilePath = os.path.join(*filePath)
	else:
		filePath = os.path.join(folderPath, name)
		joinedFilePath = filePath

	with openOrCreate(joinedFilePath, 'a'):
		pass  # creates the File
	return joinedFilePath


def createNewFolderGUI(folderPath: FilePath, gui: DatapackEditorGUI):
	name, ok = gui.askUserInput('New Folder', 'New folder')
	if not ok or not name:
		return

	try:
		createNewFolder(folderPath, name)
	except OSError as e:
		getSession().showAndLogError(e, "Cannot create folder")


def createNewFolder(folderPath: FilePath, name: str):
	if isinstance(folderPath, tuple):
		filePath = folderPath[0], os.path.join(folderPath[1], name)
		joinedFilePath = os.path.join(*filePath, '_ignoreMe.txt')
	else:
		filePath = os.path.join(folderPath, name)
		joinedFilePath = os.path.join(filePath, '_ignoreMe.txt')

	with openOrCreate(joinedFilePath, 'w'):
		pass  # creates the File


class ContextMenuEntries:
	@classmethod
	def separator(cls):
		return '', None

	@classmethod
	def pathItems(cls, filePath: FilePath) -> list[MenuItemData]:
		if not type(filePath) in {str, tuple, type(None)}:
			raise AssertionError(f"Expected str, tuple or None, but got {type(filePath)}")

		if filePath is not None:
			filePathJoined = filePath if type(filePath) is str else os.path.join(*filePath)
		else:
			filePathJoined = ''

		enabled = len(filePathJoined) > 0
		browserPath = filePath[0] if not os.path.exists(filePathJoined) and isinstance(filePath, tuple) else filePathJoined

		return [
			(f'show in {FILE_BROWSER_DISPLAY_NAME}', lambda bp=browserPath: showInFileSystem(bp), {'enabled': enabled}),
			(f'copy path', lambda p=filePathJoined: QApplication.clipboard().setText(os.path.normpath(p)), {'enabled': enabled}),
			(f'copy name', lambda p=filePathJoined: QApplication.clipboard().setText(os.path.basename(p)), {'enabled': enabled}),
		]

	@classmethod
	def fileItems(cls, filePath: FilePath, openFunc: Callable[[str], None], *, showSeparator: bool = True) -> list[MenuItemData]:
		entries: list[MenuItemData] = []
		entries.append(('open', lambda p=filePath: openFunc(p), {'enabled': filePath is not None}))
		if showSeparator:
			entries.append(cls.separator())
		entries.extend(cls.pathItems(filePath))
		return entries

	@classmethod
	def folderItems(cls, filePath: FilePath, isMutable: bool, gui: DatapackEditorGUI, openFunc: Callable[[FilePath], None], *, showSeparator: bool = True) -> list[MenuItemData]:
		entries: list[MenuItemData] = []
		entries.append(('new File', lambda p=filePath: createNewFileGUI(p, gui, openFunc), {'enabled': filePath is not None and isMutable}))
		if showSeparator:
			entries.append(cls.separator())
		entries.extend(cls.pathItems(filePath))
		return entries

	@classmethod
	def datapackItems(cls, datapack: Datapack, openFunc: Callable[[FilePath], None]) -> list[MenuItemData]:
		enabled = datapack is not None
		return [
			*cls.pathItems(datapack.path,),
			cls.separator(),
			(f'copy name', lambda p=datapack: QApplication.clipboard().setText(p.name), {'enabled': enabled}),
		]


def makeTextSearcher(expr: str, searchOptions: SearchOptions) -> Callable[[str], Iterator[tuple[int, int]]]:
	if searchOptions.searchMode == SearchMode.RegEx:
		flags = 0
		flags |= re.IGNORECASE if not searchOptions.isCaseSensitive else 0
		flags |= re.MULTILINE if not searchOptions.isMultiLine else 0
		exprC = re.compile(expr, flags=flags)

		def searcher(text: str) -> Iterator[tuple[int, int]]:
			yield from ((m.start(), m.end()) for m in exprC.finditer(text))
	else:
		if searchOptions.searchMode == SearchMode.UnicodeEscaped:
			expr = codecs.getdecoder("unicode_escape")(expr)[0]
		if not searchOptions.isCaseSensitive:
			expr = expr.lower()
		exprLen = len(expr)

		def searcher(text: str) -> Iterator[tuple[int, int]]:
			text = text if searchOptions.isCaseSensitive else text.lower()
			yield from ((m, m + exprLen) for m in findall(expr, text))

	return searcher


@overload
def autocompleteFromList(text: str, allChoices: Iterable[str]) -> str:
	pass


@overload
def autocompleteFromList(text: str, allChoices: Iterable[TT], getStr: Callable[[TT], str]) -> str:
	pass


def autocompleteFromList(text: str, allChoices: Iterable[Any], getStr: Callable[[Any], str] = None) -> str:
	searchStr = text.lower()
	if getStr is not None:
		lowerChoices = [(getStr(c).lower(), c) for c in allChoices]
	else:
		lowerChoices = [(c.lower(), c) for c in allChoices]

	searchStrIndices = [cl.find(searchStr) for cl, c in lowerChoices]
	filteredChoices = [(i, cl[i:], c) for i, (cl, c) in zip(searchStrIndices, lowerChoices) if i >= 0]
	loweredFilteredChoices = [cl for i, cl, c in filteredChoices]

	prefix = os.path.commonprefix(loweredFilteredChoices)
	if prefix:
		firstFilteredChoice = next(iter(filteredChoices))
		start = firstFilteredChoice[0]
		end = start + len(prefix)
		prefix = firstFilteredChoice[2][start:end]
		text = prefix
	return text


#FilterStr = NewType('FilterStr', str)
@ft.total_ordering
class FilterStr:
	def __init__(self, string: str):
		self.__string: str = string
		self.__filters: tuple[str, ...] = tuple(filter(None, map(str.strip, string.lower().split('|'))))
		self.__iter__ = self.__filters.__iter__  # speedup of call to iter(filterStr)

	@property
	def string(self) -> str:
		return self.__string

	@property
	def filters(self) -> tuple[str, ...]:
		return self.__filters

	def __str__(self) -> str:
		return self.__string

	def __repr__(self) -> str:
		return f"{type(self).__name__}({self.__string!r})"

	def __eq__(self, other: Any) -> bool:
		if isinstance(other, FilterStr):
			return self.__filters == other.__filters
		else:
			return False

	def __lt__(self, other: FilterStr) -> bool:
		if isinstance(other, FilterStr):
			return self.__filters < other.__filters
		else:
			return NotImplemented

	def __iter__(self) -> Iterator[str]:
		return self.__filters.__iter__()

	def __bool__(self) -> bool:
		return any(self.__filters)


def filterStrChoices(filterStr: FilterStr, allChoices: Collection[str]) -> Collection[str]:
	if not filterStr:
		return allChoices
	return [choice[1] for choice in ((choice.lower(), choice) for choice in allChoices) if any(f in choice[0] for f in filterStr)]
	#[choice for choice in allChoices if filterStr in choice.lower()]


def filterDictChoices(filterStr: FilterStr, allChoices: Mapping[str, TT]) -> list[TT]:
	if not filterStr:
		return list(allChoices.values())
	return [choice[1] for choice in ((  name.lower(),   item) for name, item in allChoices.items()) if any(f in choice[0] for f in filterStr)]


def filterComputedChoices(getStr: Callable[[TT], str]):
	def innerFilterComputedChoices(filterStr: FilterStr, allChoices: Collection[TT], getStr=getStr) -> Collection[TT]:
		if not filterStr:
			return allChoices
		return [choice[1] for choice in ((getStr(choice).lower(), choice) for choice in allChoices) if any(f in choice[0] for f in filterStr)]
	return innerFilterComputedChoices


FilePathSplitter = Union[Pattern, str]

LocalFilesProp = SerializedPropertyABC[Any, list[FilePath]]


class LocalFilesPropInfo(NamedTuple):
	prop: LocalFilesProp
	firstSplitter: FilePathSplitter
	folderName: str


@dataclass
class FileEntry:
	displayPath: str
	fullPath: FilePath
	index: int
	right: list[tuple[FilePath, tuple[str, ...]]]


class FileEntry2(NamedTuple):
	fullPath: FilePath
	virtualPath: str  # = dataclasses.field(compare=False)


@dataclass
class FilesTreeItem:
	# __slots__ = ('label', 'commonDepth', 'filePaths', 'isImmutable')
	label: str
	commonDepth: int = dataclasses.field(compare=False)
	filePaths: list[FileEntry2] = dataclasses.field(compare=False)

	isImmutable: bool = dataclasses.field(compare=False)
	isArchive: bool = dataclasses.field(default=False, compare=False)

	_folderPath: Optional[str] = dataclasses.field(default=None, compare=False)

	@property
	def folderPath(self) -> Optional[FilePath]:
		if self._folderPath is not None:
			return self._folderPath

		if not self.filePaths:
			return None
		fe = self.filePaths[0]
		if fe.virtualPath.endswith(fe.fullPath[1]):
			lenDiff = len(fe.virtualPath) - len(fe.fullPath[1])
			cd = self.commonDepth - lenDiff
			folderPath = fe.fullPath[0], fe.fullPath[1][:cd]
			return folderPath
		else:
			return None

	@property
	def isFile(self) -> bool:
		filePathsCount = len(self.filePaths)
		return (filePathsCount == 1 and len(getattr(self.filePaths[0], 'virtualPath', '')) == self.commonDepth - 1)


class Project:
	pass


class DatapackEditorGUI(AutoGUI):

	def searchableChoicePopup(
			self,
			value: TT,
			label: str,
			allChoices: Iterable[TT],
			getSearchStr: Optional[Callable[[TT], str]],
			labelMaker: Callable[[TT, int], str],
			iconMaker: Optional[Callable[[TT, int], Optional[QIcon]]],
			toolTipMaker: Optional[Callable[[TT, int], Optional[str]]],
			columnCount: int,
			onContextMenu: Optional[Callable[[TT, int], None]] = None,
			reevaluateAllChoices: bool = False,
			*,
			width: int = None,
			height: int = None,
	):
		allChoicesDict: OrderedDict[str, TT] = OrderedDict()

		def updateAllChoicesDict() -> None:
			allChoicesDict.clear()
			if getSearchStr is None:
				for choice in allChoices:
					allChoicesDict[choice.lower()] = choice
			else:
				for choice in allChoices:
					allChoicesDict[getSearchStr(choice).lower()] = choice

		updateAllChoicesDict()

		@dataclass
		class Context:
			"""docstring for Context"""
			index: int
			#value: TT
			filterVal: str
			filteredChoices: OrderedDict[str, TT]
			selectedValue: Optional[TT] = None
			focusEndOfText: bool = False

			selectionModel: Optional[QItemSelectionModel] = None

		def guiFunc(gui: DatapackEditorGUI, context: Context):
			def onKeyPressed(widget, event: QKeyEvent):
				key = event.key()
				if key == Qt.Key_Down:
					context.index += 1
					context.selectionModel.setCurrentIndex(context.selectionModel.model().index(context.index, 0, QModelIndex()), QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)
					result = True
				elif key == Qt.Key_Up:
					context.index -= 1
					if context.index < 0:
						context.index = len(context.filteredChoices)-1
					context.selectionModel.setCurrentIndex(context.selectionModel.model().index(context.index, 0, QModelIndex()), QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)
					result = True
				elif key == Qt.Key_Tab:
					# do Tab Completion:
					oldFilterVal = context.filterVal
					context.filterVal = autocompleteFromList(oldFilterVal, context.filteredChoices.keys())
					# if oldFilterVal != context.filterVal:
					# 	context.value = context.filterVal
					context.focusEndOfText = True
					result = True
				else:
					return False

				gui.redrawGUI()
				gui.redrawGUI()
				return result

			if reevaluateAllChoices and gui.isLastRedraw:
				updateAllChoicesDict()

			with gui.vLayout(verticalSpacing=0):
				with gui.hLayout(horizontalSpacing=0):
					oldValue = context.filterVal
					context.filterVal = gui.textField(
						context.filterVal,
						capturingTab=True,
						onKeyPressed=onKeyPressed,
						focusEndOfText=context.focusEndOfText,
						placeholderText='filter... [Ctrl+F]',
						shortcut=QKeySequence.Find,
						roundedCorners=CORNERS.NONE,
						overlap=(0, -1)
					)
					context.focusEndOfText = False

					caseFoldedFilterVal = context.filterVal.lower()
					context.filteredChoices = OrderedDict(choice for choice in allChoicesDict.items() if caseFoldedFilterVal in choice[0])

					gui.toolButton(f'{len(context.filteredChoices)} of {len(allChoicesDict)}', roundedCorners=CORNERS.NONE, overlap=(1, -1))

				if oldValue != context.filterVal:
					try:
						context.index = list(context.filteredChoices.values()).index(context.selectedValue)
					except ValueError:
						context.index = -1
				if len(context.filteredChoices) <= context.index:
					context.index = -1

				# search if filterVal is exactly in list. If so set index to its index:
				caseFoldedSelectedValue = ''
				if context.selectedValue is not None:
					caseFoldedSelectedValue = getSearchStr(context.selectedValue)

				if caseFoldedSelectedValue != caseFoldedFilterVal:
					for i, choice in enumerate(context.filteredChoices):
						if choice == caseFoldedFilterVal:
							context.index = i
							break

				treeResult = gui.tree(
					DataListBuilder(
						list(context.filteredChoices.values()),
						labelMaker=labelMaker,
						iconMaker=iconMaker,
						toolTipMaker=toolTipMaker,
						columnCount=columnCount,
						onDoubleClick=lambda x: gui.host.window().accept(),
						onContextMenu=lambda v, c: (onContextMenu(v, c) and False) or gui.redrawGUI(),
					),
					roundedCorners=CORNERS.NONE,
				)
				context.selectionModel = treeResult.selectionModel

				context.index = context.selectionModel.currentIndex().row()
				context.selectedValue = treeResult.selectedItem

				if len(context.filteredChoices) == 1:
					context.index = 0
					context.selectionModel.setCurrentIndex(context.selectionModel.model().index(context.index, 0, QModelIndex()), QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)

			return context

		context = Context(-2, '', OrderedDict(), value)
		newValue, isOk = self.popupWindow(
			context,
			guiFunc=guiFunc,
			width=width,
			height=height,
		)
		return newValue.selectedValue if isOk else value

	def filterTextField(self, value: Optional[str], allChoices: Iterable[str], showPlaceholderText: bool = True, **kwargs) -> str:
		def onKeyPressed(widget: CatTextField, event: QKeyEvent, gui=self, allChoices=allChoices):
			# if key == Qt.Key_Down:
			# 	context.index += 1
			# 	result = True
			# elif key == Qt.Key_Up:
			# 	context.index -= 1
			# 	if context.index < 0:
			# 		context.value = context.filterVal
			# 	result = True
			# elif
			if event.key() == Qt.Key_Tab:
				# do Tab Completion:
				# searchStr = widget.text().lower()
				# lowerChoices = [(c.lower(), c) for c in allChoices]
				# filteredChoices = [(cl, c) for cl, c in lowerChoices if searchStr in cl]
				# loweredFilteredChoices = [cl for cl, c in filteredChoices]
				#
				# prefix = os.path.commonprefix(loweredFilteredChoices)
				# if prefix:
				# 	prefix = next(iter(filteredChoices))[1][0:len(prefix)]
				# 	widget.setText(prefix)
				# result = True

				widget.setText(autocompleteFromList(widget.text(), allChoices))
				result = True
			else:
				return False

			# gui.redrawGUI()
			# gui.redrawGUI()
			return result
		if showPlaceholderText:
			kwargs.setdefault('placeholderText', 'filter... [Ctrl+F]')
		value = self.textField(value, capturingTab=True, onKeyPressed=onKeyPressed, **kwargs)

		return value

	def advancedFilterTextField(
			self,
			filterStr: Optional[FilterStr],
			allChoices: TT,
			*,
			getStrChoices: Callable[[-TT], Iterable[str]] = lambda x: x,
			filterFunc: Callable[[FilterStr, -TT], TR] = filterStrChoices,
			valuesName: str = 'choices',
			shortcut: Optional[QKeySequence] = QKeySequence.Find,
			roundedCorners: RoundedCorners = (True, True, False, False),
			overlap: Overlap = (0, -1),
			**kwargs
	) -> tuple[FilterStr, TR]:
		# TODO: find more descriptive name for advancedFilterTextField(...)

		def strChoicesIter(allChoices=allChoices):
			yield from getStrChoices(allChoices)

		if shortcut is not None:
			kwargs['shortcut'] = shortcut
		with self.hLayout(horizontalSpacing=0):
			filterStr = FilterStr(self.filterTextField(
				filterStr.string if filterStr is not None else None,
				strChoicesIter(),
				overlap=adjustOverlap(overlap, (None, None, 0, None)),
				roundedCorners=maskCorners(roundedCorners, CORNERS.LEFT),
				**kwargs
			))
			filteredChoices = filterFunc(filterStr, allChoices)
			self.toolButton(f'{len(filteredChoices):,} of {len(allChoices):,}', overlap=adjustOverlap(overlap, (1, None, None, None)), roundedCorners=maskCorners(roundedCorners, CORNERS.RIGHT))  #  {valuesName} shown', alignment=Qt.AlignRight)
		return filterStr, filteredChoices

	def filteredProjectsFilesTree3(
			self,
			allIncludedProjects: list[SerializableContainer],
			localLayoutFilesProps: list[LocalFilesPropInfo],
			isImmutable: Callable[[SerializableContainer], bool],

			labelMaker    : Callable[[FilesTreeItem, int], str] = lambda x, c: x.label,
			iconMaker     : Optional[Callable[[FilesTreeItem, int], Optional[QIcon]]] = lambda x, c: icons.file_code if x.isFile else icons.folderInTree,
			toolTipMaker  : Optional[Callable[[FilesTreeItem, int], Optional[str]]] = lambda x, c: (x.filePaths[0].virtualPath[:x.commonDepth] if x.filePaths and not isinstance(x.filePaths[0], FilesTreeItem) else x.label),
			columnCount   : int = 1,
			onDoubleClick : Optional[Callable[[FilesTreeItem], None]] =  None,
			onContextMenu : Optional[Callable[[FilesTreeItem, int], None]] = None,
			onCopy        : Optional[Callable[[FilesTreeItem], Optional[str]]] = None,
			onCut         : Optional[Callable[[FilesTreeItem], Optional[str]]] = None,
			onPaste       : Optional[Callable[[FilesTreeItem, str], None]] = None,
			onDelete      : Optional[Callable[[FilesTreeItem], None]] = None,
			isSelected    : Optional[Callable[[FilesTreeItem], bool]] = None,

			*,
			roundedCorners: RoundedCorners = CORNERS.NONE,
			overlap: Overlap = NO_OVERLAP
	):

		def childrenMaker(data: FilesTreeItem) -> list[FilesTreeItem]:
			filePathsCount = len(data.filePaths)
			if data.isFile or filePathsCount == 0:
				return []

			if isinstance(data.filePaths[0], FilesTreeItem):
				return data.filePaths

			children: OrderedDict[str, FilesTreeItem] = OrderedDict()

			commonDepth = data.commonDepth
			isImmutable = data.isImmutable
			for entry in data.filePaths:
				index2 = entry.virtualPath.find('/', commonDepth)
				index2 = len(entry.virtualPath) if index2 == -1 else index2
				folder = entry.virtualPath[commonDepth:index2]

				child = children.get(folder, None)
				if child is None:
					child = FilesTreeItem(folder, index2 + 1, [], isImmutable)
					children[folder] = child
				child.filePaths.append(entry)

			return sorted(children.values(), key=lambda x: (x.isFile, x.label.lower()))
			# return list(children.values())

		def getRight(fullPath: FilePath, firstSplitter: str) -> str:
			if not isinstance(fullPath, str):
				splittingPath = fullPath[1]
			else:
				splittingPath = fullPath
			return splittingPath.split(firstSplitter, 1)[-1]
		# autocomplete strings:
		allAutocompleteStrings: list[str] = []
		allFilePaths: list[FileEntry2] = []
		rootItem: FilesTreeItem = FilesTreeItem('<ROOT>', 0, allFilePaths, False)
		for proj in allIncludedProjects:
			projPrefix = proj.name + '/'
			projPrefixLen = len(projPrefix)
			projIsImmutable: bool = isImmutable(proj)
			projItem: FilesTreeItem = FilesTreeItem(proj.name, projPrefixLen, [], projIsImmutable, projIsImmutable, _folderPath=proj.path)
			for filesPropInfo in localLayoutFilesProps:
				fullPathsInProj = filesPropInfo.prop.get(proj)
				firstSplitter = filesPropInfo.firstSplitter
				virtualFolderPrefix = filesPropInfo.folderName + '/' if filesPropInfo.folderName else ''
				virtualFolderPrefix = projPrefix + virtualFolderPrefix
				filesForFolder: list[FileEntry2] = []
				folderItem: FilesTreeItem = FilesTreeItem(filesPropInfo.folderName, len(virtualFolderPrefix), filesForFolder, projIsImmutable)
				for fullPath in fullPathsInProj:
					right = getRight(fullPath, firstSplitter)
					virtualPath = virtualFolderPrefix + right

					allAutocompleteStrings.append(virtualPath)
					filesForFolder.append(FileEntry2(fullPath, virtualPath))
				if folderItem.filePaths:
					projItem.filePaths.append(folderItem)
			if projItem.filePaths:
				rootItem.filePaths.append(projItem)

		with self.vLayout(verticalSpacing=0):
			with self.hLayout(horizontalSpacing=0):
				filterStr = self.filterTextField(None, allAutocompleteStrings, overlap=adjustOverlap(overlap, (None, None, 0, 1)), roundedCorners=maskCorners(roundedCorners, CORNERS.TOP_LEFT), shortcut=QKeySequence.Find).lower()

				totalFilesCount = len(allAutocompleteStrings)
				filteredFilesCount = 0

				if filterStr:
					for projItem in rootItem.filePaths:
						for folderItem in projItem.filePaths:
							folderItem.filePaths = [fp for fp in folderItem.filePaths if filterStr in fp.virtualPath.lower()]

							filteredFilesCount += len(folderItem.filePaths)
						projItem.filePaths = [folderItem for folderItem in projItem.filePaths if folderItem.filePaths]
					rootItem.filePaths = [projItem for projItem in rootItem.filePaths if projItem.filePaths]
				else:
					filteredFilesCount = totalFilesCount

				self.toolButton(
					f'{filteredFilesCount:,} of {totalFilesCount:,}',
					overlap=adjustOverlap(overlap, (1, None, None, 1)),
					roundedCorners=maskCorners(roundedCorners, CORNERS.TOP_RIGHT)
				)  # files shown', alignment=Qt.AlignLeft)

			self.tree(
				DataTreeBuilder(
					rootItem,
					childrenMaker,
					labelMaker,
					iconMaker,
					toolTipMaker,
					columnCount,
					suppressUpdate=False,
					showRoot=False,
					onDoubleClick=onDoubleClick,
					onContextMenu=onContextMenu,
					onCopy=onCopy,
					onCut=onCut,
					onPaste=onPaste,
					onDelete=onDelete,
					isSelected=isSelected,
					getId=lambda x: x.label,
				),
				loadDeferred=True,
				roundedCorners=maskCorners(roundedCorners, CORNERS.BOTTOM),
				overlap=adjustOverlap(overlap, (None, 0, None, None))
			)

	def searchBar(self, text: Optional[str], searchExpr: Optional[str]) -> tuple[str, list[tuple[int, int]], bool, bool, SearchOptions]:
		def onGUI(gui: DatapackEditorGUI, text: Optional[str], searchExpr: Optional[str], outerGUI: DatapackEditorGUI) -> None:
			with gui.vLayout(verticalSpacing=0):
				with gui.hLayout(horizontalSpacing=0):
					#with gui.hLayout(horizontalSpacing=0):
					gui.customData['prevPressed'] = gui.toolButton(icon=icons.prev, tip='previous', overlap=(0, 0, 1, 1), parentShortcut=QKeySequence.FindPrevious)
					gui.customData['nextPressed'] = gui.toolButton(icon=icons.next, tip='next', overlap=(1, 0, 1, 1), parentShortcut=QKeySequence.FindNext)
					gui.customData['searchExpr'] = searchExpr if searchExpr is not None else gui.customData.get('searchExpr', '')
					gui.customData['searchExpr'] = gui.textField(gui.customData['searchExpr'], placeholderText='find... [Ctrl+F]', isMultiline=False, overlap=(1, 0, 1, 1), parentShortcut=QKeySequence.Find)

					searchMode = SearchMode.RegEx if gui.toolButton('.*', tip='RegEx', overlap=(1, 0, 1, 1), checkable=True) else SearchMode.Normal
					isCaseSensitive = gui.toolButton('Aa', tip='case sensitive', checkable=True, overlap=(1, -1))
					isMultiLine = False  # gui.toggleLeft(None, 'Multiline', enabled=isRegex)
					gui.customData['searchOptions'] = SearchOptions(searchMode, isCaseSensitive, isMultiLine)

					# do actual search:
					try:
						searcher = makeTextSearcher(gui.customData['searchExpr'].encode('utf-8'), gui.customData['searchOptions'])
					except Exception as e:
						errorText = str(e)
						gui.customData['searchResults'] = []
					else:
						# successfully created a searcher, so do the search:
						errorText = None
						if gui.customData['searchExpr'] == '':
							gui.customData['searchResults'] = []
						elif gui.customData.get('text') is None:
							# do nothin', bc. text is empty or not (yet) set
							pass
						else:
							gui.customData['searchResults'] = list(searcher(gui.customData['text'].encode('utf-8')))

					# display result count:
					#gui.hSeparator()
					if gui.customData['searchResults'] is not None:
						gui.toolButton(f'{len(gui.customData["searchResults"])} found', overlap=(1, -1), roundedCorners=(False, False, False, False))
				if errorText is not None:
					gui.helpBox(errorText, style='error')

			outerGUI.redrawGUI()

		searchGUI = self.subGUI(
			DatapackEditorGUI,
			guiFunc=lambda gui, text=text, searchExpr=searchExpr, outerGUI=self: onGUI(gui, text, searchExpr, outerGUI),
			suppressRedrawLogging=True
			# onInit=lambda w, document=document: onInit(w, document)
		)
		searchGUI._name = 'searchBar'
		searchGUI.customData['text'] = text
		searchGUI.redrawGUI()
		return \
			searchGUI.customData['searchExpr'], \
			searchGUI.customData['searchResults'], \
			searchGUI.customData['prevPressed'], \
			searchGUI.customData['nextPressed'], \
			searchGUI.customData['searchOptions']

	@property
	def _errorIcons(self) -> dict[str, QIcon]:
		return {
			'error': icons.errorColored,
			'warning': icons.warningColored,
			'info': icons.infoColored,
		}

	def errorsSummaryGUI(self: DatapackEditorGUI, errorCounts: documents.ErrorCounts, **kwargs):
		errorsTip = 'errors'
		warningsTip = 'warnings'
		hintsTip = 'hints'

		errorIcons = self._errorIcons

		#self.hSeparator()  # parser & config errors:
		self.label(errorIcons['error'], tip=errorsTip, **kwargs)
		self.label(f'{errorCounts.parserErrors + errorCounts.configErrors}', tip=errorsTip, **kwargs)
		#self.hSeparator()  # config warnings:
		self.label(errorIcons['warning'], tip=warningsTip, **kwargs)
		self.label(f'{errorCounts.configWarnings}', tip=warningsTip, **kwargs)
		#self.hSeparator()  # config hints:
		self.label(errorIcons['info'], tip=hintsTip, **kwargs)
		self.label(f'{errorCounts.configHints}', tip=hintsTip, **kwargs)
		#self.hSeparator()  # config hints:

	def errorsSummarySimpleGUI(self: DatapackEditorGUI, errorCounts: ErrorCounts, **kwargs):
		self.hSeparator()
		self.label(f'errors: {errorCounts.parserErrors + errorCounts.configErrors:3} | warnings: {errorCounts.configWarnings:3} | hints: {errorCounts.configHints:3}')
		self.hSeparator()

	def drawError(self, error: Error, **kwargs):
		if error.position is not None:
			positionMsg = f'at line {error.position.line + 1}, pos {error.position.column}'
		else:
			positionMsg = ''
		errorMsg = error.message
		style = getattr(error, 'style', 'error')
		with self.hLayout():
			self.helpBox(errorMsg, style=style, hasLabel=False, hSizePolicy=QSizePolicy.Expanding, **kwargs)
			self.helpBox(positionMsg, style=style, hasLabel=False, **kwargs)
		# msg = f'{errorMsg} {positionMsg}'
		# self.helpBox(msg, style=style, **kwargs)

	def drawErrors(self: DatapackEditorGUI, errors: Collection[Error], onDoubleClicked: Callable[[Error], None]):
		if errors:
			for error in errors:
				self.drawError(error, onDoubleClicked=lambda ev, error=error, gui=self: onDoubleClicked(error) or gui.redrawGUI())
				self.vSeparator()
		else:
			self.helpBox(f"Everything's fine!", style='info')

	@CachedProperty
	def _htmlDelegate(self) -> HTMLDelegate:
		return HTMLDelegate()

	def errorsList(self: DatapackEditorGUI, errors: Collection[Error], onDoubleClicked: Callable[[Error], None], **kwargs):

		def getLabel(error: Error, i: int) -> str:
			if error.position is not None:
				positionMsg = f'at line {error.position.line + 1}, pos {error.position.column}'
			else:
				positionMsg = ''
			errorMsg = error.message
			return (errorMsg, positionMsg)[i]

		errorIcons = self._errorIcons

		def getIcon(error: Error, i: int) -> Optional[QIcon]:
			if i == 0:
				return errorIcons.get(error.style)
			else:
				return None

		self.tree(
			DataListBuilder(
				errors,
				labelMaker=getLabel,
				iconMaker=getIcon,
				toolTipMaker=None,
				columnCount=2,
				onDoubleClick=onDoubleClicked,  # lambda e: onDoubleClicked(e) or self.redrawGUI(),
				getId=lambda e: e.message
			),
			headerVisible=True,
			itemDelegate=self._htmlDelegate,
			**kwargs
		)


TPythonGUI = TypeVar('TPythonGUI', bound=DatapackEditorGUI)


def drawCodeField(
		gui: DatapackEditorGUI,
		code: str,
		errors: list[Error],
		forceLocateElement: bool,
		highlightErrors: bool,
		currentCursorPos: tuple[int, int] = None,
		braceMatching: QsciBraceMatch = QsciBraceMatch.SloppyBraceMatch,
		**kwargs
) -> tuple[str, bool, tuple[int, int], bool]:
	codeFieldKwargs = {}

	if forceLocateElement and currentCursorPos is not None:
		codeFieldKwargs['cursorPosition'] = currentCursorPos

	forceLocate = False

	with gui.vLayout(verticalSpacing=0):
		# actual GUI:
		with gui.hLayout(horizontalSpacing=0):
			searchExpr, searchResults, prevPressed, nextPressed, searchOptions = gui.searchBar(code, searchExpr=None)
			highlightErrors = gui.toolButton(checked=highlightErrors, icon=icons.spellCheck, tip='highlight errors', checkable=True, overlap=(1, -1), roundedCorners=CORNERS.NONE)
			if nextPressed or prevPressed:
				forceLocate = True

		code, cursorPos = gui.advancedCodeField(
			code,
			braceMatching=braceMatching.value,
			searchResults=searchResults,
			prev=prevPressed,
			next=nextPressed,
			searchOptions=searchOptions,
			returnCursorPos=True,
			#onCursorPositionChanged=lambda a, b, g=gui: g.customData.__setitem__('currentCursorPos', (a, b)) ,
			errors=errors,
			**codeFieldKwargs,
			**kwargs
		)

	return code, highlightErrors, cursorPos, forceLocate





__documentDrawers: dict[Type[Document], DocumentGUIFunc] = {}
DocumentDrawer = AddToDictDecorator(__documentDrawers)
getDocumentDrawer = ft.partial(getIfKeyIssubclassOrEqual, __documentDrawers)
