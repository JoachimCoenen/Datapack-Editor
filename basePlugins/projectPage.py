from collections import defaultdict
from dataclasses import dataclass, fields, Field, field
from typing import Optional, Sequence, Type, cast, Protocol, Any

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from recordclass import as_dataclass

from base.model.searchUtils import filterComputedChoices
from cat.GUI import SizePolicy, NO_MARGINS, MessageBoxStyle, propertyDecorators as pd
from cat.GUI.components.treeBuilders import DataTreeBuilder
from cat.GUI.pythonGUI import TabOptions
from cat.Serializable.serializableDataclasses import getDecorators
from gui.icons import icons
from cat.utils import format_full_exc
from cat.utils.logging_ import logError
from base.model.aspect import getAspectsForClass
from base.model.project.project import Project, ProjectRoot, Root, DependencyDescr, ProjectAspect
from base.model.session import getSession
from gui.datapackEditorGUI import DatapackEditorGUI, SearchableListContext
from base.plugin import PluginBase, SideBarTabGUIFunc, PLUGIN_SERVICE, ToolBtnFunc


def initPlugin():
	PLUGIN_SERVICE.registerPlugin('ProjectPage', ProjectPagePlugin())


class ProjectPagePlugin(PluginBase):

	def dependencies(self) -> set[str]:
		return set()

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


def _editRoot(gui: DatapackEditorGUI, root: ProjectRoot):
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
	with gui.scrollBox(contentsMargins=(gui.panelMargins, gui.panelMargins, gui.panelMargins, gui.panelMargins), preventVStretch=False):  # , roundedCorners=roundedCorners, cornerRadius=cornerRadius):
		project = getSession().project
		basicsGUI(gui, project)
		rootsAndDependenciesGUI(gui, project)
		aspectsGUI(gui, project)


def basicsGUI(gui: DatapackEditorGUI, project: Project):
	gui.title("Basics")
	with gui.vPanel(seamless=True):
		project.name = gui.textField(project.name, 'name')
		gui.folderPathField(project.path, 'path', enabled=False)
		gui.helpBox("Project missing config file ('.dpeproj')" if not project.hasConfigFile else " ", style='error')
		gui.checkbox(not project.isEmpty, 'is not empty', enabled=True)


def rootsAndDependenciesGUI(gui: DatapackEditorGUI, project: Project):
	gui.title("Roots & Dependencies")
	with gui.vPanel(seamless=True):
		with gui.tabWidget(documentMode=True) as tabs:
			with tabs.addTab(TabOptions("Roots"), 'roots', seamless=True):
				_RootsNS.rootsGUI(gui, project)
			with tabs.addTab(TabOptions("Dependencies"), 'dependencies', seamless=True):
				_DependenciesNS.dependenciesGUI(gui, project)


class InfoP(Protocol):
	root: Optional[Root]


@as_dataclass()
class RootInfo:
	root: Root


@as_dataclass()
class RequiredByInfo:
	root: Root
	descr: DependencyDescr


@as_dataclass()
class DependencyInfo:
	root: Optional[Root]
	descr: DependencyDescr
	# @property
	# def root(self) -> Optional[Root]:
	# 	return self.descr.resolved


class _DependenciesNS:

	@as_dataclass()  # (unsafe_hash=True)
	class DependencyDetails:
		name: str = field(compare=True)
		children: list[InfoP] = field(compare=False)

		def __hash__(self) -> int:
			return hash((_DependenciesNS.DependencyDetails, self.name))

		def __eq__(self, other) -> bool:
			if not isinstance(other, _DependenciesNS.DependencyDetails):
				return NotImplemented
			return self.name == other.name

		def __ne__(self, other) -> bool:
			if not isinstance(other, _DependenciesNS.DependencyDetails):
				return NotImplemented
			return self.name != other.name

	@classmethod
	def getDependencyDetails(
			cls,
			item: InfoP,
			requiredBy: dict[str, list[RequiredByInfo]],
	) -> list[DependencyDetails]:

		# def getProjModules(pr: InfoP) -> list[InfoP]:
		# 	localModules = getattr(pr, 'localModules', None)
		# 	return localModules if localModules is not None else []

		def getProjDependencies(info: InfoP) -> list[DependencyInfo]:
			return [DependencyInfo(d.resolved, d) for d in root.dependencies] if (root := info.root) is not None else []

		def getProjRequiredBy(info: InfoP) -> list[RequiredByInfo]:
			return requiredBy.get(root.identifier, []) if (root := info.root) is not None else []

		result = [
			# cls.DependencyDetails("Modules:", getProjModules(item)),
			cls.DependencyDetails("Dependencies:", getProjDependencies(item)),
			cls.DependencyDetails("Required by:", getProjRequiredBy(item)),
		]

		return [details for details in result if details.children]

	@classmethod
	def collectRequiredBy(cls, project: Project) -> dict[str, list[RequiredByInfo]]:
		allRoots = project.roots + project.deepDependencies
		requiredBy: defaultdict[str, list[RequiredByInfo]] = defaultdict(list)
		for root in allRoots:
			for dep in root.dependencies:
				requiredBy[dep.identifier].append(RequiredByInfo(root, dep))
		return dict(requiredBy)

	@classmethod
	def dependenciesGUI(cls, gui: DatapackEditorGUI, project: Project):
		requiredBy = cls.collectRequiredBy(project)
		allRoots = [RootInfo(root) for root in project.roots + project.deepDependencies]

		def childrenMaker(item: Project | InfoP | cls.DependencyDetails) -> Sequence[InfoP | cls.DependencyDetails]:
			if isinstance(item, list):
				return item
			elif isinstance(item, cls.DependencyDetails):
				return item.children
			else:  # elif isinstance(item, InfoP):
				return cls.getDependencyDetails(item, requiredBy)

		def labelMaker(item: list | InfoP | cls.DependencyDetails, c: int) -> str:
			if isinstance(item, list):
				return "<ROOT>"
			elif isinstance(item, RootInfo):
				return (item.root.name, '')[c]
			elif isinstance(item, DependencyInfo):
				return (item.descr.name, "(missing)" if item.descr.resolved is None else "")[c]
			elif isinstance(item, RequiredByInfo):
				return (item.root.name, "(missing)" if item.descr.resolved is None else "")[c]
			elif isinstance(item, cls.DependencyDetails):
				return (item.name, "")[c]
			else:
				return (str(item), "")[c]

		def iconMaker(item: list | InfoP | cls.DependencyDetails, c: int) -> Optional[QIcon]:
			if c > 0:
				return None
			if isinstance(item, list):
				return icons.lists
			elif isinstance(item, RootInfo):
				return icons.project if isinstance(item.root, ProjectRoot) else icons.book
			elif isinstance(item, DependencyInfo):
				return icons.book
			elif isinstance(item, RequiredByInfo):
				return icons.prev
			elif isinstance(item, cls.DependencyDetails):
				return None
			else:
				return None

		def toolTipMaker(item: list | InfoP | cls.DependencyDetails, c: int = 0) -> Optional[str]:
			if isinstance(item, list):
				return project.path
			elif isinstance(item, RootInfo):
				return f'{item.root.identifier} ({item.root.normalizedLocation})'
			elif isinstance(item, DependencyInfo):
				return f'{item.descr.identifier} ({item.root.normalizedLocation if item.root is not None else "(missing)"})'
			elif isinstance(item, RequiredByInfo):
				return f'{item.root.identifier} ({item.root.normalizedLocation})'
			elif isinstance(item, cls.DependencyDetails):
				return None
			else:
				return str(type(item))

		def getId(item: list | InfoP | cls.DependencyDetails) -> Any:
			if isinstance(item, list):
				return 1531608
			elif isinstance(item, RootInfo):
				return item.root.identifier + '}]root[{'
			elif isinstance(item, DependencyInfo):
				return item.descr.identifier + '}]dependency[{'
			elif isinstance(item, RequiredByInfo):
				return item.root.identifier + '}]requiredBy[{'
			elif isinstance(item, cls.DependencyDetails):
				return item.name
			else:
				return id(item)

		listContext = gui.customData.get('dependencies_listContext')
		if listContext is None:
			listContext = SearchableListContext()

		selected, listContext = gui.filteredTreeWithSearchField(
			allRoots,
			listContext,
			lambda filteredRoots: DataTreeBuilder(
				filteredRoots,
				childrenMaker=childrenMaker,
				labelMaker=labelMaker,
				iconMaker=iconMaker,
				toolTipMaker=toolTipMaker,
				columnCount=2,
				suppressUpdate=False,
				showRoot=False,
				onCopy=toolTipMaker,
				getId=getId,
			),
			getStrChoices=lambda items: [item.root.name for item in items],
			filterFunc=filterComputedChoices(lambda item: item.root.name),
		)
		gui.customData['dependencies_listContext'] = listContext

		with gui.hPanel(contentsMargins=NO_MARGINS, seamless=True):
			if gui.toolButton(icon=icons.refresh, tip="refresh dependencies", enabled=True):
				_refreshRoots(project)
			gui.addHSpacer(0, SizePolicy.Expanding)
			if gui.toolButton(icon=icons.edit, tip='Edit', enabled=False):
				_editRoot(gui, selected)
			if gui.toolButton(icon=icons.up, tip='Move up', enabled=False):
				_moveRootUp(project, selected)
			if gui.toolButton(icon=icons.down, tip='Move down', enabled=False):
				_moveRootDown(project, selected)
			if gui.toolButton(icon=icons.remove, tip='Remove selected from project', enabled=False):
				_removeRoot(gui, project, selected)
			if gui.toolButton(icon=icons.add, tip='Add', enabled=False):
				_addRoot(gui, project)


class _RootsNS:
	@classmethod
	def rootsGUI(cls, gui: DatapackEditorGUI, project: Project):
		def childrenMaker(item: Project | Root | DependencyDescr) -> Sequence[Root | DependencyDescr]:
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

		def labelMaker(item: Project | Root | DependencyDescr, c: int) -> str:
			if isinstance(item, Project):
				return project.name
			elif isinstance(item, Root):
				return item.name
			elif isinstance(item, DependencyDescr):
				return item.name if item.resolved is not None else f"{item.name} (missing)"
			else:
				return str(item)

		def iconMaker(item: Project | Root | DependencyDescr, c: int) -> Optional[QIcon]:
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

		def toolTipMaker(item: Project | Root | DependencyDescr, c: int = 0) -> Optional[str]:
			if isinstance(item, Project):
				return project.path
			elif isinstance(item, Root):
				return item.normalizedLocation
			elif isinstance(item, DependencyDescr):
				return f'{item.identifier} ({item.resolved.normalizedLocation if item.resolved is not None else "missing"})'
			else:
				return str(type(item))

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
				_editRoot(gui, selected)
			if gui.toolButton(icon=icons.up, tip='Move up', enabled=canMoveUp):
				_moveRootUp(project, selected)
			if gui.toolButton(icon=icons.down, tip='Move down', enabled=canMoveDown):
				_moveRootDown(project, selected)
			if gui.toolButton(icon=icons.remove, tip='Remove selected from project', enabled=isProjectRoot):
				_removeRoot(gui, project, selected)
			if gui.toolButton(icon=icons.add, tip='Add'):
				_addRoot(gui, project)


def aspectsGUI(gui: DatapackEditorGUI, project: Project):
	gui.title("Aspects")
	with gui.vLayout(seamless=True):
		for aspect in list(project.aspects):
			aspectPanelGUI(gui, project, aspect)
		with gui.hPanel(contentsMargins=NO_MARGINS, seamless=True):
			gui.addHSpacer(0, SizePolicy.Expanding)
			if gui.toolButton(icon=icons.add, tip='Add'):
				_addAspectGUI(gui, project)


def aspectPanelGUI(gui: DatapackEditorGUI, project: Project, aspect: ProjectAspect):
	allFields = [f for f in fields(aspect) if all(not isinstance(d, pd.NoUI) for d in getDecorators(f))]
	with gui.vPanel(seamless=True, preventVStretch=False):
		with gui.hPanel(seamless=True, preventVStretch=False):
			isOpen = gui.spoiler(drawDisabled=not allFields)
			gui.label(aspect.getAspectType())
			gui.addHSpacer(0, SizePolicy.Expanding)
			if gui.toolButton(icon=icons.remove, tip='remove'):
				_removeAspectGUI(gui, project, aspect)
		if isOpen and allFields:
			with gui.vPanel(), gui.indentation():
				aspectOptionsGUI(gui, aspect, allFields)


def aspectOptionsGUI(gui: DatapackEditorGUI, aspect: ProjectAspect, allFields: list[Field]):
	try:
		for f in allFields:
			gui.propertyField(aspect, f, True, enabled=True)
			gui.addVSpacer(gui.spacing, SizePolicy.Fixed)  # just a spacer
	except Exception as ex:
		logError(
			f"Error while drawing GUI for ProjectAspect {aspect.getAspectType()} ({type(aspect).__qualname__}):",
			format_full_exc(ex, indentLvl=1)
		)
		gui.helpBox(f"Error: \"{ex}\". For further details see logfile.log", style='error')


def _removeAspectGUI(gui: DatapackEditorGUI, project: Project, aspect: ProjectAspect):
	if gui.askUser(f"Do you really want to remove the Aspect '{aspect.getAspectType()}'?", "", style=MessageBoxStyle.Warning):
		project.aspects.discard(type(aspect))


def _addAspectGUI(gui: DatapackEditorGUI, project: Project):

	allAspectClss: list[Type[ProjectAspect]] = cast(list[Type[ProjectAspect]], list(getAspectsForClass(type(project)).values()))
	allAspectClss = [aspectCls for aspectCls in allAspectClss if aspectCls not in project.aspects]

	aspectCls = gui.searchableChoicePopup(
		cast(Type[ProjectAspect], None),
		'Aspects',
		allAspectClss,
		getSearchStr=lambda x: x.getAspectType(),
		labelMaker=lambda x, i: x.getAspectType(),
		iconMaker=lambda x, i: None,
		toolTipMaker=lambda x, i: x.getAspectType(),
		columnCount=1,
		onContextMenu=None,
		reevaluateAllChoices=True,
		# width=width,
		# height=height,
	)
	if aspectCls is not None:
		project.aspects.add(aspectCls)
