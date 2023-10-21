import os
from abc import abstractmethod, ABC
from dataclasses import dataclass, field
from typing import Optional, Any, TypeVar, Generic

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QDialog

import Cat.GUI.propertyDecorators as pd
from Cat.GUI.pythonGUI import PythonGUIDialog
from Cat.GUI.components.catTabBar import TabOptions
from Cat.GUI.enums import *
from Cat.GUI.components.treeBuilders import DataListBuilder
from Cat.Serializable.serializableDataclasses import catMeta, SerializableDataclass
from Cat.utils.utils import sanitizeFileName
from base.model.pathUtils import FilePathStr, joinFilePath, unitePathTpl
from base.model.project.projectCreator import ProjectCreator
from base.model.session import getSession
from base.plugin import PLUGIN_SERVICE
from gui.datapackEditorGUI import DatapackEditorGUI


_T = TypeVar('_T', bound=SerializableDataclass)


# todo: add settings for DEFAULT_PROJECTS_LOCATION:
DEFAULT_PROJECTS_LOCATION = os.path.expanduser('~/cce/projects').replace('\\', '/')


def projPathValidator(path: str) -> Optional[pd.ValidatorResult]:
	result = pd.folderPathValidator(path)

	if not result and not unitePathTpl(getSession().getProjectConfigPath(path)):
		result = pd.ValidatorResult("Selected directory is missing a project configuration.", 'error')
	return result


def newProjDirectoryPathValidator(path: str) -> Optional[pd.ValidatorResult]:
	if os.path.lexists(path):
		return pd.ValidatorResult("Project directory already exists.", 'warning')
	if os.path.lexists(unitePathTpl(getSession().getProjectConfigPath(path))):
		return pd.ValidatorResult("Project configuration already exists.", 'error')
	return None


@dataclass
class OpenExistingData(SerializableDataclass):
	path: FilePathStr = field(metadata=catMeta(
		kwargs=dict(label='Directory'),
		decorators=[
			pd.FolderPath(),
			pd.Validator(projPathValidator)
		]
	))


@dataclass
class CreateNewData(SerializableDataclass):
	name: str = field(metadata=catMeta(
		kwargs=dict(label='Project Name'),
	))
	parentDirectory: FilePathStr = field(default=DEFAULT_PROJECTS_LOCATION, metadata=catMeta(
		kwargs=dict(label='Parent Directory'),
		decorators=[
			pd.FolderPath(),
			pd.Validator(pd.folderPathValidator)
		]
	))
	customDirectoryName: str = field(default='', metadata=catMeta(
		kwargs=dict(
			label='Directory Name',
			placeholderText=property(lambda s: s.actualDirectoryName)
		),
		decorators=[
			pd.Validator(pd.fileNameValidator)
		]
	))

	@property
	def actualDirectoryName(self) -> str:
		if dirName := self.customDirectoryName:
			return dirName
		return sanitizeFileName(self.name)

	resultingDirectoryPath: FilePathStr = field(init=False, metadata=catMeta(
		readOnly=True,
		kwargs=dict(label=''),
		decorators=[
			pd.ReadOnlyLabel(),
			pd.Validator(newProjDirectoryPathValidator)
		]
	))  # overridden by a read-only property further down. Used ro define validation and GUI.


CreateNewData.resultingDirectoryPath = property(lambda self: joinFilePath(self.parentDirectory, self.actualDirectoryName))
CreateNewData.resultingDirectoryPath.__set_name__(CreateNewData, 'resultingDirectoryPath')


@dataclass
class CreateFromExistingData(SerializableDataclass):
	path: FilePathStr = field(metadata=catMeta(
		kwargs=dict(label='Directory'),
		decorators=[
			pd.FolderPath(),
			pd.Validator(projPathValidator)
		]
	))


@dataclass
class DialogPage(Generic[_T], ABC):
	tabOptions: TabOptions
	data: _T

	@abstractmethod
	def onGUI(self, gui: DatapackEditorGUI) -> None:
		pass

	def validate(self) -> list[pd.ValidatorResult]:
		"""
		errors are always first in the list.
		:return:
		"""
		data = self.data
		return data.validate()

	def hasNoError(self) -> bool:
		valRes = self.validate()
		return not valRes or valRes[0].style != 'error'

	@abstractmethod
	def acceptAction(self, gui: DatapackEditorGUI) -> None:
		pass


@dataclass
class OpenExistingDialogPage(DialogPage[OpenExistingData]):
	def onGUI(self, gui: DatapackEditorGUI) -> None:
		data = self.data
		with gui.groupBox("Select Existing Project"):
			gui.propertyField(data, 'path', enabled=True)
		gui.addVSpacer(0, SizePolicy.Expanding)  # preventVStretch

	def acceptAction(self, gui: DatapackEditorGUI) -> None:
		path = self.data.path.rstrip('/\\')
		getSession().openProject(path)


@dataclass
class CreateNewDialogPage(DialogPage[CreateNewData]):

	creators: list[ProjectCreator] = field(default_factory=list)
	projectOptionsShown: bool = field(default=True, init=False)

	def __post_init__(self) -> None:
		self.creators = [
			pcCls()
			for plugin in PLUGIN_SERVICE.activePlugins
			for pcCls in plugin.projectCreators()
		]

	def onGUI(self, gui: DatapackEditorGUI) -> None:
		data = self.data
		with gui.groupBox("Create New Project"):
			gui.propertyField(data, 'name')
			gui.propertyField(data, 'customDirectoryName')
			gui.propertyField(data, 'parentDirectory')
			gui.propertyField(data, 'resultingDirectoryPath')

		with gui.collapsibleGroupBox("Project Options", isOpen=self.projectOptionsShown) as optionsShown:
			self.projectOptionsShown = optionsShown
			if optionsShown:
				self._creatorsGUI(gui)

		if not optionsShown:
			gui.addVSpacer(0, SizePolicy.Expanding)  # preventVStretch

	def _creatorsGUI(self, gui: DatapackEditorGUI):
		creators = self.creators
		with gui.vLayout(seamless=True), gui.hSplitter() as splitter:
			with splitter.addArea(stretchFactor=0, seamless=True):
				treeResult = gui.tree(
					DataListBuilder(
						creators,
						labelMaker=lambda c, i: c.title,
						iconMaker=None,
						toolTipMaker=lambda c, i: c.title,
						columnCount=1,
						getId=id
					),
					headerVisible=True,
					loadDeferred=True,
				)
				if creators and treeResult.selectedItem is None:
					gui.selectRow(treeResult.selectionModel, 0)

			with splitter.addArea(stretchFactor=1, seamless=True):
				with gui.scrollBox():
					selectedCreator: Optional[ProjectCreator] = treeResult.selectedItem
					if selectedCreator is not None:
						selectedCreator.onGUI(gui)

	@staticmethod
	def _splitValidationResults(valResults: list[pd.ValidatorResult]) -> tuple[list[pd.ValidatorResult], list[pd.ValidatorResult]]:
		errors = [valRes for valRes in valResults if valRes.style == 'error']
		warnings = [valRes for valRes in valResults if valRes.style == 'warning']
		return errors, warnings

	def validate(self) -> list[pd.ValidatorResult]:
		errors, warnings = self._splitValidationResults(super().validate())
		for creator in self.creators:
			errors[len(errors):len(errors)], warnings[len(warnings):len(warnings)] = self._splitValidationResults(creator.validate())
		return errors + warnings

	def acceptAction(self, gui: DatapackEditorGUI) -> None:
		data = self.data
		try:
			os.makedirs(data.resultingDirectoryPath, exist_ok=True)
		except OSError as ex:
			getSession().showAndLogError(ex, "Error while creating project directory. Aborting.")
			return  # ?

		configPath = unitePathTpl(getSession().getProjectConfigPath(data.resultingDirectoryPath))
		try:
			with open(configPath, 'w') as f:
				f.write('{"@class": "Project"}')
		except OSError as ex:
			getSession().showAndLogError(ex, "Error while creating project config file. Aborting.")
			return  # ?

		project = getSession().openProject(data.resultingDirectoryPath)
		project.name = data.name

		# add aspects: Not necessary currently, because every Project gets all aspects in Project.setup()
		# projectCls = type(project)
		# for aspectType in data.projectAspects:
		# 	aspectCls = getAspectCls(projectCls, aspectType)
		# 	if aspectCls is not None:
		# 		project.aspects.add(aspectCls)

		for creator in self.creators:
			creator.initializeProject(gui, project)


@dataclass
class CreateFromExistingDialogPage(DialogPage[CreateFromExistingData]):
	def onGUI(self, gui: DatapackEditorGUI) -> None:
		# with gui.groupBox("Create From Existing"):
		with gui.hLayout(), gui.hCentered():
			gui.title("To come in a future version.", wordWrap=False)
		with gui.hCentered2():
			gui.title("😎")
		gui.addVSpacer(0, SizePolicy.Expanding)  # preventVStretch

	def acceptAction(self, gui: DatapackEditorGUI) -> None:
		gui.showInformationDialog("Creating From Existing Project...", "Please stand by...")


class NewProjectDialog(PythonGUIDialog):

	def __init__(
			self,
			parent: Optional[QWidget] = None,
			flags: Qt.WindowFlags | Qt.WindowType = Qt.WindowFlags(),
			*,
			x: Optional[int] = None,
			y: Optional[int] = None,
			width: Optional[int] = None,
			height: Optional[int] = None
	):
		super(PythonGUIDialog, self).__init__(DatapackEditorGUI, parent, flags, x=x, y=y, width=width, height=height)
		# basic window setup:
		self.setWindowTitle("Open or Create a new Project")
		self.disableContentMargins = True
		self.drawStatusbarBorder = False
		self.statusbarIsWindowPanel = True

		# initialize data:
		self._openExistingData: OpenExistingData = OpenExistingData(getSession().projectPath)
		self._createNewData: CreateNewData = CreateNewData("New Project", os.path.dirname(getSession().projectPath) or DEFAULT_PROJECTS_LOCATION)

		# GUI data:
		self.guiPages: dict[str, DialogPage] = {
			'openExisting': OpenExistingDialogPage(
				TabOptions("Open Existing"),
				OpenExistingData(getSession().projectPath)
			),
			'createNew': CreateNewDialogPage(
				TabOptions("Create New"),
				CreateNewData("New Project", os.path.dirname(getSession().projectPath) or DEFAULT_PROJECTS_LOCATION)
			),
			'createFromExisting': CreateFromExistingDialogPage(
				TabOptions("Create From Existing"),
				CreateFromExistingData(getSession().projectPath)
			),
		}
		self.selectedPageId: Optional[str] = None

	def OnGUI(self, gui: DatapackEditorGUI):
		guiPages = self.guiPages.copy()
		with gui.tabWidget() as tabs:
			for pageId, dialogPage in guiPages.items():
				with tabs.addView(dialogPage.tabOptions, id_=pageId, windowPanel=True, contentsMargins=(-1, -1, -1, 0)):
					dialogPage.onGUI(gui)

		self.selectedPageId = tabs.selectedView

	def OnStatusbarGUI(self, gui: DatapackEditorGUI):
		with gui.vLayout():
			gui.dialogButtons({
				MessageBoxButton.Ok: (lambda b: self.accept(), dict(enabled=self.isOkEnabled())),
				MessageBoxButton.Cancel: lambda b: self.reject(),
			})

	@property
	def selectedPage(self) -> Optional[DialogPage]:
		return self.guiPages.get(self.selectedPageId)

	def isOkEnabled(self) -> bool:
		return (page := self.selectedPage) is not None and page.hasNoError()

	@classmethod
	def showModal(
			cls,
			parent: Optional[QWidget] = None,
			*,
			x: Optional[int] = None,
			y: Optional[int] = None,
			width: Optional[int] = None,
			height: Optional[int] = None,
			kwargs: dict[str, Any] = None,
	) -> tuple[Optional[DialogPage], bool]:
		"""
		class method to create the dialog and return (value, accepted)
		:param parent:
		:param x:
		:param y:
		:param width:
		:param height:
		:param kwargs:
		:return:
		"""
		if kwargs is None:
			kwargs = {}
		dialog = cls(parent, x=x, y=y, width=width, height=height)
		# add kwArgs to dialog
		dialog._gui.addkwArgsToItem(dialog, kwargs)

		while True:
			result = dialog.exec()
			page = dialog.selectedPage
			isOk = (result == QDialog.Accepted) and page is not None
			if not isOk:
				return None, False

			valResults = page.validate()
			if valResults:
				if valResults[0].style == 'error':
					dialog._gui.showErrorDialog(
						"Some values are invalid:",
						"\n".join(f" - {valRes.message}" for valRes in valResults if valRes.style == 'error') +
						"\n\nPlease fix all indicated problems.",
						textFormat=Qt.TextFormat.MarkdownText
					)
					continue
				elif valResults[0].style == 'warning':
					if dialog._gui.showMessageDialog(
						"There are Warnings. Do you want to ignore them?",
						"\n".join(f" - {valRes.message}" for valRes in valResults if valRes.style == 'warning'),
						textFormat=Qt.TextFormat.MarkdownText,
						style=MessageBoxStyle.Warning,
						buttons=MessageBoxButtonPreset.IgnoreCancel
					) is MessageBoxButton.Ignore:
						return page, True
					else:
						continue
			return page, True
