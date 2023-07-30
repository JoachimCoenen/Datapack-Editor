from dataclasses import dataclass
from typing import Optional, Sequence

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

from Cat.CatPythonGUI.GUI import SizePolicy, NO_MARGINS
from Cat.CatPythonGUI.GUI.pythonGUI import TabOptions
from Cat.CatPythonGUI.GUI.treeBuilders import DataTreeBuilder
from Cat.icons import icons
from base.model.project.project import Project, ProjectRoot, Root, DependencyDescr
from base.model.session import getSession
from gui.datapackEditorGUI import DatapackEditorGUI
from base.plugin import PluginBase, SideBarTabGUIFunc, PLUGIN_SERVICE, ToolBtnFunc


def initPlugin():
	PLUGIN_SERVICE.registerPlugin('ProjectPage', ProjectPagePlugin())


class ProjectPagePlugin(PluginBase):
	def sideBarTabs(self) -> list[tuple[TabOptions, SideBarTabGUIFunc, Optional[ToolBtnFunc]]]:
		return [(TabOptions('Project', icon=icons.project), projectPanelGUI, None)]


def _addRoot(gui: DatapackEditorGUI, project: Project):
	@dataclass
	class NamePath:
		name: str
		path: str

	def guiFUnc(gui: DatapackEditorGUI, val: NamePath) -> NamePath:
		val.name = gui.textField(val.name, 'name')
		val.path = gui.folderPathField(val.path, 'path')
		return val


	namePath, isOk = gui.askUserInput(
		f"Add new Root",
		NamePath("new Root", ""),
		guiFUnc
	)
	if isOk:
		project.addRoot(ProjectRoot(namePath.name, namePath.path))


def _removeRoot(gui: DatapackEditorGUI, project: Project, root: ProjectRoot):
	if gui.askUser(f"remove root '{root.name}' from project?", "this cannot be undone!", textFormat=Qt.PlainText):
		project.removeRoot(root)


def _moveRootUp(project: Project, root: ProjectRoot):
	roots = project.roots
	idx = roots.index(root)
	if idx > 0:
		roots[idx-1], roots[idx] = roots[idx], roots[idx-1]


def _moveRootDown(project: Project, root: ProjectRoot):
	roots = project.roots
	idx = roots.index(root)
	if idx < len(roots) - 1:
		roots[idx], roots[idx+1] = roots[idx+1], roots[idx]


def _editRoot(gui: DatapackEditorGUI, project: Project, root: ProjectRoot):
	newName, isOk = gui.askUserInput(
		f"Edit '{root.name}'",
		root.name,
	)
	if isOk:
		root.name = newName


def _refreshRoots(project: Project):
	project.resolveDependencies()
	project.analyzeDependencies()


def projectPanelGUI(gui: DatapackEditorGUI):  # , *, roundedCorners: RoundedCorners, cornerRadius: float):
	with gui.scrollBox(contentsMargins=(gui.panelMargins, gui.panelMargins, gui.panelMargins, gui.panelMargins), preventVStretch=True):  # , roundedCorners=roundedCorners, cornerRadius=cornerRadius):
		project = getSession().project

		gui.title("Basics")
		project.name = gui.textField(project.name, 'name')
		project.path = gui.folderPathField(project.path, 'path')
		gui.helpBox("invallid project" if not project.isValid else "", style='error')
		gui.checkbox(project.isEmpty, 'is empty', enabled=False)

		gui.vSeparator()
		rootsGUI(gui, project)


def rootsGUI(gui: DatapackEditorGUI, project: Project):
	def childrenMaker(item: Project | ProjectRoot | DependencyDescr) -> Sequence[ProjectRoot | DependencyDescr]:
		if isinstance(item, Project):
			return project.roots
		elif isinstance(item, Root):
			return item.dependencies
		elif isinstance(item, DependencyDescr):
			return item.resolved.dependencies if item.resolved is not None else ()
		elif isinstance(item, tuple):
			return item
		else:
			return ()

	def labelMaker(item: Project | ProjectRoot | DependencyDescr, c: int) -> str:
		if isinstance(item, Project):
			return project.name
		elif isinstance(item, Root):
			return item.name
		elif isinstance(item, DependencyDescr):
			return item.name if item.resolved is not None else f"{item.name} (missing)"
		else:
			return str(item)

	def iconMaker(item: Project | ProjectRoot | DependencyDescr, c: int) -> Optional[QIcon]:
		if c > 0:
			return None
		if isinstance(item, Project):
			return icons.project
		elif isinstance(item, Root):
			return icons.project
		elif isinstance(item, DependencyDescr):
			return icons.book
		else:
			return None

	def toolTipMaker(item: Project | ProjectRoot | DependencyDescr, c: int=0) -> Optional[str]:
		if isinstance(item, Project):
			return project.path
		elif isinstance(item, Root):
			return item.normalizedLocation
		elif isinstance(item, DependencyDescr):
			return f'{item.identifier} ({item.resolved.normalizedLocation if item.resolved is not None else "missing"})'
		else:
			return str(type(item))

	gui.title("Roots")
	with gui.vLayout(seamless=True):
		selected = gui.tree(
			DataTreeBuilder(
				(project,),
				childrenMaker=childrenMaker,
				labelMaker=labelMaker,
				iconMaker=iconMaker,
				toolTipMaker=toolTipMaker,
				columnCount=1,
				onCopy=toolTipMaker,
				getId=id
			),
			stretchLastColumn=True
		).selectedItem
		with gui.hPanel(contentsMargins=NO_MARGINS, seamless=True):
			isProjectRoot = isinstance(selected, ProjectRoot)
			canMoveDown = isProjectRoot and project.roots and project.roots[-1] is not selected
			canMoveUp = isProjectRoot and project.roots and project.roots[0] is not selected
			if gui.toolButton(icon=icons.refresh, tip="refresh dependencies", enabled=True):
				_refreshRoots(project)
			gui.addHSpacer(0, SizePolicy.Expanding)
			if gui.toolButton(icon=icons.edit, tip='Edit', enabled=isProjectRoot):
				_editRoot(gui, project, selected)
			if gui.toolButton(icon=icons.up, tip='Move up', enabled=canMoveUp):
				_moveRootUp(project, selected)
			if gui.toolButton(icon=icons.down, tip='Move down', enabled=canMoveDown):
				_moveRootDown(project, selected)
			if gui.toolButton(icon=icons.remove, tip='Remove selected from project', enabled=isProjectRoot):
				_removeRoot(gui, project, selected)
			if gui.toolButton(icon=icons.add, tip='Add'):
				_addRoot(gui, project)

		# moddleOverlap = (1, 1, 1, 0)
		# shouldAppendElement = self.toolButton(icon=icons.add, tip='Add', overlap=(0, 1, 0, 0), roundedCorners=CORNERS.NONE)
		# shouldDeleteSelected = self.toolButton(icon=icons.remove, tip='Delete selected [Del]', overlap=moddleOverlap, enabled=someElementIsSelected)  # , shortcut=QKeySequence.Delete
		# shouldChangeSelected = self.toolButton(icon=icons.edit, tip='Change selected [F2]', overlap=moddleOverlap, shortcut=Qt.Key_F2, enabled=someElementIsSelected)
		# shouldMoveUp = self.toolButton(icon=icons.up, tip='Move up', overlap=moddleOverlap, enabled=someElementIsSelected)
		# shouldMoveDown = self.toolButton(icon=icons.down, tip='Move down', overlap=moddleOverlap, enabled=someElementIsSelected)


def rootsGUI2(gui: DatapackEditorGUI, project: Project):
	gui.title("Roots")
	with gui.vLayout(seamless=True):
		for root in project.roots:
			rootPanelGUI(gui, root)
			gui.vSeparator()
		with gui.hPanel(contentsMargins=NO_MARGINS, seamless=True):
			gui.addHSpacer(0, SizePolicy.Expanding)
			if gui.toolButton(icon=icons.add, tip='Add'):
				_addRoot(gui, project)

		# moddleOverlap = (1, 1, 1, 0)
		# shouldAppendElement = self.toolButton(icon=icons.add, tip='Add', overlap=(0, 1, 0, 0), roundedCorners=CORNERS.NONE)
		# shouldDeleteSelected = self.toolButton(icon=icons.remove, tip='Delete selected [Del]', overlap=moddleOverlap, enabled=someElementIsSelected)  # , shortcut=QKeySequence.Delete
		# shouldChangeSelected = self.toolButton(icon=icons.edit, tip='Change selected [F2]', overlap=moddleOverlap, shortcut=Qt.Key_F2, enabled=someElementIsSelected)
		# shouldMoveUp = self.toolButton(icon=icons.up, tip='Move up', overlap=moddleOverlap, enabled=someElementIsSelected)
		# shouldMoveDown = self.toolButton(icon=icons.down, tip='Move down', overlap=moddleOverlap, enabled=someElementIsSelected)


def rootPanelGUI(gui: DatapackEditorGUI, root: ProjectRoot):
	with gui.hLayout(seamless=True):
		with gui.vPanel(seamless=True, preventVStretch=False):
			root.name = gui.textField(root.name, 'name')
			gui.folderPathField(root.location, 'location')
		with gui.vPanel(seamless=True, ):
			gui.toolButton(icon=icons.up, tip='move up')
			gui.toolButton(icon=icons.down, tip='move down')
		with gui.vPanel(seamless=True, preventVStretch=False):
			gui.addVSpacer(0, sizePolicy=SizePolicy.Expanding)
			gui.toolButton(icon=icons.remove, tip='remove')

