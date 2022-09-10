import copy
import warnings
from dataclasses import replace, fields

from PyQt5.QtGui import QColor, qGray
import numpy as np

from Cat.CatPythonGUI.GUI.catWidgetMixins import BaseColors
from gui.themes.theme import addColorScheme, ColorScheme, Style, StylesModifier, updateGlobalStylesToMatchUIColors, GlobalStyles

enabled = True

_DO_PRINT = False


def initPlugin():
	addColorScheme(buildColorScheme())


def buildColorScheme() -> ColorScheme:
	scheme = ColorScheme('Default Dark', [])
	from .scheme_default import buildColorScheme
	lightScheme = buildColorScheme()

	scheme.uiColors = invertUIColors(lightScheme.uiColors)
	blackColor = scheme.uiColors.Input
	scheme.globalStyles = invertGlobalStyles(lightScheme.globalStyles, blackColor)
	updateGlobalStylesToMatchUIColors(scheme)
	scheme.globalStyles.defaultStyle |= Style(background=scheme.uiColors.Window)

	for language, styles in lightScheme.styles2.items():
		print(f"STYLES:")
		styles._styles = {name: invertStyle(style, blackColor, f'{language}:{name}') for name, style in styles._styles.items()}
		print(f"MODIFIERS:")
		styles.innerLanguageStyleModifiers = {name: invertStylesModifier(stylesMode, blackColor, f'{language}:{name}') for name, stylesMode in styles.innerLanguageStyleModifiers.items()}
		scheme.styles2[language] = styles

	# scheme.defaultStyle = invertStyle(lightScheme.defaultStyle)
	# scheme.lineNumberStyle = invertStyle(lightScheme.lineNumberStyle)
	# scheme.braceLightStyle = invertStyle(lightScheme.braceLightStyle)
	# scheme.braceBadStyle = invertStyle(lightScheme.braceBadStyle)
	# scheme.controlCharStyle = invertStyle(lightScheme.controlCharStyle)
	# scheme.indentGuideStyle = invertStyle(lightScheme.indentGuideStyle)
	# scheme.calltipStyle = invertStyle(lightScheme.calltipStyle)
	# scheme.foldDisplayTextStyle = invertStyle(lightScheme.foldDisplayTextStyle)
	#
	# scheme.caretLineStyle = invertStyle(lightScheme.caretLineStyle)
	return scheme


def invertUIColors(uiColors: BaseColors) -> BaseColors:
	inverted = {}
	for f in fields(uiColors):
		inverted[f.name] = invert(getattr(uiColors, f.name), name=f'uiColors:{f.name}')
	inverted = BaseColors(**inverted)
	inverted2 = copy.copy(inverted)

	darker = lerpColor(inverted.Panel, inverted.Window, 0.5)
	lighter = inverted.Window
	inverted2.Window = darker
	inverted2.Panel = lighter
	inverted2.Input = lighter
	inverted2.Button = lighter

	highlight = applyGamma(uiColors.Highlight, GAMMA_FOR_INVERT)
	lightHighlight = applyGamma(uiColors.LightHighlight, GAMMA_FOR_INVERT)
	highlightInv = applyGamma(inverted2.Highlight, GAMMA_FOR_INVERT)
	lightHighlightInv = applyGamma(inverted2.Highlight, GAMMA_FOR_INVERT)
	deltaGray = qGrayF(lightHighlight) - qGrayF(highlight)
	lightGray = qGrayF(highlightInv) + deltaGray
	lightHighlightInv2 = findColorForGrayGoal2(lightHighlightInv.hueF(), lightHighlightInv.hsvSaturationF(), lightGray)
	inverted2.LightHighlight = lightHighlightInv2
	# inverted2.Highlight = inverted.LightHighlight
	# inverted2.LightHighlight = inverted.Highlight

	gHighlight = qGrayF(inverted2.Highlight) >= 0.5
	gHighlightText = qGrayF(inverted2.HighlightedText) >= 0.5
	gText = qGrayF(inverted2.Text) >= 0.5
	if gHighlightText == gHighlight and gText != gHighlight:
		inverted2.HighlightedText = inverted2.Text

	return inverted2


def invertStylesModifier(stylesMod: StylesModifier, blackColor: QColor, name: str) -> StylesModifier:
	# return invertDataclass(stylesMod, blackColor)
	modifier = invertStyle(stylesMod.modifier, blackColor, f'{name}.modifier') if stylesMod.modifier is not None else None
	default = invertStyle(stylesMod.default, blackColor, f'{name}.default') if stylesMod.default is not None else None
	return replace(stylesMod, modifier=modifier, default=default)


def invertGlobalStyles(gs: GlobalStyles, blackColor: QColor) -> GlobalStyles:
	# return invertDataclass(globalStyles, blackColor)
	inverted = {
		f.name: invertStyle(getattr(gs, f.name), blackColor, f'globalStyles:{f.name}')
		for f in fields(GlobalStyles)
	}
	return replace(gs, **inverted)


def invertStyle(style: Style, blackColor: QColor, name: str) -> Style:
	# return invertDataclass(style, blackColor)
	foreground = invert(style.foreground, blackColor=blackColor, name=f'{name}.foreground') if style.foreground is not None else None
	background = invert(style.background, name=f'{name}.background') if style.background is not None else None
	if _DO_PRINT: print("----------------")
	return replace(style, foreground=foreground, background=background)


GAMMA_FOR_INVERT = 1.2  # 1.2
INV_GAMMA_FOR_INVERT = 1 / GAMMA_FOR_INVERT


def applyGamma(c: QColor, gamma: float) -> QColor:
	return QColor.fromHsvF(c.hsvHueF(), c.hsvSaturationF(), c.valueF() ** gamma)


def invert(c1: QColor, *, blackColor: QColor = QColor('black'), name: str):
	if _DO_PRINT:
		print(f"\n: {name} :")
	a, b = 1, 1
	c2 = applyGamma(c1, GAMMA_FOR_INVERT)
	bc2 = applyGamma(blackColor, GAMMA_FOR_INVERT)

	lightnessF = lerp(c2.lightnessF(), 0.0, 0.05)
	c3 = QColor.fromHslF(c2.hueF(), c2.hslSaturationF(), lightnessF)

	satFactor = 1 - a*(1 - lightnessF)**2
	hsvSaturationGoal = c3.hsvSaturationF() * satFactor

	blackLevel = bc2.lightnessF() * b
	if _DO_PRINT: print(f"blackLevel = {round(blackLevel, 5)}")
	grayGoal = lerp(1, blackLevel, qGrayF(c3))
	if _DO_PRINT:
		print(f"c1 = {c1.name()}")
		print(f"g1 (gray) = {round(grayGoal, 5)}")
		print(f"g2 (sat)  = {round(hsvSaturationGoal, 5)}")
	c4 = findColorForGrayGoal2(c3.hueF(), hsvSaturationGoal, grayGoal)
	c5 = applyGamma(c4, INV_GAMMA_FOR_INVERT)
	if _DO_PRINT:
		print(f"c5 = {c5.name()}")
	return c5


def lerpColor(c1: QColor, c2: QColor, x: float) -> QColor:
	return QColor.fromRgbF(
		lerp(c1.redF(), c2.redF(), x),
		lerp(c1.greenF(), c2.greenF(), x),
		lerp(c1.blueF(), c2.blueF(), x),
		lerp(c1.alphaF(), c2.alphaF(), x),
	)


def lerp(c1: float, c2: float, x: float) -> float:
	return c1 + (c2 - c1) * x


def clamp(x: float, min_: float, max_: float) -> float:
	return min(max(x, min_), max_)


def findColorForGrayGoal2(hueF: float, hsvSaturationGoal: float, grayGoal: float) -> QColor:

	def func(x):
		x2 = np.clip(x, 0, 1)
		c = QColor.fromHslF(hueF, x2[1], x2[0])
		p1 = qGrayF(c) - grayGoal
		p2 = c.hsvSaturationF() - hsvSaturationGoal
		return p1*p1 + p2*p2*2

	x0 = np.array([0.5, 0.5])
	res = minimize(func, x0)  # , bounds=(0, 1), disp=False)
	if _DO_PRINT:
		print(f"res = {res}")
	x2 = np.clip(res, 0, 1)
	c = QColor.fromHslF(hueF, x2[1], x2[0])
	if _DO_PRINT:
		print(f"p1 (gray) = {round(qGrayF(c) - grayGoal, 5)}")
		print(f"p2 (sat)  = {round(c.saturationF() - hsvSaturationGoal, 5)}")
	return c


def qGrayF(color: QColor) -> float:
	return qGray(color.rgb()) / 255


def colorToStr(c: QColor):
	return c.name()

class _MaxFuncCallError(RuntimeError):
	pass


def minimize(fun, x0, *, disp=False, bounds=None):
	return _minimize_neldermead(fun, x0, disp=disp, bounds=bounds)


def _minimize_neldermead(function, x0, disp=False, xatol=1e-8, fatol=1e-4, bounds=None):
	"""
	Minimization of scalar function of one or more variables using the
	Nelder-Mead algorithm. (SciPy implementation, but modified)

	References
	----------
	.. [1] Gao, F. and Han, L.
	   Implementing the Nelder-Mead simplex algorithm with adaptive
	   parameters. 2012. Computational Optimization and Applications.
	   51:1, pp. 259-277

	Copyright Notice
	----------------
	Copyright (c) 2001-2002 Enthought, Inc. 2003-2022, SciPy Developers.
	All rights reserved.

	Redistribution and use in source and binary forms, with or without
	modification, are permitted provided that the following conditions
	are met:

	1. Redistributions of source code must retain the above copyright
	   notice, this list of conditions and the following disclaimer.

	2. Redistributions in binary form must reproduce the above
	   copyright notice, this list of conditions and the following
	   disclaimer in the documentation and/or other materials provided
	   with the distribution.

	3. Neither the name of the copyright holder nor the names of its
	   contributors may be used to endorse or promote products derived
	   from this software without specific prior written permission.

	THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
	"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
	LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
	A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
	OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
	SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
	LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
	DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
	THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
	(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
	OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
	"""

	nonzdelt = 0.05
	zdelt = 0.00025

	if bounds is not None:
		x0 = np.clip(x0, bounds[0], bounds[1])

	N = len(x0)
	sim = np.empty((N + 1, N), dtype=x0.dtype)
	sim[0] = x0
	for k in range(N):
		y = np.array(x0, copy=True)
		if y[k] != 0:
			y[k] = (1 + nonzdelt)*y[k]
		else:
			y[k] = zdelt
		sim[k + 1] = y

	# If neither are set, then set both to default
	maxiter = N * 200
	maxfun = N * 200

	if bounds is not None:
		sim = np.clip(sim, bounds[0], bounds[1])

	one2np1 = list(range(1, N + 1))
	fsim = np.full((N + 1,), np.inf, dtype=float)

	fcalls = 0

	def func(x):
		nonlocal fcalls
		if fcalls >= maxfun:
			raise _MaxFuncCallError("Too many function calls")
		fcalls += 1
		return function(x)

	try:
		for k in range(N + 1):
			fsim[k] = func(sim[k])
	except _MaxFuncCallError:
		pass
	finally:
		ind = np.argsort(fsim)
		sim = np.take(sim, ind, 0)
		fsim = np.take(fsim, ind, 0)

	ind = np.argsort(fsim)
	fsim = np.take(fsim, ind, 0)
	# sort so sim[0,:] has the lowest function value
	sim = np.take(sim, ind, 0)

	iterations = 1

	while fcalls < maxfun and iterations < maxiter:
		try:
			if (np.max(np.ravel(np.abs(sim[1:] - sim[0]))) <= xatol and
					np.max(np.abs(fsim[0] - fsim[1:])) <= fatol):
				break

			xbar = np.add.reduce(sim[:-1], 0) / N
			xr = 2 * xbar - sim[-1]
			if bounds is not None:
				xr = np.clip(xr, bounds[0], bounds[1])

			fxr = func(xr)
			doshrink = 0

			if fxr < fsim[0]:
				xe = 3 * xbar - 2 * sim[-1]
				if bounds is not None:
					xe = np.clip(xe, bounds[0], bounds[1])
				fxe = func(xe)

				if fxe < fxr:
					sim[-1] = xe
					fsim[-1] = fxe
				else:
					sim[-1] = xr
					fsim[-1] = fxr
			else:  # fsim[0] <= fxr
				if fxr < fsim[-2]:
					sim[-1] = xr
					fsim[-1] = fxr
				else:  # fxr >= fsim[-2]
					# Perform contraction
					if fxr < fsim[-1]:
						xc = 1.5 * xbar - 0.5 * sim[-1]
						if bounds is not None:
							xc = np.clip(xc, bounds[0], bounds[1])
						fxc = func(xc)

						if fxc <= fxr:
							sim[-1] = xc
							fsim[-1] = fxc
						else:
							doshrink = 1
					else:
						# Perform an inside contraction
						xcc = 0.5 * xbar + 0.5 * sim[-1]
						if bounds is not None:
							xcc = np.clip(xcc, bounds[0], bounds[1])
						fxcc = func(xcc)

						if fxcc < fsim[-1]:
							sim[-1] = xcc
							fsim[-1] = fxcc
						else:
							doshrink = 1

					if doshrink:
						for j in one2np1:
							sim[j] = sim[0] + 0.5 * (sim[j] - sim[0])
							if bounds is not None:
								sim[j] = np.clip(sim[j], bounds[0], bounds[1])
							fsim[j] = func(sim[j])
			iterations += 1
		except _MaxFuncCallError:
			pass
		finally:
			ind = np.argsort(fsim)
			sim = np.take(sim, ind, 0)
			fsim = np.take(fsim, ind, 0)

	x = sim[0]
	fval = np.min(fsim)
	if disp:
		if fcalls >= maxfun:
			msg = 'Maximum number of function evaluations has been exceeded.'
			warnings.warn(msg, RuntimeWarning, 3)
		elif iterations >= maxiter:
			msg = 'Maximum number of iterations has been exceeded.'
			warnings.warn(msg, RuntimeWarning, 3)
		else:
			msg = 'Optimization terminated successfully.'
			print(msg)
		print("  Function evaluations: %d" % fcalls)
		print("  Iterations: %d" % iterations)
		print("  Current function value: %f" % fval)

	return x
