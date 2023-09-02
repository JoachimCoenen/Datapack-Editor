from __future__ import annotations

import codecs
import functools as ft
import os
import re
from collections import OrderedDict
from dataclasses import dataclass
from typing import Optional, Iterable, overload, TypeVar, Callable, Any, Iterator, Collection, Mapping

from PyQt5.QtCore import Qt, QItemSelectionModel, QModelIndex
from PyQt5.QtGui import QKeyEvent, QKeySequence, QIcon
from PyQt5.QtWidgets import QApplication, QSizePolicy

from Cat.CatPythonGUI.AutoGUI.autoGUI import AutoGUI
from Cat.CatPythonGUI.GUI import Style, RoundedCorners, Overlap, adjustOverlap, maskCorners, CORNERS
from Cat.CatPythonGUI.GUI.Widgets import CatTextField, HTMLDelegate
from Cat.CatPythonGUI.GUI.codeEditor import SearchOptions, SearchMode, QsciBraceMatch
from Cat.CatPythonGUI.GUI.enums import ResizeMode
from Cat.CatPythonGUI.GUI.pythonGUI import MenuItemData
from Cat.CatPythonGUI.GUI.treeBuilders import DataListBuilder
from Cat.icons import icons
from Cat.utils import findall, FILE_BROWSER_DISPLAY_NAME, showInFileSystem, CachedProperty
from base.model.applicationSettings import getApplicationSettings
from base.model.documents import ErrorCounts
from base.model.pathUtils import FilePath, unitePath
from base.model.utils import GeneralError

inputBoxStyle = Style({'CatBox': Style({'background': '#FFF2CC'})})
resultBoxStyle = Style({'CatBox': Style({'background': '#DAE8FC'})})


_TT = TypeVar('_TT')
_TR = TypeVar('_TR')


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


def filterStrChoices(filterStr: FilterStr, allChoices: Collection[str]) -> Collection[str]:
	if not filterStr:
		return allChoices
	return [choice[1] for choice in ((choice.lower(), choice) for choice in allChoices) if any(f in choice[0] for f in filterStr)]
	# [choice for choice in allChoices if filterStr in choice.lower()]


def filterDictChoices(filterStr: FilterStr, allChoices: Mapping[str, _TT]) -> list[_TT]:
	if not filterStr:
		return list(allChoices.values())
	return [choice[1] for choice in ((  name.lower(),   item) for name, item in allChoices.items()) if any(f in choice[0] for f in filterStr)]


def filterComputedChoices(getStr: Callable[[_TT], str]):
	def innerFilterComputedChoices(filterStr: FilterStr, allChoices: Collection[_TT], getStr=getStr) -> Collection[_TT]:
		if not filterStr:
			return allChoices
		return [choice[1] for choice in ((getStr(choice).lower(), choice) for choice in allChoices) if any(f in choice[0] for f in filterStr)]
	return innerFilterComputedChoices


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
					context.selectionModel.setCurrentIndex(context.selectionModel.model().index(context.index, 0, QModelIndex()), QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)

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
			filterFunc: Callable[[FilterStr, -_TT], _TR] = filterStrChoices,
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

	def searchBar(self, text: Optional[str], searchExpr: Optional[str]) -> tuple[str, list[tuple[int, int]], bool, bool, SearchOptions]:
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

		self.label(errorIcons['error'], tip=errorsTip, **kwargs)
		self.label(f'{errorCounts.errors}', tip=errorsTip, **kwargs)
		self.label(errorIcons['warning'], tip=warningsTip, **kwargs)
		self.label(f'{errorCounts.warnings}', tip=warningsTip, **kwargs)
		self.label(errorIcons['info'], tip=hintsTip, **kwargs)
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

		errorIcons = self._errorIcons

		def getIcon(error: GeneralError, i: int) -> Optional[QIcon]:
			if i == 0:
				return errorIcons.get(error.style)
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
			errors=errors,
			font=font,
			**codeFieldKwargs,
			**kwargs
		)

	return code, highlightErrors, cursorPos, forceLocate
