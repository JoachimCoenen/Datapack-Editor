from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Any

from PyQt5.QtGui import QIcon

from Cat.GUI.components.treeBuilders import DataTreeBuilder
from Cat.GUI.pythonGUI import TabOptions
from gui.icons import icons
from base.model.project.index import Index, IndexBundle
from base.model.project.project import Root
from base.model.session import getSession
from gui.datapackEditorGUI import DatapackEditorGUI
from base.plugin import PluginBase, SideBarTabGUIFunc, PLUGIN_SERVICE, ToolBtnFunc


def initPlugin():
	PLUGIN_SERVICE.registerPlugin('PluginDebugPlugin', PluginDebugPlugin())


class PluginDebugPlugin(PluginBase):

	def dependencies(self) -> set[str]:
		return {'PluginPlugin'}

	def optionalDependencies(self) -> set[str]:
		return {'ProjectFiles'}  # ordering of gui elements

	def sideBarTabs(self) -> list[tuple[TabOptions, SideBarTabGUIFunc, Optional[ToolBtnFunc]]]:
		return [(TabOptions('Index Bundles', icon=icons.folder_open), indexBundlesGUI, None)]


def indexBundlesGUI(gui: DatapackEditorGUI):
	filteredProjectsFilesTreeGUI(gui, getSession().project.allRoots)


def filteredProjectsFilesTreeGUI(
		gui: DatapackEditorGUI,
		allRoots: list[Root],
):
	gui.tree(
		DataTreeBuilder(
			allRoots,
			_childrenMaker,
			_labelMaker,
			_iconMaker,
			_toolTipMaker,
			columnCount=1,
			suppressUpdate=False,
			showRoot=False,
			onCopy=_onCopy,
			getId=_getId,
		),
		loadDeferred=True,
	)


@dataclass(unsafe_hash=True)
class TreeItem:
	name: str
	value: Any = field(hash=False, compare=False)


def _labelMaker(data: TreeItem | Root, column: int) -> str:
	if isinstance(data, Root):
		return data.name if column == 0 else ""
	else:
		return data.name if column == 0 else (data.value if isinstance(data.value, str) else "")


def _iconMaker(data: TreeItem | Root, column: int) -> Optional[QIcon]:
	return None


def _toolTipMaker(data: TreeItem | Root, column: int) -> str:
	if isinstance(data, Root):
		return data.normalizedLocation
	else:
		return ""


def _onCopy(data: TreeItem | Root) -> str:
	if isinstance(data, Root):
		return data.normalizedLocation
	else:
		return data.value if isinstance(data.value, str) else data.name


def _getId(data: TreeItem | Root) -> str:
	if isinstance(data, Root):
		return data.normalizedLocation
	elif isinstance(data, (tuple, list)):
		return '123546'
	else:
		return data.name


def _childrenMaker(data: Root) -> list[TreeItem]:
	if isinstance(data, TreeItem):
		data = data.value
	if isinstance(data, list):
		return data
	elif isinstance(data, Root):
		return [TreeItem(type(bundle).__name__, bundle) for bundle in data.indexBundles]
	elif isinstance(data, IndexBundle):
		return [TreeItem(name, index) for name, index in data.subIndicesByName.items()]
	elif isinstance(data, Index):
		return [TreeItem(str(key), str(value)) for key, value in data.items()]
	else:
		return []
