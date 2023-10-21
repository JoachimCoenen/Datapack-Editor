from __future__ import annotations

import codecs
import copy
import functools as ft
import os
import re
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Optional, Iterable, overload, TypeVar, Callable, Any, Iterator, Collection, Mapping, Generic, \
	Sequence, Type

from PyQt5.QtCore import Qt, QItemSelectionModel, QModelIndex
from PyQt5.QtGui import QKeyEvent, QKeySequence, QIcon
from PyQt5.QtWidgets import QApplication, QSizePolicy, QTreeView

from Cat.GUI import Style, RoundedCorners, Overlap, CORNERS, TreeBuilderABC
from Cat.GUI.autoGUI import AutoGUI
from Cat.GUI.components.Widgets import CatTextField, HTMLDelegate
from Cat.GUI.components.codeEditor import SearchOptions, SearchMode, QsciBraceMatch, IndexSpan
from Cat.GUI.components.treeBuilders import DataListBuilder
from Cat.GUI.decoratorDrawers import registerDecoratorDrawer, InnerDrawPropertyFunc
from Cat.GUI.enums import ResizeMode, SizePolicy
from Cat.GUI.pythonGUI import MenuItemData
from Cat.Serializable.serializableDataclasses import SerializableDataclass
from Cat.Serializable.utils import PropertyDecorator, get_args
from gui.icons import icons
from Cat.utils import findall, FILE_BROWSER_DISPLAY_NAME, showInFileSystem, CachedProperty
from base.model.applicationSettings import getApplicationSettings
from base.model.documents import ErrorCounts
from base.model.pathUtils import FilePath, unitePath
from base.model.utils import GeneralError

inputBoxStyle = Style({'CatBox': Style({'background': '#FFF2CC'})})
resultBoxStyle = Style({'CatBox': Style({'background': '#DAE8FC'})})


_TT = TypeVar('_TT')
_TR = TypeVar('_TR')
_T2 = TypeVar('_T2')


class ContextMenuEntries:
	@classmethod
	def separator(cls):
		return '', None

	@classmethod
	def pathItems(cls, filePath: FilePath) -> list[MenuItemData]:
		if not type(filePath) in {str, tuple, type(None)}:
			raise AssertionError(f"Expected str, tuple or None, but got {type(filePath)}")

		if filePath is not None:
			filePathJoined = unitePath(filePath)
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


def makeTextSearcher(expr: str, searchOptions: SearchOptions) -> Callable[[str], Iterator[IndexSpan]]:
	if searchOptions.searchMode == SearchMode.RegEx:
		flags = 0
		flags |= re.IGNORECASE if not searchOptions.isCaseSensitive else 0
		flags |= re.MULTILINE if not searchOptions.isMultiLine else 0
		exprC = re.compile(expr, flags=flags)

		def searcher(text: str) -> Iterator[IndexSpan]:
			yield from (IndexSpan(m.start(), m.end()) for m in exprC.finditer(text))
	else:
		if searchOptions.searchMode == SearchMode.UnicodeEscaped:
			expr = codecs.getdecoder("unicode_escape")(expr)[0]
		if not searchOptions.isCaseSensitive:
			expr = expr.lower()
		exprLen = len(expr)

		def searcher(text: str) -> Iterator[IndexSpan]:
			text = text if searchOptions.isCaseSensitive else text.lower()
			yield from (IndexSpan(m, m + exprLen) for m in findall(expr, text))

	return searcher


@overload
def autocompleteFromList(text: str, allChoices: Iterable[str]) -> str:
	pass


@overload
def autocompleteFromList(text: str, allChoices: Iterable[_TT], getStr: Callable[[_TT], str]) -> str:
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


def filterStrChoices(filterStr: FilterStr, allChoices: Collection[str]) -> tuple[int, int, Collection[str]]:
	if not filterStr:
		result = allChoices
	else:
		result = [choice[1] for choice in ((choice.lower(), choice) for choice in allChoices) if any(f in choice[0] for f in filterStr)]
	return len(allChoices), len(result), result
	# [choice for choice in allChoices if filterStr in choice.lower()]


def filterDictChoices(filterStr: FilterStr, allChoices: Mapping[str, _TT]) -> tuple[int, int, list[_TT]]:
	if not filterStr:
		result = list(allChoices.values())
	else:
		result = [choice[1] for choice in ((  name.lower(),   item) for name, item in allChoices.items()) if any(f in choice[0] for f in filterStr)]
	return len(allChoices), len(result), result


def filterComputedChoices(getStr: Callable[[_TT], str]):
	def innerFilterComputedChoices(filterStr: FilterStr, allChoices: Collection[_TT], getStr=getStr) -> tuple[int, int, Collection[_TT]]:
		if not filterStr:
			result = allChoices
		else:
			result = [choice[1] for choice in ((getStr(choice).lower(), choice) for choice in allChoices) if any(f in choice[0] for f in filterStr)]
		return len(allChoices), len(result), result
	return innerFilterComputedChoices


@dataclass
class SearchableListContext(Generic[_TR]):
	selectedValue: Optional[_TR] = None
	filterStr: FilterStr = field(default_factory=lambda: FilterStr(''))
	filteredChoices: list[_TR] = field(default_factory=list)
	focusEndOfText: bool = False
	treeView: Optional[QTreeView] = None


class DatapackEditorGUI(AutoGUI):

	def searchableChoicePopup(
			self,
			value: _TT,
			label: str,
			allChoices: Iterable[_TT],
			getSearchStr: Optional[Callable[[_TT], str]],
			labelMaker: Callable[[_TT, int], str],
			iconMaker: Optional[Callable[[_TT, int], Optional[QIcon]]],
			toolTipMaker: Optional[Callable[[_TT, int], Optional[str]]],
			columnCount: int,
			onContextMenu: Optional[Callable[[_TT, int], None]] = None,
			reevaluateAllChoices: bool = False,
			*,
			width: int = None,
			height: int = None,
	):
		allChoicesDict: OrderedDict[str, _TT] = OrderedDict()

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
			#value: _TT
			filterVal: str
			filteredChoices: dict[str, _TT]
			selectedValue: Optional[_TT] = None
			focusEndOfText: bool = False

			selectionModel: Optional[QItemSelectionModel] = None

		def guiFunc(gui: DatapackEditorGUI, context: Context):
			def onKeyPressed(widget, event: QKeyEvent):
				key = event.key()
				if key == Qt.Key_Down:
					context.index += 1
					self.selectRow(context.selectionModel, context.index)
					result = True
				elif key == Qt.Key_Up:
					context.index -= 1
					if context.index < 0:
						context.index = len(context.filteredChoices)-1
					self.selectRow(context.selectionModel, context.index)
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
					context.filteredChoices = dict(choice for choice in allChoicesDict.items() if caseFoldedFilterVal in choice[0])

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
					self.selectRow(context.selectionModel, context.index)

			return context

		context = Context(-2, '', {}, value)
		newValue, isOk = self.popupWindow(
			context,
			guiFunc=guiFunc,
			width=width,
			height=height,
		)
		return newValue.selectedValue if isOk else value

	def filterTextField(self, value: Optional[str], allChoices: Iterable[str], showPlaceholderText: bool = True, **kwargs) -> str:
		def onKeyPressed(widget: CatTextField, event: QKeyEvent):
			if event.key() == Qt.Key_Tab:
				widget.setText(autocompleteFromList(widget.text(), allChoices))
				return True
			else:
				return False
		if showPlaceholderText:
			kwargs.setdefault('placeholderText', 'filter... [Ctrl+F]')
		value = self.textField(value, capturingTab=True, onKeyPressed=onKeyPressed, **kwargs)

		return value

	def advancedFilterTextField(
			self,
			filterStr: Optional[FilterStr],
			allChoices: _TT,
			*,
			getStrChoices: Callable[[-_TT], Iterable[str]] = lambda x: x,
			filterFunc: Callable[[FilterStr, -_TT], tuple[int, int, _TR]] = filterStrChoices,
			shortcut: Optional[QKeySequence] = QKeySequence.Find,
			roundedCorners: RoundedCorners = (True, True, False, False),
			overlap: Overlap = (0, -1),
			**kwargs
	) -> tuple[FilterStr, _TR]:
		# TODO: find more descriptive name for advancedFilterTextField(...)

		def strChoicesIter(allChoices=allChoices):
			yield from getStrChoices(allChoices)

		if shortcut is not None:
			kwargs['shortcut'] = shortcut
		with self.hLayout(seamless=True):  # horizontalSpacing=0):
			filterStr = FilterStr(self.filterTextField(
				filterStr.string if filterStr is not None else None,
				strChoicesIter(),
				**kwargs
			))
			allCount, filteredCount, filteredChoices = filterFunc(filterStr, allChoices)
			self.toolButton(f'{filteredCount:,} of {allCount:,}')
		return filterStr, filteredChoices

	def advancedFilterTextField2(
			self,
			allChoices: Sequence[_TT],
			context: Optional[SearchableListContext[_TR]],
			*,
			getStrChoices: Callable[[Iterable[_TT]], Iterable[str]] = lambda x: x,  # : Callable[[-_TT], Iterable[str]]
			filterFunc: Callable[[FilterStr, Iterable[_TT]], tuple[int, int, Collection[_TR]]] = filterStrChoices,  # : Callable[[FilterStr, -_TT], _TR]
			isRegex: bool = False,
	) -> SearchableListContext[_TR]:
		# TODO: find more descriptive name for advancedFilterTextField2(...)

		def onKeyPressed(widget, event: QKeyEvent):
			key = event.key()
			if key in {Qt.Key_Down, Qt.Key_Up, Qt.Key_Left, Qt.Key_Right, Qt.Key_Return}:
				if context.treeView is not None:
					context.treeView.keyPressEvent(QKeyEvent(event))
					event.accept()
				return True
			elif key == Qt.Key_Tab:
				# do Tab Completion:
				oldFilterVal = context.filterStr
				context.filterStr = FilterStr(autocompleteFromList(oldFilterVal.string, getStrChoices(allChoices)))  # , isRegex=isRegex)
				context.focusEndOfText = True
				self.OnInputModified(context.treeView)
				return True
			else:
				return False

		if context is None:
			context = SearchableListContext()

		# with self.vLayout(seamless=True):
		with self.hLayout(seamless=True):
			context.filterStr = FilterStr(self.textField(
				context.filterStr.string,
				capturingTab=True,
				onKeyPressed=onKeyPressed,
				focusEndOfText=context.focusEndOfText,
				placeholderText='filter... [Ctrl+F]',
				shortcut=QKeySequence.Find
			))  # , isRegex=isRegex)
			context.focusEndOfText = False
			allCount, filteredCount, context.filteredChoices = filterFunc(context.filterStr, allChoices)
			self.toolButton(f'{filteredCount} of {allCount}')
			# if context.filterStr.regexError is not None:
			# 	self.helpBox(str(context.filterStr.regexError), style='error', elided=True)
		return context

	def filteredTree(
			self,
			context: SearchableListContext[_TT],
			treeBuilder: TreeBuilderABC[_TT],
			headerBuilder: Optional[TreeBuilderABC[_T2]] = None,
			*,
			headerVisible: bool | Ellipsis = ...,
			loadDeferred: bool = True,
			columnResizeModes: Optional[Iterable[ResizeMode]] = None,
			stretchLastColumn: bool | Ellipsis = ...,
			**kwargs
	) -> SearchableListContext[_TT]:
		treeResult = self.tree(
			treeBuilder,
			headerBuilder,
			headerVisible=headerVisible,
			loadDeferred=loadDeferred,
			columnResizeModes=columnResizeModes,
			stretchLastColumn=stretchLastColumn,
			**kwargs
		)
		context.treeView = treeResult.treeView
		selectionModel = treeResult.selectionModel

		# if self.isFirstRedraw and selectionModel is not self.modifiedInput[0]:
		# 	currentIndex = treeResult.treeView.currentIndex()
		# 	if currentIndex.isValid():
		# 		treeResult.treeView.scrollTo(currentIndex)  has bad performance characteristics :'(

		if len(context.filteredChoices) == 1:
			self.selectRow(selectionModel, 0)
		context.selectedValue = treeResult.selectedItem
		return context

	def selectRow(self, selectionModel: QItemSelectionModel, row: int):
		model_index = selectionModel.model().index(row, 0, QModelIndex())
		selectionModel.setCurrentIndex(model_index, QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)

	def filteredTreeWithSearchField(
			self,
			allChoices: Sequence[_TT],
			filterContext: Optional[SearchableListContext[_TR]],
			treeBuilderBuilder: Callable[[list[_TR]], TreeBuilderABC[_TR]],
			*,
			headerBuilderBuilder: Callable[[], Optional[TreeBuilderABC[_T2]]] = None,
			getStrChoices: Callable[[Iterable[_TT]], Iterable[str]] = lambda x: x,  # : Callable[[-_TT], Iterable[str]]
			filterFunc: Callable[[FilterStr, Iterable[_TT]], tuple[int, int, Collection[_TR]]] = filterStrChoices,  # : Callable[[FilterStr, -_TT], _TR]
			isRegex: bool = False,
			headerVisible: bool | Ellipsis = ...,
			loadDeferred: bool = True,
			columnResizeModes: Optional[Iterable[ResizeMode]] = None,
			stretchLastColumn: bool | Ellipsis = ...,
			cornerGUI: Callable[[], None] = None,
			sandwichedGUI: Callable[[], None] = None,
			**kwargs
	) -> tuple[Optional[_TR], SearchableListContext[_TR]]:
		with self.vLayout(seamless=True):
			with self.hLayout(seamless=True):
				filterContext = self.advancedFilterTextField2(
					allChoices,
					filterContext,
					getStrChoices=getStrChoices,
					filterFunc=filterFunc,
					isRegex=isRegex,
				)

				if cornerGUI is not None:
					cornerGUI()

			if sandwichedGUI is not None:
				sandwichedGUI()

			treeBuilder = treeBuilderBuilder(filterContext.filteredChoices)
			headerBuilder = headerBuilderBuilder() if headerBuilderBuilder is not None else None
			filterContext = self.filteredTree(
				filterContext,
				treeBuilder,
				headerBuilder,
				headerVisible=headerVisible,
				loadDeferred=loadDeferred,
				columnResizeModes=columnResizeModes,
				stretchLastColumn=stretchLastColumn,
				**kwargs
			)

		return filterContext.selectedValue, filterContext

	def searchBar(self, text: Optional[str], searchExpr: Optional[str]) -> tuple[str, list[IndexSpan], bool, bool, SearchOptions]:
		def onGUI(gui: DatapackEditorGUI, text: Optional[str], searchExpr: Optional[str], outerGUI: DatapackEditorGUI) -> None:
			with gui.vLayout(seamless=True):
				with gui.hLayout(seamless=True):
					with gui.hPanel(seamless=True):
						gui.customData['prevPressed'] = gui.framelessButton(icon=icons.prev, tip='previous', margins=gui.smallDefaultMargins, parentShortcut=QKeySequence.FindPrevious)
						gui.customData['nextPressed'] = gui.framelessButton(icon=icons.next, tip='next', margins=gui.smallDefaultMargins, parentShortcut=QKeySequence.FindNext)
					gui.customData['searchExpr'] = searchExpr if searchExpr is not None else gui.customData.get('searchExpr', '')
					gui.customData['searchExpr'] = gui.textField(gui.customData['searchExpr'], placeholderText='find... [Ctrl+F]', isMultiline=False, overlap=(1, 0, 1, 1), parentShortcut=QKeySequence.Find)

					with gui.hPanel(seamless=True):
						searchMode = SearchMode.RegEx if gui.framelessButton('.*', tip='RegEx', margins=gui.smallDefaultMargins, checkable=True) else SearchMode.Normal
						isCaseSensitive = gui.framelessButton('Aa', tip='case sensitive', margins=gui.smallDefaultMargins, checkable=True)
						isMultiLine = False  # gui.toggleLeft(None, 'Multiline', enabled=isRegex)
						gui.customData['searchOptions'] = SearchOptions(searchMode, isCaseSensitive, isMultiLine)

					# do actual search:
					try:
						searcher: Callable[[str], Iterator[IndexSpan]] = makeTextSearcher(gui.customData['searchExpr'].encode('utf-8'), gui.customData['searchOptions'])
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
			suppressRedrawLogging=True,
			seamless=True
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

	@staticmethod
	def getErrorIcon(style: str) -> Optional[QIcon]:
		match style:
			case 'error': return icons.errorColored
			case 'warning': return icons.warningColored
			case 'info': return icons.infoColored
			case _: return None

	def errorsSummaryGUI(self: DatapackEditorGUI, errorCounts: ErrorCounts, **kwargs):
		errorsTip = 'errors'
		warningsTip = 'warnings'
		hintsTip = 'hints'

		self.label(self.getErrorIcon('error'), tip=errorsTip, **kwargs)
		self.label(f'{errorCounts.errors}', tip=errorsTip, **kwargs)
		self.label(self.getErrorIcon('warning'), tip=warningsTip, **kwargs)
		self.label(f'{errorCounts.warnings}', tip=warningsTip, **kwargs)
		self.label(self.getErrorIcon('info'), tip=hintsTip, **kwargs)
		self.label(f'{errorCounts.hints}', tip=hintsTip, **kwargs)

	def errorsSummarySimpleGUI(self: DatapackEditorGUI, errorCounts: ErrorCounts, **kwargs):
		self.hSeparator()
		self.label(f'errors: {errorCounts.errors:3} | warnings: {errorCounts.warnings:3} | hints: {errorCounts.hints:3}')
		self.hSeparator()

	def drawError(self, error: GeneralError, **kwargs):
		if error.position is not None:
			positionMsg = f'at line {error.position.line + 1}, pos {error.position.column}'
		else:
			positionMsg = ''
		errorMsg = error.htmlMessage
		style = getattr(error, 'style', 'error')
		with self.hLayout():
			self.helpBox(errorMsg, style=style, hasLabel=False, hSizePolicy=QSizePolicy.Expanding, **kwargs)
			self.helpBox(positionMsg, style=style, hasLabel=False, **kwargs)
		# msg = f'{errorMsg} {positionMsg}'
		# self.helpBox(msg, style=style, **kwargs)

	def drawErrors(self: DatapackEditorGUI, errors: Collection[GeneralError], onDoubleClicked: Callable[[GeneralError], None]):
		if errors:
			for error in errors:
				self.drawError(error, onDoubleClicked=lambda ev, error=error, gui=self: onDoubleClicked(error) or gui.redrawGUI())
				self.vSeparator()
		else:
			self.helpBox(f"Everything's fine!", style='info')

	@CachedProperty
	def _htmlDelegate(self) -> HTMLDelegate:
		return HTMLDelegate()

	def errorsList(self: DatapackEditorGUI, errors: Collection[GeneralError], onDoubleClicked: Callable[[GeneralError], None], **kwargs):

		def getLabel(error: GeneralError, i: int) -> str:
			if error.position is not None:
				positionMsg = f'at line {error.position.line + 1}, pos {error.position.column}'
			else:
				positionMsg = ''
			errorMsg = error.htmlMessage.replace('\n', '')
			return (errorMsg, positionMsg)[i]

		def getIcon(error: GeneralError, i: int) -> Optional[QIcon]:
			if i == 0:
				return self.getErrorIcon(error.style)
			else:
				return None

		self.tree(
			DataListBuilder(
				errors,
				labelMaker=getLabel,
				iconMaker=getIcon,
				toolTipMaker=lambda e, i: getLabel(e, 0),
				columnCount=2,
				onDoubleClick=onDoubleClicked,  # lambda e: onDoubleClicked(e) or self.redrawGUI(),
				onCopy=lambda e: e.message,
				getId=lambda e: e.message,
			),
			headerVisible=False,
			stretchLastColumn=False,
			columnResizeModes=(ResizeMode.Stretch, ResizeMode.ResizeToContents),
			itemDelegate=self._htmlDelegate,
			**kwargs
		)


TPythonGUI = TypeVar('TPythonGUI', bound=DatapackEditorGUI)


def drawCodeField(
		gui: DatapackEditorGUI,
		code: str,
		errors: list[GeneralError],
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

	font = getApplicationSettings().appearance.monospaceFont

	with gui.vLayout(seamless=True):
		# actual GUI:
		with gui.hLayout(seamless=True):
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
			errors=errors if highlightErrors else [],
			font=font,
			**codeFieldKwargs,
			**kwargs
		)

	return code, highlightErrors, cursorPos, forceLocate


class EditableSerializableDataclassList(PropertyDecorator):
	"""docstring for List"""
	def __init__(
			self,
			name: str,
			treeBuilderBuilder: Callable[[list[_TR]], TreeBuilderABC[_TR]],
			*,
			headerBuilderBuilder: Callable[[], Optional[TreeBuilderABC[_T2]]] = None,
			getStrChoices: Callable[[Iterable[_TT]], Iterable[str]] = lambda x: x,  # : Callable[[-_TT], Iterable[str]]
			filterFunc: Callable[[FilterStr, Iterable[_TT]], tuple[int, int, Collection[_TR]]] = filterStrChoices,  # : Callable[[FilterStr, -_TT], _TR]
			dialogWidth: Optional[int] = None, dialogHeight: Optional[int] = None,
	):
		super().__init__()
		self.name: str = name
		self.treeBuilderBuilder: Callable[[list[_TR]], TreeBuilderABC[_TR]] = treeBuilderBuilder
		self.headerBuilderBuilder: Callable[[], Optional[TreeBuilderABC[_T2]]] = headerBuilderBuilder
		self.getStrChoices: Callable[[Iterable[_TT]], Iterable[str]] = getStrChoices
		self.filterFunc: Callable[[FilterStr, Iterable[_TT]], tuple[int, int, Collection[_TR]]] = filterFunc
		self.dialogWidth: Optional[int] = dialogWidth
		self.dialogHeight: Optional[int] = dialogHeight


@registerDecoratorDrawer(EditableSerializableDataclassList)
def drawList(gui_: DatapackEditorGUI, values_: list[_TT], type_: Optional[Type[list[_TT]]], decorator_: EditableSerializableDataclassList, drawProperty_: InnerDrawPropertyFunc[list[_TT]], owner_: SerializableDataclass, **kwargs) -> _TT:
	innerType_ = get_args(type_)[0]

	def _addRoot(gui: DatapackEditorGUI):
		newVal, isOk = gui.askUserInput(
			f"Add",
			innerType_(),
			width=int(decorator_.dialogWidth * gui.scale) if decorator_.dialogWidth is not None else None,
			height=int(decorator_.dialogHeight * gui.scale) if decorator_.dialogHeight is not None else None,
		)
		if isOk:
			values_.append(newVal)

	def _editRoot(gui: DatapackEditorGUI, value: _TT):
		newVal, isOk = gui.askUserInput(
			f"Edit",
			copy.deepcopy(value),
			width=int(decorator_.dialogWidth * gui.scale) if decorator_.dialogWidth is not None else None,
			height=int(decorator_.dialogHeight * gui.scale) if decorator_.dialogHeight is not None else None,
		)
		if isOk:
			value.copyFrom(newVal)

	def _removeRoot(gui: DatapackEditorGUI, value: _TT):
		# todo ask user
		values_.remove(value)

	def _moveRootUp(value: _TT):
		idx = values_.index(value)
		if idx > 0:
			values_[idx - 1], values_[idx] = values_[idx], values_[idx - 1]

	def _moveRootDown(value: _TT):
		idx = values_.index(value)
		if idx < len(values_) - 1:
			values_[idx], values_[idx + 1] = values_[idx + 1], values_[idx]

	contextId = f'{decorator_.name}_listContext'
	listContext = gui_.customData.get(contextId)
	if listContext is None:
		listContext = SearchableListContext()

	with gui_.vLayout(seamless=True):
		selected, listContext = gui_.filteredTreeWithSearchField(
			values_,
			listContext,
			decorator_.treeBuilderBuilder,
			headerBuilderBuilder=decorator_.headerBuilderBuilder,
			getStrChoices=decorator_.getStrChoices,
			filterFunc=decorator_.filterFunc,
		)
		gui_.customData[contextId] = listContext

		with gui_.hPanel(seamless=True):
			canMoveDown = selected is not None and values_ and values_[-1] is not selected
			canMoveUp = selected is not None and values_ and values_[0] is not selected
			gui_.addHSpacer(0, SizePolicy.Expanding)
			if gui_.toolButton(icon=icons.edit, tip='Edit', enabled=selected is not None):
				_editRoot(gui_, selected)
			if gui_.toolButton(icon=icons.up, tip='Move up', enabled=canMoveUp):
				_moveRootUp(selected)
			if gui_.toolButton(icon=icons.down, tip='Move down', enabled=canMoveDown):
				_moveRootDown(selected)
			if gui_.toolButton(icon=icons.remove, tip='Remove selected', enabled=selected is not None):
				_removeRoot(gui_, selected)
			if gui_.toolButton(icon=icons.add, tip='Add', enabled=True):
				_addRoot(gui_)
	return values_