from dataclasses import dataclass
from typing import Optional, Protocol, NewType

from graphviz import Digraph

from base.gui.experimental.graphVizAdapter import renderGraph, DotGraph


class PluginLike(Protocol):

	@property
	def name(self) -> str: return ''

	@property
	def displayName(self) -> str: return ''

	def dependencies(self) -> set[str]: ...
	def optionalDependencies(self) -> set[str]: ...


NodeId = NewType('NodeId', str)


@dataclass
class PluginNode:
	id: NodeId
	plugin: Optional[PluginLike]

	@property
	def displayName(self) -> str:
		return self.plugin.displayName if self.plugin is not None else self.id


def getNodeId(name: str) -> NodeId:
	return NodeId(name.replace(':', '<'))


def buildPluginGraph(plugins: list[PluginLike]) -> DotGraph:

	# all existing plugins:
	allPluginNodes: dict[str, PluginNode] = {plugin.name: (PluginNode(getNodeId(plugin.name), plugin)) for plugin in plugins}

	# all missing plugins:
	allDepPlugins: set[str] = set()
	for plugin in plugins:
		allDepPlugins |= plugin.dependencies()
		allDepPlugins |= plugin.optionalDependencies()
	allMissingNodes: list[PluginNode] = [PluginNode(getNodeId(dep), None) for dep in allDepPlugins - allPluginNodes.keys()]

	# all edges:
	dependencies         = {(plugin.id, getNodeId(dep)) for plugin in allPluginNodes.values() for dep in plugin.plugin.dependencies()}
	optionalDependencies = {(plugin.id, getNodeId(dep)) for plugin in allPluginNodes.values() for dep in plugin.plugin.optionalDependencies()}

	# buildGraph:
	f = Digraph('plugin_dependencies', filename='fsm.gv')
	f.attr('graph', mode='major', overlap='false', ranksep='1.0')  # , sep='+32')

	# add all Nodes for existing Plugins:
	f.attr('node', shape='box', fontname='Arial', fontsize='10')
	for node in allPluginNodes.values():
		f.node(node.id, label=node.displayName)

	# add all Nodes for missing Plugins:
	f.attr('node', shape='ellipse', fontname='Arial', fontsize='9', style='dotted')
	for node in allMissingNodes:
		f.node(node.id, label=f"{node.displayName}\n(missing)")

	# edges for dependencies:
	f.attr('edge', arrowhead='none', arrowtail='empty', dir='back', style='solid')
	for srcId, dstId in dependencies:
		f.edge(dstId + ':s', srcId + ':n', sametail='DependsOn', samehead='IsDependencyOf')

	# edges for optional dependencies:
	f.attr('edge', arrowhead='none', arrowtail='empty', dir='back', style='dotted')
	for srcId, dstId in optionalDependencies:
		f.edge(dstId + ':s', srcId + ':n', sametail='DependsOn', samehead='IsDependencyOf')

	return renderGraph(f, engine='dot')
