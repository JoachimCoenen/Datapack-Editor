from typing import Callable, Optional, overload

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPen, QBrush

from Cat.GUI import PythonGUI, Style
from Cat.GUI.components.renderArea import ArrowType, CatPainter, Pens, Polyline, Rect, Vector
from Cat.GUI.pythonGUI import PythonGUIDialog
from base.model.session import getSession

try:
	from base.gui.experimental.graphVizAdapter import DotGraph, DotGraphEdge, DotGraphObject, Point, DotGraphStyleableBase, DotGraphLabeledBase
except ImportError:
	DotGraph = None
	Point = None
	DotGraphEdge = None
	DotGraphObject = None
	DotGraphStyleableBase = None
	DotGraphLabeledBase = None
	HAS_GRAPHVIZ = False
else:
	HAS_GRAPHVIZ = True


if HAS_GRAPHVIZ:

	lineStyleConversion = {
		#          (lineStyle, lineWidthIncrease)
		'dashed' : (Qt.PenStyle.DashLine, 0),
		'dotted' : (Qt.PenStyle.DotLine, 0),
		'solid'  : (Qt.PenStyle.SolidLine, 0),
		'invis'  : (Qt.PenStyle.NoPen, 0),
		'bold'   : (Qt.PenStyle.SolidLine, 1),
	}

	arrowStyleConversion = {
		#          (arrowType, inverted, empty
		'box'    : (ArrowType.box, False, False),
		'crow'   : (ArrowType.arrow, True, True),
		'curve'  : (ArrowType.box, False, False),
		'diamond': (ArrowType.diamond, False, False),
		'dot'    : (ArrowType.dot, False, False),
		'icurve' : (ArrowType.box, True, False),
		'inv'    : (ArrowType.arrow, True, False),
		'none'   : (ArrowType.none, False, False),
		'normal' : (ArrowType.arrow, False, False),
		'tee'    : (ArrowType.box, False, False),
		'vee'    : (ArrowType.box, False, False),
		'empty'  : (ArrowType.arrow, False, True),
	}

	def getArrowStyle(arrowName: str) -> tuple[ArrowType, bool, bool]:
		isOpen = False
		if arrowName.startswith('o'):
			isOpen = True
			arrowName = arrowName[1:]
		if arrowName.startswith(('l', 'r')):
			arrowName = arrowName[1:]
		arrowType, inverted, empty = arrowStyleConversion[arrowName]
		return arrowType, inverted, empty or isOpen

	def p2v(p: Point) -> Vector:
		return Vector(p.x, -p.y)

	PPI = 72.0


	def getTableStyle(gui: PythonGUI) -> str:  # , size: Vector
		tableStyle = Style({
			'td, table': Style({
				'border'         : f'1px solid {gui.host.palette().text().color().name()}',
				'background'     : gui.host.palette().toolTipBase().color().name(),
				'border-collapse': 'collapse',
				#'width'          : f'{int(size.x)}px',
			}),
			# 'table'    : Style({
			# 	'height': f'{int(size.y)}px',
			# }),
			'body': Style({
				'color'      : gui.host.palette().text().color().name(),
				'background' : gui.host.palette().base().color().name(),
				'vertical-align': 'middle',
			}),
		})
		return str(tableStyle)


	def getLabelStyle(gui: PythonGUI) -> str:
		labelStyle = Style({
			'body': Style({
				'color'      : gui.host.palette().text().color().name(),
				'background' : gui.host.palette().base().color().name(),
			}),
		})
		return str(labelStyle)

	def graphDialogInner(self: PythonGUIDialog, gui: PythonGUI, dotGraph: DotGraph) -> None:
		edgePen = QPen(gui.host.palette().text().color())
		edgeBrush = QBrush(Qt.NoBrush)
		nodePen = QPen(gui.host.palette().text().color())
		nodeBrush = QBrush(Qt.NoBrush)
		labelStyle = getLabelStyle(gui)
		tableStyle = getTableStyle(gui)

		bb = dotGraph.bb
		size = Vector(bb.urx, bb.ury) - Vector(bb.llx, bb.lly)
		cp: CatPainter = gui.renderArea(boundingSize=size, cornerRadius=self.windowCornerRadius)
		if gui.isLastRedraw:
			with cp:  # CatPainter(ra) as cp:
				cp.setBoundingSize(size.x, size.y)
				with cp.scaled(scale=Vector(1, 1), translation=Vector(-bb.llx, size.y - bb.lly)):
					for node in dotGraph.objects:
						_drawObject(cp, node, nodePen, nodeBrush, tableStyle)
					for edge in dotGraph.edges:
						_drawEdge(cp, edge, edgePen, edgeBrush, labelStyle)


	def _modifyPenBrushStyle(dgo: DotGraphStyleableBase, basePen: QPen, baseBrush: QBrush) -> tuple[QPen, QBrush]:
		penWidth = dgo.penwidth
		lineStyle, lineWidthIncrease = lineStyleConversion.get(dgo.style)

		pen = QPen(basePen)
		pen.setStyle(lineStyle)
		pen.setWidth(int(penWidth + lineWidthIncrease))

		if dgo.color is not None:
			pen.setColor(QColor(dgo.color))

		brush = QBrush(baseBrush)
		if dgo.fillcolor is not None:
			brush.setColor(dgo.fillcolor)

		return pen, brush

	@overload
	def _drawLabeledBase(cp: CatPainter, node: DotGraphLabeledBase, *, labelRect: Rect, labelStyle: str, pen: QPen): ...
	@overload
	def _drawLabeledBase(cp: CatPainter, node: DotGraphLabeledBase, *, labelPos: Vector, labelStyle: str, pen: QPen): ...

	def _drawLabeledBase(cp: CatPainter, node: DotGraphLabeledBase, *, labelRect: Optional[Rect] = None, labelPos: Optional[Vector] = None, labelStyle: str, pen: QPen):
		if node.label is not None:
			if True or node.label.startswith('<'):
				doc = cp.getTextDocument('', font=node.fontname, size=node.fontsize)
				doc.setDefaultStyleSheet(labelStyle)

				if labelRect is not None:
					labelSize = labelRect.bottomRight - labelRect.topLeft
					# ? doc.setPageSize(QSizeF(labelSize.x, labelSize.y))
					doc.setTextWidth(labelSize.x)

				if node.label.startswith('<'):
					doc.setHtml(node.label)
				else:
					doc.setPlainText(node.label)

				if labelPos is None:
					labelPos = labelRect.center
				actualLabelSize = Vector(doc.size().width(), doc.size().height())
				labelRect = Rect(center=labelPos, size=actualLabelSize)

				cp.drawTextDocument(doc, labelRect)
			else:
				cp.text(node.label, labelRect, font=node.fontname, size=node.fontsize, pen=pen)

	# def _drawObjectLabelOLD(cp: CatPainter, node: DotGraphObject, nodeRect: Rect, pen: QPen, tableStyle: str):
	# 	if node.label is not None:
	# 		labelRect = nodeRect.adjusted(-1, -1, +2, +1)
	# 		if node.label.startswith('<'):
	# 			doc = cp.getTextDocument('', font=node.fontname, size=node.fontsize)
	# 			labelSize = labelRect.bottomRight - labelRect.topLeft
	# 			doc.setDefaultStyleSheet(tableStyle)
	# 			doc.setPageSize(QSizeF(labelSize.x, labelSize.y))
	# 			doc.setTextWidth(labelSize.x)
	# 			doc.setHtml(node.label)
	# 			cp.drawTextDocument(doc, labelRect)
	# 		else:
	# 			cp.text(node.label, labelRect, font=node.fontname, size=node.fontsize, pen=pen)

	def _drawObjectLabel(cp: CatPainter, node: DotGraphObject, nodeRect: Rect, labelStyle: str, pen: QPen):
		_drawLabeledBase(cp, node, labelRect=nodeRect.adjusted(-1, -1, +2, +1), labelStyle=labelStyle, pen=pen)


	def _drawObject(cp: CatPainter, node: DotGraphObject, nodePen: QPen, nodeBrush: QBrush, tableStyle: str):
		pen, brush = _modifyPenBrushStyle(node, nodePen, nodeBrush)

		nodeRect = Rect(center=p2v(node.pos), size=Vector(node.width * PPI, node.height * PPI))
		if node.shape in {'box', 'rect', 'rectangle', 'square'}:
			cp.rect(nodeRect, pen=pen, brush=brush)
		elif node.shape in {'circle', 'ellipse', 'oval'}:
			cp.ellipse(nodeRect, pen=pen, brush=brush)
		elif node.shape == 'plaintext':
			cp.borderRect(nodeRect, pen=Pens.lightgray)
			pass
		else:
			cp.borderRect(nodeRect, pen=Pens.red)

		_drawObjectLabel(cp, node, nodeRect, tableStyle, pen=pen)


	def _drawEdgeLabel(cp: CatPainter, edge: DotGraphEdge, labelStyle: str, pen: QPen):
		_drawLabeledBase(cp, edge, labelPos=p2v(edge.lp), labelStyle=labelStyle, pen=pen)
		# if edge.label is not None:
		# 	doc = cp.getTextDocument('', font=edge.fontname, size=edge.fontsize)
		# 	doc.setDefaultStyleSheet(labelStyle)
		# 	if edge.label.startswith('<'):
		# 		doc.setHtml(edge.label)
		# 	else:
		# 		doc.setPlainText(edge.label)
		# 	labelSize = Vector(doc.size().width(), doc.size().height())
		# 	labelRect = Rect(center=p2v(edge.lp), size=labelSize * 1)
		# 	cp.drawTextDocument(doc, labelRect)


	def _drawEdge(cp: CatPainter, edge: DotGraphEdge, edgePen: QPen, edgeBrush: QBrush, labelStyle: str):
		pen, brush = _modifyPenBrushStyle(edge, edgePen, edgeBrush)

		ePos = edge.pos
		allPoints = ([ePos.start] if ePos.start else []) + ePos.points + ([ePos.end] if ePos.end else [])
		line = Polyline([p2v(p) for p in allPoints], isClosed=False)
		# arrowType = ArrowType(randint(ArrowType.arrow.value, ArrowType.diamond.value))
		if edge.arrowhead != 'none':
			# line[-1] = cp.drawArrowlike(line[-1], line[-2], 10., *getArrowStyle(edge.arrowhead), pen=pen)
			p1 = line[-1]
			i, p2 = next(((-i, p) for i, p in enumerate(reversed(line), 1) if p != p1), (None, None))
			if p2 is None:
				p2 = p1 + Vector(0, +1)
				i = -1
			arrowEnd = cp.drawArrowlike(p1, p2, 10., *getArrowStyle(edge.arrowhead), pen=pen, brush=brush)
			line[i:] = (arrowEnd,) * -i

		if edge.arrowtail != 'none':
			p1 = line[0]
			i, p2 = next(((i, p) for i, p in enumerate(line) if p != p1), (None, None))
			if p2 is None:
				p2 = p1 + Vector(0, +1)
				i = 0
			arrowEnd = cp.drawArrowlike(p1, p2, 10., *getArrowStyle(edge.arrowtail), pen=pen, brush=brush)
			line[:i] = (arrowEnd,) * i
		if ePos.start is not None:
			line = Polyline(line.values[1:], isClosed=False)
		cp.spline(line, pen=pen)

		_drawEdgeLabel(cp, edge, labelStyle, pen=pen)

else:
	def graphDialogInner(self: PythonGUIDialog, gui: PythonGUI, dotGraph: DotGraph) -> None:
		gui.helpBox("could not load graphviz.", style='error')


def showGraphDialog(gui: PythonGUI, _dotGraph: DotGraph, title: str):
	class GraphDialog(PythonGUIDialog):
		def OnGUI(self, gui: PythonGUI):
			graphDialogInner(self, gui, _dotGraph)

	dialog = GraphDialog(type(gui), )
	dialog.disableContentMargins = True
	dialog.setWindowTitle(title)
	dialog.exec()


def showGraphDialogSafe(gui: PythonGUI, dotGraphBuilder: Callable[[], DotGraph], title: str):
	try:
		dotGraph = dotGraphBuilder()
		showGraphDialog(gui, dotGraph, title)
	except Exception as e:
		getSession().showAndLogError(e)
