from __future__ import annotations

import codecs
import dataclasses
import functools as ft
import os
import re
from dataclasses import dataclass
from operator import attrgetter
from typing import Optional, Iterable, overload, TypeVar, Callable, Any, Iterator, Collection, Mapping, Union, Pattern, NamedTuple, Protocol, Type, Generic

from PyQt5.QtCore import Qt, QItemSelectionModel, QModelIndex
from PyQt5.QtGui import QKeyEvent, QKeySequence, QIcon
from PyQt5.QtWidgets import QApplication, QWidget, QSizePolicy

import documents
from Cat.CatPythonGUI.AutoGUI.autoGUI import AutoGUI
from Cat.CatPythonGUI.GUI import Style, RoundedCorners, Overlap, adjustOverlap, maskCorners, CORNERS, NO_OVERLAP, NO_MARGINS
from Cat.CatPythonGUI.GUI.Widgets import CatTextField
from Cat.CatPythonGUI.GUI.catWidgetMixins import CatFramedWidgetMixin
from Cat.CatPythonGUI.GUI.codeEditor import SearchOptions, SearchMode, QsciBraceMatch, Error
from Cat.CatPythonGUI.GUI.pythonGUI import MenuItemData, PythonGUIWidget
from Cat.CatPythonGUI.GUI.treeBuilders import DataListBuilder, DataHeaderBuilder, DataTreeBuilder
from Cat.Serializable import SerializedPropertyABC, SerializableContainer
from Cat.icons import icons
from Cat.utils import Deprecated, findall, FILE_BROWSER_DISPLAY_NAME, showInFileSystem, Maybe, format_full_exc
from Cat.utils.abc import abstractmethod
from Cat.utils.collections import AddToDictDecorator, getIfKeyIssubclassOrEqual, OrderedDict
from Cat.utils.profiling import logError
from documents import Document, ErrorCounts
from gui.mcFunctionLexer import LexerMCFunction
from model.Model import Datapack
from model.pathUtils import FilePath

inputBoxStyle = Style({'CatBox': Style({'background': '#FFF2CC'})})
resultBoxStyle = Style({'CatBox': Style({'background': '#DAE8FC'})})


class DocumentGUIFunc(Protocol):
	def __call__(self, gui: DatapackEditorGUI, document: Document, **kwargs) -> Document:
		...


TT = TypeVar('TT')
TR = TypeVar('TR')
T2 = TypeVar('T2')


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
	def datapackItems(cls, datapack: Datapack, openFunc: Callable[[FilePath], None]) -> list[MenuItemData]:
		enabled = datapack is not None
		return [
			*cls.pathItems(datapack.path,),
			cls.separator(),
			(f'copy name', lambda p=datapack: QApplication.clipboard().setText(p.name), {'enabled': enabled}),
		]

	@classmethod
	def mvnActions(cls, gui: DatapackEditorGUI, project: Project) -> list[MenuItemData]:
		return [
			('Install',       lambda p=project: p.maven.mvnInstall(), {'enabled': project is not None and project.maven.isValid}),
			('Clean',         lambda p=project: p.maven.mvnClean(), {'enabled': project is not None and project.maven.isValid}),
			('Clean Install', lambda p=project: p.maven.mvnCleanInstall(), {'enabled': project is not None and project.maven.isValid}),
			cls.separator(),
			('Jetty Run',     lambda p=project: p.maven.mvnJettyRun(), {'enabled': project is not None and project.maven.isValid}),
			cls.separator(),
			('Download Sources',     lambda p=project: p.maven.downloadSources(), {'enabled': project is not None and project.maven.isValid}),
		]


	@classmethod
	def gitActions(cls, gui: DatapackEditorGUI, project: Project) -> list[MenuItemData]:
		gitIsValid = project is not None and project.git.isValid
		if gitIsValid:
			git = project.git
		else:
			git  = None
		return [
			('Pull',           lambda g=git: g.pullFromRemote(), {'enabled': gitIsValid, 'tip': 'Pull current branch'}),
			('Fetch',          lambda g=git: g.fetchRemotes(), {'enabled': gitIsValid, 'tip': 'Fetch all remote branches'}),
			('Prune',          lambda g=git: g.pruneRemoteBranches(), {'enabled': gitIsValid, 'tip': 'Prune all remote branches'}),
			('Switch Branch',
				lambda g=git: Maybe(GitGUIMethods.branchSelectionPopup(gui, g.localBranches.values())).apply(g.switchBranch),
				{'enabled': gitIsValid}
			),
			('Checkout Remote',
				lambda g=git: Maybe(GitGUIMethods.branchSelectionPopup(gui, g.remoteBranches.values())).apply(g.switchBranch),
				{'enabled': gitIsValid}
			),
			# ('Switch Branch',
			# 	[
			# 		(branchName, lambda g=git, bn=branchName: g.switchBranch(bn) or g.refresh(), {'enabled': gitIsValid})
			# 		for branchName in git.localBranches.keys()
			# 	] if gitIsValid else [],
			# 	{'enabled': gitIsValid}
			# ),
			# ('Checkout Remote',
			# 	[
			# 		(branchName, lambda g=git, bn=branchName: g.switchBranch(bn) or g.refresh(), {'enabled': gitIsValid})
			# 		for branchName in git.remoteBranches.keys()
			# 	] if gitIsValid else [],
			# 	{'enabled': gitIsValid}
			# ),
			('Create Branch',  lambda gui=gui, g=git: GitGUIMethods.createBranchGUI(gui, g), {'enabled': gitIsValid, 'tip': 'Create a new branch and switch to it.'}),
			('Create Local from Remote',
				lambda g=git: Maybe(GitGUIMethods.branchSelectionPopup(gui, [b for b in git.remoteBranches.values() if b.name.partition('/')[2] not in git.localBranches])).apply(g.createLocalBranchFromRemote),
				{'enabled': gitIsValid}
			),
			# ('Create Local from Remote',
			# 	[
			# 		(branchName, lambda g=git, bn=branchName: g.createLocalBranchFromRemote(bn) or g.refresh(), {'enabled': branchName.partition('/')[2] not in git.localBranches})
			# 		for branchName in git.remoteBranches.keys()
			# 	] if gitIsValid else [],
			# 	{'enabled': gitIsValid}
			# ),
			cls.separator(),
			('Stash',          lambda g=git: g.stashPush(), {'enabled': gitIsValid and bool(git.hasModifiedFiles)}),
			('Pop stash',      lambda g=git: g.stashPop(), {'enabled': gitIsValid and bool(git.stashes)}),
			cls.separator(),
			('Create patch file', lambda gui=gui, g=git: GitGUIMethods.createPatchFileGUI(gui, g), {'enabled': gitIsValid}),
		]


class GitGUIMethods:
	# @classmethod
	# def createPatchFileGUI(cls, gui: PumpDriveSelectorGUI, repository: catGit.Repository):
	# 	if not repository.isValid:
	# 		raise ValueError('repository must be a valid repository (repository.isValid == True)')
	#
	# 	# currentBranch = repository.currentBranch
	# 	# if currentBranch is None:
	# 	# 	gui.showWarningDialog('No branch selected', 'You must select a branch before you can create a patch file.')
	#
	# 	lastNCommits = repository.getLastNCommits(100)
	# 	earliestIndex, ok = gui.askUserInput('Select earliest commit to include', 0, lambda g, i, **kwargs: cls.commitsTable(g, lastNCommits),)
	# 	if not ok:
	# 		return
	# 	commitsCount = earliestIndex + 1
	#
	# 	#savePath = gui.showFileDialog(repository.path, filters=[('Patch file', '.patch')], style='save')
	# 	savePath, ok = earliestIndex, ok = gui.askUserInput('choose filename', 'patch1.patch')
	# 	if not savePath or not ok:
	# 		return
	#
	# 	repository.generatePatchFileForCommits(commitsCount, savePath)
	#
	# @classmethod
	# def createBranchGUI(cls, gui: PumpDriveSelectorGUI, repository: catGit.Repository) -> None:
	# 	if not repository.isValid:
	# 		raise ValueError('repository must be a valid repository (repository.isValid == True)')
	#
	# 	branchName: str = ''
	# 	while True:
	# 		branchName, ok = gui.askUserInput('Branch name ', branchName)
	# 		if not ok:
	# 			return
	# 		branchName = branchName.strip()
	# 		if not cls.isBranchNameValid(branchName):
	# 			gui.showWarningDialog('Invalid branch name', f"'{branchName}' is not a valid branch name in git.")
	# 			continue
	# 		branches = repository.localBranches
	# 		if branchName in branches:
	# 			gui.showWarningDialog('Invalid branch name', f"'{branchName}' already exists.")
	# 			continue
	#
	# 		# branch name is valid!
	# 		repository.createLocalBranch(branchName)
	# 		return
	#
	# @staticmethod
	# def branchSelectionPopup(gui: PumpDriveSelectorGUI, branches: list[catGit.Branch]) -> Optional[catGit.Branch]:
	# 	initialBranch: Optional[catGit.Branch] = None
	# 	branch = gui.searchableChoicePopup(
	# 		initialBranch,
	# 		'New File',
	# 		branches,
	# 		getSearchStr=lambda x: x.name,
	# 		labelMaker=lambda x, i: x.name,
	# 		iconMaker=None,
	# 		toolTipMaker=lambda x, i: x.name,
	# 		columnCount=1,
	# 		width=450,
	# 		height=450,
	# 	)
	# 	return branch
	#
	# @classmethod
	# def isBranchNameValid(cls, branchName: str) -> bool:
	# 	return re.fullmatch(r'^(?!@$|build-|/|.*([/.]\.|//|@\{|\\))[^\000-\037\177 ~^:?*[]+(?<!\.lock)(?<![/.])$', branchName) is not None
	#
	# @classmethod
	# def commitsTable(cls, gui: PumpDriveSelectorGUI, commits: list[catGit.Commit], **kwargs) -> int:
	# 	def labelMaker(c: catGit.Commit, column: int):
	# 		return (
	# 			f'<span style="{getStyles().warning}">{escapeForXml(f"{c.committer}")}</span>',
	# 			f'<span style="{getStyles().warning}">{escapeForXml(f"{c.timeStamp}")}</span>',
	# 			f'{escapeForXml(c.subject)}',
	# 		)[column]
	#
	# 	# def toolTipMaker(c: catGit.Commit, column: int):
	# 	# 	return str(pr[0].path)
	#
	# 	# def onContextMenu(x: catGit.Commit, column: int):
	# 	# 	with gui.popupMenu(atMousePosition=True) as menu:
	# 	# 		menu.addItems(ContextMenuEntries.projectItems(gui, pr[0], self._tryOpenOrSelectDocument))
	#
	# 	selection = gui.tree(
	# 		DataListBuilder(
	# 			commits,
	# 			labelMaker,
	# 			None,
	# 			None,
	# 			3,
	# 			onContextMenu=None,
	# 			getId=catGit.Commit.id.get
	# 		),
	# 		headerBuilder=DataHeaderBuilder(('committer', 'time stamp', 'subject'), lambda x, i: x[i]),
	# 		headerVisible=True,
	# 		itemDelegate=HTMLDelegate(),
	# 		**kwargs
	# 	).selectedItem
	#
	# 	index = -1
	# 	if selection is not None:
	# 		try:
	# 			index = commits.index(selection)
	# 		except ValueError:
	# 			index = -1
	# 	return index
	#
	# 	# gui.propertyListField3(commits, Commit(None))
	# 	return gui.listField(None, [
	# 		#f'{c.subject} ({c.committer} @ {c.timeStamp})' +
	# 		f'{escapeForXml(c.subject)} <span style="{getStyles().warning}">{escapeForXml(f"({c.committer} @ {c.timeStamp})")}</span>'
	# 		for c in commits
	# 	], itemDelegate=HTMLDelegate(), **kwargs)
	# 	# gui.dataTable([(commit.id, commit.subject, commit.committer, commit.committerEmail, commit.timeStamp) for commit in commits], headers=('hash', 'subject', 'committer', 'e-mail', 'time stamp'))
	pass


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
	virtualPath: str = dataclasses.field(compare=False)


@dataclass
class FilesTreeItem:
	label: str
	commonDepth: int = dataclasses.field(compare=False)
	filePaths: list[FileEntry2] = dataclasses.field(compare=False)

	@property
	def isFile(self) -> bool:
		filePathsCount = len(self.filePaths)
		return (filePathsCount == 1 and len(getattr(self.filePaths[0], 'virtualPath', '')) == self.commonDepth - 1)


class Project:
	pass


class DatapackEditorGUI(AutoGUI):

	def showAndLogError(self, e: Exception, title: str = 'Error') -> None:
		logError(format_full_exc(e))
		self.showWarningDialog(title, str(e))

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
						onDoubleClick=lambda g=gui: gui.host.window().accept(),
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
			openFunc: Callable[[FilePath], None],
			includeDependencies: bool = True,
			roundedCorners: RoundedCorners = CORNERS.NONE,
			overlap: Overlap = NO_OVERLAP
	):
		"""
		TODO docString for filteredProjectsFilesTree(...)
		:param allIncludedProjects:
		:param localLayoutFilesProps:
		:param openFunc:
		:param includeDependencies:
		:return:
		"""

		def childrenMaker(data: FilesTreeItem) -> list[FilesTreeItem]:
			filePathsCount = len(data.filePaths)
			if data.isFile or filePathsCount == 0:
				return []

			if isinstance(data.filePaths[0], FilesTreeItem):
				return data.filePaths

			children: OrderedDict[str, FilesTreeItem] = OrderedDict()

			commonDepth = data.commonDepth
			for entry in data.filePaths:
				index2 = entry.virtualPath.find('/', commonDepth)
				index2 = len(entry.virtualPath) if index2 == -1 else index2
				folder = entry.virtualPath[commonDepth:index2]

				child = children.get(folder, None)
				if child is None:
					child = FilesTreeItem(folder, index2 + 1, [])
					children[folder] = child
				child.filePaths.append(entry)
			return list(children.values())

		def labelMaker(data: FilesTreeItem, column: int) -> str:
			return data.label

		def toolTipMaker(data: FilesTreeItem, column: int) -> str:
			if data.isFile:
				return data.filePaths[0].virtualPath[:data.commonDepth]
			else:
				return data.label

		def iconMaker(data: FilesTreeItem, column: int) -> QIcon:
			return icons.file_code if data.isFile else icons.folderInTree

		def onDoubleClick(data: FilesTreeItem):
			if data.isFile:
				openFunc(data.filePaths[0].fullPath)

		def onContextMenu(data: FilesTreeItem, column: int):
			if data.isFile:
				with self.popupMenu(atMousePosition=True) as menu:
					menu.addItems(ContextMenuEntries.fileItems(data.filePaths[0].fullPath, openFunc=openFunc))

		# if includeDependencies:
		# 	allIncludedProjects.extend(sorted(project.deepDependencies, key=attrgetter('name')))

		# if isinstance(firstSplitter, str):
		# 	def getRight(fullPath: FilePath) -> str:
		# 		if not isinstance(fullPath, str):
		# 			splittingPath = fullPath[1]
		# 		else:
		# 			splittingPath = fullPath
		# 		return splittingPath.split(firstSplitter, 1)[-1]
		# else:
		# 	firstSplitterPattern = re.compile(firstSplitter)
		# 	def getRight(fullPath: FilePath) -> str:
		# 		if not isinstance(fullPath, str):
		# 			splittingPath = fullPath[1]
		# 		else:
		# 			splittingPath = fullPath
		# 		return firstSplitterPattern.split(splittingPath, 1)[-1]

		def getRight(fullPath: FilePath, firstSplitter: str) -> str:
			if not isinstance(fullPath, str):
				splittingPath = fullPath[1]
			else:
				splittingPath = fullPath
			return splittingPath.split(firstSplitter, 1)[-1]

		FilesByVirtualFolder = OrderedDict[str, list[tuple[FilePath, str]]]

		# if not isinstance(localLayoutFilesProps, list):
		# 	localLayoutFilesProps = [localLayoutFilesProps]

		# autocomplete strings:
		allAutocompleteStrings: list[str] = []
		allFilePaths: list[FileEntry2] = []
		rootItem: FilesTreeItem = FilesTreeItem('<ROOT>', 0, allFilePaths)
		for proj in allIncludedProjects:
			projPrefix = proj.name + '/'
			projPrefixLen = len(projPrefix)
			#filesForProj: list[FileEntry2] = []
			projItem: FilesTreeItem = FilesTreeItem(proj.name, projPrefixLen, [])
			for filesPropInfo in localLayoutFilesProps:
				fullPathsInProj = filesPropInfo.prop.get(proj)
				firstSplitter = filesPropInfo.firstSplitter
				virtualFolderPrefix = filesPropInfo.folderName + '/' if filesPropInfo.folderName else ''
				virtualFolderPrefix = projPrefix + virtualFolderPrefix
				filesForFolder: list[FileEntry2] = []
				folderItem: FilesTreeItem = FilesTreeItem(filesPropInfo.folderName, len(virtualFolderPrefix), filesForFolder)
				for fullPath in fullPathsInProj:
					right = getRight(fullPath, firstSplitter)
					virtualPath = virtualFolderPrefix + right

					allAutocompleteStrings.append(virtualPath)
					filesForFolder.append(FileEntry2(fullPath, virtualPath))
				if folderItem.filePaths:
					projItem.filePaths.append(folderItem)
			if projItem.filePaths:
				rootItem.filePaths.append(projItem)

			# filesInProj: list[tuple[FilePath, str]] = []
			# for fullPath in allAutoCompletesInProj:
			# 	right = getRight(fullPath)
			# 	allAutocompleteStrings.append(projPrefix + right)
			# 	filesInProj.append((fullPath, right))
			# allFilesByProj.append((proj, filesInProj))

		with self.vLayout(verticalSpacing=0):
			with self.hLayout(horizontalSpacing=0):
				filterStr = self.filterTextField(None, allAutocompleteStrings, overlap=adjustOverlap(overlap, (None, None, 0, 1)), roundedCorners=maskCorners(roundedCorners, CORNERS.TOP_LEFT), shortcut=QKeySequence.Find).lower()

				# totalFilesCount = 0
				# filteredFilesCount = 0
				# result = FileEntry('...', '', 0, [])
				# for proj, filesInProj in allFilesByProj:
				# 	projPrefix = proj.simpleName + '/'
				# 	#filesInProj = localLayoutFilesProp.get(proj)  # proj.layouts.localLayoutFiles
				# 	virtFolderFileEntries: list[FileEntry] = []
				# 	for virtFolder, filesInVirtFolder in filesInProj.items():
				# 		virtFolderPrefix = virtFolder + '/' if virtFolder else ''
				# 		rightList = []
				# 		for fullPathRight in filesInVirtFolder:
				# 			if filterStr and filterStr not in (projPrefix + virtFolderPrefix + fullPathRight[1]).lower():
				# 				continue
				#
				# 			fullPath = fullPathRight[0]
				# 			rightSplitted = tuple(fullPathRight[1].split('/'))
				#
				# 			rightList.append((fullPath, rightSplitted,))
				#
				# 		totalFilesCount += len(filesInVirtFolder)
				# 		filteredFilesCount += len(rightList)
				#
				# 		if rightList:
				# 			projFileEntry = FileEntry(virtFolder, proj.path, 0, rightList)
				# 			# rightEntryDict = resultDict.add(proj, projFileEntry)
				# 			virtFolderFileEntries.append(projFileEntry)
				#
				# 	if virtFolderFileEntries:
				# 		projFileEntry = FileEntry(proj.simpleName, proj.path, 0, virtFolderFileEntries)
				# 		result.right.append(projFileEntry)

				totalFilesCount = len(allAutocompleteStrings)
				filteredFilesCount = 0

				# DBG_vpLenSum = 0
				# DBG_fpLenSum = 0

				if filterStr:
					for projItem in rootItem.filePaths:
						for folderItem in projItem.filePaths:
							folderItem.filePaths = [fp for fp in folderItem.filePaths if filterStr in fp.virtualPath.lower()]

							# DBG_fpLenSum += sum(sys.getsizeof(fp.fullPath) if isinstance(fp.fullPath, str) else (sys.getsizeof(fp.fullPath[0]) + sys.getsizeof(fp.fullPath[1])) for fp in folderItem.filePaths)
							# DBG_vpLenSum += sum(sys.getsizeof(fp.virtualPath) for fp in folderItem.filePaths)

							filteredFilesCount += len(folderItem.filePaths)
						projItem.filePaths = [folderItem for folderItem in projItem.filePaths if folderItem.filePaths]
					rootItem.filePaths = [projItem for projItem in rootItem.filePaths if projItem.filePaths]
					# filteredFilesCount = len(rootItem.filePaths)
				else:
					filteredFilesCount = totalFilesCount

				self.toolButton(
					f'{filteredFilesCount:,} of {totalFilesCount:,}',
					overlap=adjustOverlap(overlap, (1, None, None, 1)),
					roundedCorners = maskCorners(roundedCorners, CORNERS.TOP_RIGHT)
				)  # files shown', alignment=Qt.AlignLeft)

				# self.toolButton(
				# 	f'{DBG_fpLenSum // filteredFilesCount:,} avg full path length',
				# 	overlap=adjustOverlap(overlap, (1, None, None, 1)),
				# 	roundedCorners = maskCorners(roundedCorners, CORNERS.TOP_RIGHT)
				# )  # files shown', alignment=Qt.AlignLeft)
				#
				# self.toolButton(
				# 	f'{DBG_vpLenSum // filteredFilesCount:,} avg virt. path length',
				# 	overlap=adjustOverlap(overlap, (1, None, None, 1)),
				# 	roundedCorners = maskCorners(roundedCorners, CORNERS.TOP_RIGHT)
				# )  # files shown', alignment=Qt.AlignLeft)

			self.tree(
				DataTreeBuilder(
					rootItem,
					childrenMaker,
					labelMaker,
					iconMaker,
					toolTipMaker,
					1,
					suppressUpdate=False,
					showRoot=False,
					onDoubleClick=onDoubleClick,
					getId=lambda x: x.label,
					onContextMenu=onContextMenu
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
					gui.customData['prevPressed'] = gui.toolButton(icon=icons.prev, tip='previous', overlap=(0, 0, 1, 1), roundedCorners=(False, False, False, False), shortcut=QKeySequence.FindPrevious)
					gui.customData['nextPressed'] = gui.toolButton(icon=icons.next, tip='next', overlap=(1, 0, 1, 1), shortcut=QKeySequence.FindNext)
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
		searchGUI.customData['text'] = text
		searchGUI.redrawGUI()
		return \
			searchGUI.customData['searchExpr'], \
			searchGUI.customData['searchResults'], \
			searchGUI.customData['prevPressed'], \
			searchGUI.customData['nextPressed'], \
			searchGUI.customData['searchOptions']


	def errorsSummaryGUI(self: DatapackEditorGUI, errorCounts: documents.ErrorCounts, **kwargs):
		errorsTip = 'errors'
		warningsTip = 'warnings'
		hintsTip = 'hints'

		#self.hSeparator()  # parser & config errors:
		self.label(icons.errorColored, tip=errorsTip, **kwargs)
		self.label(f'{errorCounts.parserErrors + errorCounts.configErrors}', tip=errorsTip, **kwargs)
		#self.hSeparator()  # config warnings:
		self.label(icons.warningColored, tip=warningsTip, **kwargs)
		self.label(f'{errorCounts.configWarnings}', tip=warningsTip, **kwargs)
		#self.hSeparator()  # config hints:
		self.label(icons.infoColored, tip=hintsTip, **kwargs)
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
			self.helpBox(f'All is OK!', style='info')

	def editor(self, editor: Type[EditorBase[TT]], model: TT, **kwargs) -> None:
		editor = self.customWidget(editor, initArgs=(model,), model=model, **kwargs)
		editor.redraw()


TPythonGUI = TypeVar('TPythonGUI', bound=DatapackEditorGUI)


class EditorBase(PythonGUIWidget, CatFramedWidgetMixin, Generic[TT]):

	def __init__(
			self,
			model: TT,
			GuiCls: Type[TPythonGUI] = DatapackEditorGUI,
			parent: Optional[QWidget] = None,
			flags: Union[Qt.WindowFlags, Qt.WindowType] = Qt.WindowFlags()
	):
		super(EditorBase, self).__init__(self.OnGUI, GuiCls, parent, flags)
		self._model: TT = model
		self.layout().setContentsMargins(0, 0, 0, 0)

	@abstractmethod
	def OnGUI(self, gui: TPythonGUI) -> None:
		raise NotImplementedError()

	def model(self) -> TT:
		return self._model

	def setModel(self, model: TT):
		if model is not self._model:
			self._model = model
			self.redraw()


def drawCodeField(
		gui: DatapackEditorGUI,
		code: str,
		language: str,
		errorRanges: list[tuple[int, int, int, int, str]],
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
			language=language,
			braceMatching=braceMatching.value,
			searchResults=searchResults,
			prev=prevPressed,
			next=nextPressed,
			searchOptions=searchOptions,
			returnCursorPos=True,
			#onCursorPositionChanged=lambda a, b, g=gui: g.customData.__setitem__('currentCursorPos', (a, b)) ,
			errorRanges=errorRanges,
			**codeFieldKwargs,
			**kwargs
		)

	return code, highlightErrors, cursorPos, forceLocate





__documentDrawers: dict[Type[Document], DocumentGUIFunc] = {}
DocumentDrawer = AddToDictDecorator(__documentDrawers)
getDocumentDrawer = ft.partial(getIfKeyIssubclassOrEqual, __documentDrawers)


def drawTextDocument(gui: DatapackEditorGUI, document: documents.TextDocument, language: Optional[str], **kwargs) -> documents.TextDocument:
	if document is None:
		return document
	if document.highlightErrors:
		errorRanges = [(error.position.line, error.position.column, error.end.line, error.end.column, error.style) for error in document.errors if error.position is not None and error.end is not None]
	else:
		errorRanges = []
	with gui.vLayout(contentsMargins=NO_MARGINS, verticalSpacing=0):
		document.content, document.highlightErrors, document.cursorPosition, document.forceLocate = drawCodeField(
			gui,
			document.content,
			language=document.language,
			errorRanges=errorRanges,
			forceLocateElement=True,
			currentCursorPos=document.cursorPosition,
			selectionTo=document.selection[2:] if document.selection[0] != -1 else None,
			highlightErrors=document.highlightErrors,
			onCursorPositionChanged=lambda a, b, d=document: type(d).cursorPosition.set(d, (a, b)),
			onSelectionChanged2=lambda a1, b1, a2, b2, d=document: type(d).selection.set(d, (a1, b1, a2, b2)),
			#autoCompletionTree=getSession().project.models.allTypesAutoCompletionTree
			**kwargs
		)

	document.onErrorsChanged.connect('mainGUIRedraw', lambda d, g=gui: g.redrawGUI())
	return document


def drawSimpleCodeDocument(gui: DatapackEditorGUI, v: Document, language: str, **kwargs) -> Document:
	content = v.content
	with gui.vLayout(verticalSpacing=0):
		searchOptions = gui.searchBar(content, searchExpr=None)[1:]
		content = gui.advancedCodeField(content, None, language, True, *searchOptions, **kwargs)
	v.content = content
	return v


DocumentDrawer(documents.TextDocument)(      ft.partial(drawTextDocument, language=None))
DocumentDrawer(documents.JsonDocument)(      ft.partial(drawTextDocument, language='Json'))
DocumentDrawer(documents.MCFunctionDocument)(ft.partial(drawTextDocument, language='MCFunction'))



