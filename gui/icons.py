import os

from PyQt5.QtGui import QIcon

from Cat.GUI.components import catWidgetMixins
from Cat.GUI.icons import CompositionMode, iconCombiner, iconFromSVG, _Icons as CatIcons, iconGetter
from Cat.utils import getExePath

_ICON_IN_TREE_OPTIONS = dict(color_on=lambda: catWidgetMixins.standardBaseColors.Icon)


def makeIcon(name: str, ext='.svg'):
	_iconFolder = os.path.dirname(getExePath())
	return QIcon(os.path.join(_iconFolder, f'{name}{ext}'))


class _Icons(CatIcons):
	__slots__ = ()
	# util:
	slash:            QIcon = iconGetter('fa5s.slash')
	slashRed:         QIcon = iconGetter('fa5s.slash', options=[dict(color='red')])
	_shadowedSlash = (slashRed, dict(mode=CompositionMode.Erase, offset=(-0.075 * 0, 0.06))), (slash, dict(offset=(0, -0.06)))
	circleSolid:      QIcon = iconGetter("fa5s.circle", options=[dict(scale_factor=1.033019)])
	squareSolid:      QIcon = iconGetter("fa5s.square-full")

	bolt:             QIcon = iconGetter("fa5s.bolt")
	book:             QIcon = iconGetter("fa5s.book")
	carFront:         QIcon = iconGetter("fa5s.car")
	carFrontAlt:      QIcon = iconGetter("fa5s.car-alt")
	carSide:          QIcon = iconGetter("fa5s.car-side")
	globeSolid:       QIcon = iconGetter("fa5s.globe", options=[dict(scale_factor=1.033019)])
	globeOutlined:    QIcon = iconCombiner((globeSolid, dict(scale=0.885177, mode=CompositionMode.Normal)), (circleSolid, dict(mode=CompositionMode.Xor)))
	_globeAlt:        QIcon = iconGetter("fa.globe")
	globeAlt:         QIcon = iconCombiner((_globeAlt, dict(scale=876 / 748, offset=(0, -6.0 / 876))))
	mapPin:           QIcon = iconGetter("fa5s.map-pin")
	mapPinAlt:        QIcon = iconGetter("fa.map-pin")

	mapMarker:        QIcon = iconFromSVG(
		b'<svg aria-hidden="true" focusable="false" data-prefix="fas" data-icon="map-marker-alt" class="svg-inline--fa fa-map-marker-alt fa-w-12" role="img" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><path fill="currentColor" d="'
		+ b'M172.268 501.67C26.97 291.031 0 269.413 0 192 0 85.961 85.961 0 192 0s192 85.961 192 192c0 77.413-26.97 99.031-172.268 309.67-9.535 13.774-29.93 13.773-39.464 0zM192 272c44.183 0 80-35.817 80-80s-35.817-80-80-80-80 35.817-80 80 35.817 80 80 80z'
		+ b'"></path></svg>', scale=0.875, offset=(+(512-384)/512/2*0.875, -0.0)
	)
	mapMarkerAlt:     QIcon = iconGetter("fa5s.map-marker-alt")

	font:             QIcon = iconGetter('fa5s.font')

	# default:
	folder_closed:    QIcon = iconGetter("fa5s.folder")
	folder_open:      QIcon = iconGetter("fa5s.folder-open")
	folderInTree:     QIcon = iconGetter("fa5s.folder", on="fa5s.folder-open", active="fa5s.folder-open", options=[_ICON_IN_TREE_OPTIONS])
	archive:          QIcon = iconGetter("fa5s.file-archive")
	archiveInTree:    QIcon = iconGetter("fa5s.file-archive", on="fa5s.file-archive", active="fa5s.file-archive", options=[_ICON_IN_TREE_OPTIONS])
	file:             QIcon = iconGetter("fa5s.file")
	file_code:        QIcon = iconGetter("fa5.file-code")
	file_upload:      QIcon = iconGetter("fa5s.file-upload")
	disabledFile_upload: QIcon = iconCombiner(file_upload, *_shadowedSlash)
	code:             QIcon = iconGetter("fa5s.code")

	package:          QIcon = iconGetter("fa5s.box-open")
	packages:         QIcon = iconGetter("fa5s.boxes")
	project:          QIcon = iconGetter("fa5s.project-diagram")
	skipTestMode:     QIcon = iconCombiner(circleSolid, (bolt, dict(mode=CompositionMode.Erase)))
	offlineMode:      QIcon = iconCombiner((globeAlt, dict(scale=(-1, 1))), *_shadowedSlash)
	offlineMode2:     QIcon = iconCombiner((globeAlt, dict(scale=(1, 1))), *_shadowedSlash)

	types:            QIcon = iconGetter("fa5s.shapes")  # maybe?
	type_:            QIcon = iconGetter("fa5s.greater-than")  # maybe?
	lists:            QIcon = iconGetter("fa5s.list")
	table:            QIcon = iconGetter("fa5s.table")
	sitemap:          QIcon = iconGetter("fa5s.sitemap")
	mapSigns:         QIcon = iconGetter("fa5s.map-signs")
	signal:           QIcon = iconGetter("fa5s.signal")
	terminal:         QIcon = iconGetter("fa5s.terminal")
	hEllipsis:        QIcon = iconGetter("fa5s.ellipsis-h")
	vEllipsis:        QIcon = iconGetter("fa5s.ellipsis-v")

	color:            QIcon = iconGetter("fa5s.palette")

	# edit, modify, reload, etc.
	next:             QIcon = iconGetter('fa5s.arrow-right')
	prev:             QIcon = iconGetter('fa5s.arrow-left')
	up:               QIcon = iconGetter('fa5s.arrow-up')
	down:             QIcon = iconGetter('fa5s.arrow-down')

	chevronUp:        QIcon = iconGetter('fa5s.chevron-up')
	chevronDown:      QIcon = iconGetter('fa5s.chevron-down')
	chevronRight:     QIcon = iconGetter('fa5s.chevron-right')
	chevronLeft:      QIcon = iconGetter('fa5s.chevron-left')

	item:             QIcon = iconGetter('fa5s.asterisk')
	dot:              QIcon = iconGetter('fa5s.circle', options=[dict(scale_factor=0.285)])
	bars:             QIcon = iconGetter('fa5s.bars')
	add:              QIcon = iconGetter('fa5s.plus')
	remove:           QIcon = iconGetter('fa5s.minus')
	edit:             QIcon = iconGetter('fa5s.pen')
	editGrey:         QIcon = iconGetter('fa5s.pen', options=[dict(color='grey')])
	refresh:          QIcon = iconGetter('fa5s.sync-alt')
	disabledRefresh:  QIcon = iconCombiner(refresh, *_shadowedSlash)
	rerun:            QIcon = iconGetter('fa5s.redo')

	open:             QIcon = iconGetter("fa5s.folder-open")
	save:             QIcon = iconGetter("fa5s.save")
	saveAs:           QIcon = iconCombiner(
		(save, dict(scale=(1, 1))),
		(edit, dict(mode=CompositionMode.Xor, scale=0.5, offset=(+0.33, 0.11 + 0 * -0.02))),
		# (editGrey, dict(scale=0.66, offset=(+0.33, 0.11 + 0 * +0.02)))
	)
	undo:             QIcon = iconGetter('fa5s.undo')
	redo:             QIcon = iconGetter('fa5s.redo')

	settings:         QIcon = iconGetter('fa5s.sliders-h')
	# settings:         QIcon = iconGetter('fa.cog')
	search:           QIcon = iconGetter('fa5s.search')
	locate:           QIcon = mapMarker

	locateText:       QIcon = iconCombiner(
		# (locate, dict(scale=(1, 1))), 0.
		(mapMarker, dict(mode=CompositionMode.Normal, scale=0.75, offset=(-0.25, -0.125 + 0 * -0.02))),
		(font, dict(mode=CompositionMode.Normal, scale=0.75, offset=(+0.125, +0.125 + 0 * -0.02))),
	)
	locateTextAlt:  QIcon = iconCombiner(
		# (locate, dict(scale=(1, 1))),
		(mapPin, dict(mode=CompositionMode.Normal, scale=0.875, offset=(-0.25, -0.0625 + 0 * -0.02))),
		(font, dict(mode=CompositionMode.Normal, scale=0.75, offset=(+0.125, +0.125 + 0 * -0.02))),
	)

	spellCheck:       QIcon = iconGetter('fa5s.spell-check')
	error:            QIcon = iconGetter('fa5s.exclamation-circle')
	errorColored:     QIcon = iconGetter('fa5s.exclamation-circle', options=[dict(color='red')])
	warning:          QIcon = iconGetter('fa5s.exclamation-triangle')
	warningColored:   QIcon = iconGetter('fa5s.exclamation-triangle', options=[dict(color='#EBC700')])
	info:             QIcon = iconGetter('fa5s.info-circle')
	infoColored:      QIcon = iconGetter('fa5s.info-circle', options=[dict(color='#0072FF')])
	windowRestore:    QIcon = iconGetter('fa5s.window-restore')
	windowMaximize:   QIcon = iconGetter('fa5s.window-maximize')
	windowMinimize:   QIcon = iconGetter('fa5s.window-minimize')

	# composite icons:

	# examples:
	packageSlashed:   QIcon = iconCombiner(package, (slash, dict(mode=CompositionMode.Erase, offset=(-0.075 * 0, 0.06))), (slash, dict(offset=(0, -0.06))))
	ban:              QIcon = iconGetter('fa5s.ban')
	camera:           QIcon = iconGetter('fa5s.camera')
	stopwatch:        QIcon = iconGetter('fa5s.stopwatch')
	camera_ban:       QIcon = iconGetter('fa5s.camera', 'fa5s.ban', options=[dict(scale_factor=0.5, active='fa5s.balance-scale'), dict(color='red')])
	dota:              QIcon = iconCombiner(
		(hEllipsis, dict(mode=CompositionMode.Normal, scale=1)),
		(vEllipsis, dict(mode=CompositionMode.Crop, scale=1)),
	)

	# brands:
	git:              QIcon = iconGetter("fa5s.code-branch")  # = iconGetter("fa5b.git-alt")  # = makeIcon("git-alt-brands")
	java:             QIcon = iconGetter('fa5b.java')  # = makeIcon("java-brands")
	python:           QIcon = iconGetter('fa5b.python')


icons = _Icons()
