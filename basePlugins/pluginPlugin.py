from __future__ import annotations

from dataclasses import dataclass, field
from typing import Type

from Cat.CatPythonGUI.AutoGUI import propertyDecorators as pd
from Cat.CatPythonGUI.AutoGUI.autoGUI import AutoGUI
from Cat.CatPythonGUI.AutoGUI.decoratorDrawers import registerDecoratorDrawer, InnerDrawPropertyFunc
from Cat.CatPythonGUI.GUI import SizePolicy
from Cat.CatPythonGUI.GUI.treeBuilders import DataListBuilder
from Cat.Serializable.dataclassJson import catMeta, SerializableDataclass
from Cat.icons import icons
from base.gui.experimental.graphVizView import showGraphDialogSafe
from base.gui.experimental.pluginGraph import buildPluginGraph
from base.model.applicationSettings import SettingsAspect
from base.model.aspect import AspectType
from base.plugin import PluginBase, PLUGIN_SERVICE


PLUGIN_ASPECT_TYPE = AspectType('cce:plugins')


def initPlugin():
	PLUGIN_SERVICE.registerPlugin('PluginPlugin', PluginPlugin())


class PluginPlugin(PluginBase):

	def dependencies(self) -> set[str]:
		return set()

	def optionalDependencies(self) -> set[str]:
		return set()

	def settingsAspects(self) -> list[Type[SettingsAspect]]:
		return [PluginSettings]


class PluginsViewPD(pd.PropertyDecorator):
	pass


@dataclass
class PluginSettings(SettingsAspect):
	@classmethod
	def getAspectType(cls) -> AspectType:
		return PLUGIN_ASPECT_TYPE

	loadedPlugins: dict[str, PluginBase] = field(
		init=False,
		metadata=catMeta(
			readOnly=True,
			serialize=False,
			decorators=[PluginsViewPD(), pd.Title("Loaded Plugins")],
			# kwargs=dict(headers=("plugins",), label=None)
		)
	)


def getLoadedPlugins(self) -> dict[str, PluginBase]:
	from base.plugin import PLUGIN_SERVICE
	return PLUGIN_SERVICE.plugins.copy()


PluginSettings.loadedPlugins = property(getLoadedPlugins)


@registerDecoratorDrawer(PluginsViewPD)
def drawPluginsViewPD(gui_: AutoGUI, plugins: dict[str, PluginBase], type_, decorator_: PluginsViewPD, drawProperty_: InnerDrawPropertyFunc[str], owner_: SerializableDataclass, **kwargs) -> dict[str, PluginBase]:
	with gui_.vLayout(seamless=True):
		# gui_.valueField([(v.name,) for v in plugins.values()], type_=list[tuple[str]], headers=("plugins",), label=None)
		gui_.tree(
			DataListBuilder(
				list(plugins.values()),
				lambda p, c: p.name,
				lambda p, c: None,
				lambda p, c: f'{type(p).__qualname__} | {type(p).__module__}.{type(p).__name__}',
				1,
				getId=lambda p: p.name
			),
		)
		with gui_.hPanel(seamless=True):
			gui_.addHSpacer(9, SizePolicy.Expanding)
			if gui_.toolButton(icon=icons.project, tip="Show dependency tree", enabled=True):
				with gui_.overlay():
					showPluginDependencyTree(gui_, plugins)
	return plugins


@dataclass
class _LegendPluginDummy:
	name: str
	displayName: str
	_dependencies: set[str] = field(default_factory=set)
	_optionalDependencies: set[str] = field(default_factory=set)

	def dependencies(self) -> set[str]:
		return self._dependencies

	def optionalDependencies(self) -> set[str]:
		return self._optionalDependencies


def showPluginDependencyTree(gui: AutoGUI, plugins: dict[str, PluginBase]) -> None:
	legend: list[_LegendPluginDummy] = [
		_LegendPluginDummy(
			'cce:_legend_plugin_dummy__plugin',
			'A Plugin',
			_dependencies={'cce:_legend_plugin_dummy__required_plugin'},
			_optionalDependencies={'cce:_legend_plugin_dummy__optionally_required_plugin'},
		),
		_LegendPluginDummy(
			'cce:_legend_plugin_dummy__required_plugin',
			'A Required Plugin',
		),
		_LegendPluginDummy(
			'cce:_legend_plugin_dummy__optionally_required_plugin',
			'An Optionally Required Plugin',
		),
	]

	showGraphDialogSafe(gui, lambda: buildPluginGraph(legend + list(plugins.values())), "plugin Dependencies")