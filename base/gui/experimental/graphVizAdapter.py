from __future__ import annotations

import os
from dataclasses import dataclass, field
from json import JSONDecodeError
from typing import Optional

import graphviz
from graphviz.graphs import BaseGraph

from Cat.Serializable.serializableDataclasses import SerializableDataclass, catMeta
from Cat.utils.formatters import indentMultilineStr


class GraphRenderError(Exception):
	def __init__(self, msg: str, graphSource: Optional[str]):
		self.msg: str = msg
		self.graphSource: Optional[str] = graphSource

	def __str__(self):
		if self.graphSource is not None:
			return self.msg + '\nSource:\n' + str(indentMultilineStr(self.graphSource, indent='    '))
		else:
			return self.msg


def renderGraph(graph: BaseGraph, *, engine: str = 'dot') -> DotGraph:
	# engines = ['dot', 'sfdp', 'neato']  # graphviz.ENGINES  # ['fdp', 'dot', 'sfdp', 'twopi', 'neato']  ['dot', 'neato']
	graphFormat = 'json0'  # formats = ['json0', 'json', 'dot', 'xdot', 'dot_json', 'xdot_json', ]

	graph.engine = engine
	graph.format = graphFormat

	directory = 'temp'
	filename = f'graph_{engine}'
	fileExt = f'.{graphFormat}'
	filePath = os.path.join(directory, filename)

	try:
		graph.render(filename=filename, directory=directory, cleanup=False)
	except graphviz.backend.CalledProcessError as e:
		raise GraphRenderError(str(e), graph.source)
	except OSError as e:
		raise GraphRenderError(str(e), f"filename = '{filename}'\ndirectory = '{directory}'")

	inFilePath = filePath + fileExt
	try:
		with open(inFilePath, "r") as inFile:
			inText = inFile.read()
			dotGraph = DotGraph.fromJson(inText, onError=None)
	except JSONDecodeError as e:
		raise GraphRenderError(str(e), inText)
	except OSError as e:
		raise GraphRenderError(str(e), f"filepath = '{inFilePath}'")

	outFilePath = filePath + '_OUT' + fileExt
	try:
		with open(outFilePath, "w") as outFile:
			dotGraph.toJson(outFile)
	except OSError as e:
		raise GraphRenderError(str(e), f"filepath = '{outFilePath}'")
	return dotGraph


@dataclass
class Point:
	x: float
	y: float

	@classmethod
	def decode(cls, v: str) -> Point:
		return cls(*[float(c) for c in v.split(',')])

	def encode(self):
		return ','.join((str(self.x), str(self.y),))


@dataclass
class Rect:
	llx: float
	lly: float
	urx: float
	ury: float

	@classmethod
	def decode(cls, v: str) -> Rect:
		return cls(*[float(c) for c in v.split(',')])

	def encode(self):
		return ','.join((str(self.llx), str(self.lly), str(self.urx), str(self.ury),))


@dataclass
class Spline:
	points: list[Point]  # = Field(default_factory=list)
	start: Optional[Point] = None
	end: Optional[Point] = None

	@classmethod
	def decode(cls, v: str):
		splitted = v.split(' ')
		end = None
		if splitted and splitted[0].startswith('e'):
			end = splitted[0][2:]
			splitted = splitted[1:]
		start = None
		if splitted and splitted[0].startswith('s'):
			start = splitted[0][2:]
			splitted = splitted[1:]
		return cls([Point.decode(c) for c in splitted], Point.decode(start) if start else None, Point.decode(end) if end else None)

	def encode(self):
		pnts: list[str] = []
		if self.end:
			pnts.append(f'e,{self.end.encode()}')
		if self.start:
			pnts.append(f's,{self.start.encode()}')
		pnts.extend(c.encode() for c in self.points)
		return ' '.join(pnts)


@dataclass
class DotGraph(SerializableDataclass):
	name: str = field(default='')
	directed: bool = field(default=True)
	strict: bool = field(default=False)
	bb: Rect = field(default_factory=lambda: Rect(0, 0, 0, 0), metadata=catMeta(decode=lambda s, v: Rect.decode(v), encode=lambda s, v: v.encode()))
	mode: str = field(default="major")
	model: str = field(default='circuit')
	overlap: str = field(default='false')
	splines: str = field(default='ortho')
	_subgraph_cnt: int = field(default=0)
	objects: list[DotGraphObject] = field(default_factory=list)
	edges: list[DotGraphEdge] = field(default_factory=list)


@dataclass
class DotGraphStyleableBase(SerializableDataclass):
	fillcolor: Optional[str] = None
	color: Optional[str] = None
	style: str = 'solid'
	penwidth: float = 1.0


@dataclass
class DotGraphLabeledBase(SerializableDataclass):
	fontname: str = 'Arial'
	fontsize: float = field(default=10., metadata=catMeta(decode=lambda s, v: float(v), encode=lambda s, v: str(v)))
	label: Optional[str] = None


@dataclass
class DotGraphObject(DotGraphStyleableBase, DotGraphLabeledBase):
	_gvid: int = 0
	name: str = 'name'
	height: float = field(default=0.5, metadata=catMeta(decode=lambda s, v: float(v), encode=lambda s, v: str(v)))
	pos: Point = field(default_factory=lambda: Point(0., 0.), metadata=catMeta(decode=lambda s, v: Point.decode(v), encode=lambda s, v: v.encode()))
	shape: str = 'box'
	width: float = field(default=1.8611, metadata=catMeta(decode=lambda s, v: float(v), encode=lambda s, v: str(v)))


@dataclass
class DotGraphEdge(DotGraphStyleableBase, DotGraphLabeledBase):
	_gvid: int = 0
	tail: int = 117
	head: int = 54
	arrowhead: str = 'none'
	arrowtail: str = 'empty'
	dir: str = 'back'
	lp: Point = field(default_factory=lambda: Point(0., 0.), metadata=catMeta(decode=lambda s, v: Point.decode(v), encode=lambda s, v: v.encode()))
	pos: Spline = field(default_factory=lambda: Spline([]), metadata=catMeta(decode=lambda s, v: Spline.decode(v), encode=lambda s, v: v.encode()))
