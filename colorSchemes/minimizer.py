"""
Minimization of scalar function of one or more variables using the Nelder-Mead algorithm.
Used to calculate the optimal colors for the dark scheme.
"""
from __future__ import annotations

import operator
import sys
import warnings
from dataclasses import dataclass
from math import inf
from typing import Sequence, Iterator, overload, Callable

inf = inf


@dataclass
class Array:
	_vals: list[float]

	@overload
	def __getitem__(self, index: int) -> float: ...
	@overload
	def __getitem__(self, index: slice) -> Array: ...

	def __getitem__(self, index: int | slice) -> float | Array:
		if isinstance(index, slice):
			return Array(self._vals[index])
		else:
			return self._vals[index]

	def __setitem__(self, index: int, val: float) -> None:
		self._vals[index] = val

	def __len__(self) -> int:
		return len(self._vals)

	def index(self, value: float, start: int = 0, stop: int = sys.maxsize) -> int:
		return self._vals.index(value, start, stop)

	def count(self, value: float) -> int:
		return self._vals.count(value)

	def __contains__(self, value: object) -> bool:
		return self._vals.__contains__(value)

	def __iter__(self) -> Iterator[float]:
		return self._vals.__iter__()

	def __reversed__(self) -> Iterator[float]:
		return self._vals.__reversed__()

	def _apply2(self, other: float | Array, func: Callable[[float, float], float]) -> Array:
		if isinstance(other, Array):
			assert len(other) == len(self)
			vals = _applyaa(self._vals, other._vals, func)
		elif isinstance(other, (float, int)):
			vals = _applyaf(self._vals, other, func)
		else:
			raise NotImplemented(f" cannot handle type '{type(other)}' of value '{other}'.")
		return Array(vals)

	def __add__(self, other: float | Array) -> Array:
		return self._apply2(other, operator.add)

	def __radd__(self, other: float | Array) -> Array:
		return self._apply2(other, operator.add)

	def __sub__(self, other: float | Array) -> Array:
		return self._apply2(other, operator.sub)

	def __rsub__(self, other: float | Array) -> Array:
		return self._apply2(other, lambda a, b: b - a)

	def __mul__(self, other: float | Array) -> Array:
		return self._apply2(other, operator.mul)

	def __rmul__(self, other: float | Array) -> Array:
		return self._apply2(other, operator.mul)

	def __truediv__(self, other: float | Array) -> Array:
		return self._apply2(other, operator.truediv)


@dataclass
class Matrix:
	_vals: list[list[float]]
	_shape: tuple[int, int]

	@overload
	def __getitem__(self, index: int) -> Array: ...
	@overload
	def __getitem__(self, index: slice) -> Matrix: ...

	def __getitem__(self, index: int | slice) -> Array | Matrix:
		if isinstance(index, slice):
			vals = self._vals[index]
			return Matrix(vals, (len(vals), self._shape[1]))
		else:
			return Array(self._vals[index])

	def __setitem__(self, index: int, val: Sequence[float]) -> None:
		assert len(val) == self._shape[1]
		self._vals[index] = list(val)

	def _apply2(self, other: float | Array | Matrix, func: Callable[[float, float], float]) -> Matrix:
		if isinstance(other, Matrix):
			assert other._shape == self._shape
			vals = _applymm(self._vals, other._vals, func)
		elif isinstance(other, Array):
			assert len(other) == self._shape[1]
			vals = _applyma(self._vals,         other._vals, func)
		elif isinstance(other, (float, int)):
			vals = _applymf(self._vals, other, func)
		else:
			raise NotImplemented(f" cannot handle type '{type(other)}' of value '{other}'.")
		return Matrix(vals, self._shape)

	def __add__(self, other: float | Array | Matrix) -> Matrix:
		return self._apply2(other, operator.add)

	def __radd__(self, other: float | Array | Matrix) -> Matrix:
		return self._apply2(other, operator.add)

	def __sub__(self, other: float | Array | Matrix) -> Matrix:
		return self._apply2(other, operator.sub)

	def __rsub__(self, other: float | Array | Matrix) -> Matrix:
		return self._apply2(other, lambda a, b: b - a)

	def __mul__(self, other: float | Array | Matrix) -> Matrix:
		return self._apply2(other, operator.mul)

	def __rmul__(self, other: float | Array | Matrix) -> Matrix:
		return self._apply2(other, operator.mul)

	def __truediv__(self, other: float | Array | Matrix) -> Matrix:
		return self._apply2(other, operator.truediv)


def emptym(shape: tuple[int, int]) -> Matrix:
	vals = [
		[0.0] * shape[1] for _ in range(shape[0])
	]
	return Matrix(vals, shape)


def fulla(shape: tuple[int], val: float) -> Array:
	vals = [val] * shape[0]
	return Array(vals)


def array(*args: float) -> Array:
	return Array(list(args))


def _applyaf[T1, T2, R](input: list[T1], b: T2, func: Callable[[T1, T2], R]) -> list[R]:
	return [func(inp, b) for inp in input]


def _applyaa[T1, T2, R](input: list[T1], bs: list[T2], func: Callable[[T1, T2], R]) -> list[R]:
	return [func(inp, b) for inp, b in zip(input, bs)]


def _applymf[T1, T2, R](input: list[list[T1]], b: T2, func: Callable[[T1, T2], R]) -> list[list[R]]:
	return [_applyaf(inp, b, func) for inp in input]


def _applyma[T1, T2, R](input: list[list[T1]], bs: list[T2], func: Callable[[T1, T2], R]) -> list[list[R]]:
	return [_applyaa(inp, bs, func) for inp in input]


def _applymm[T1, T2, R](input: list[list[T1]], bs: list[list[T2]], func: Callable[[T1, T2], R]) -> list[list[R]]:
	return [_applyaa(inp, b, func) for inp, b in zip(input, bs)]


def _clip(input: list[float], a_min: float, a_max: float) -> list[float]:
	return [min(a_max, max(a_min, inp)) for inp in input]


def clipa(input: Array, a_min: float, a_max: float) -> Array:
	return Array(_clip(input._vals, a_min, a_max))


def clipm(input: Matrix, a_min: float, a_max: float) -> Matrix:
	return Matrix([_clip(inp, a_min, a_max)for inp in input._vals], input._shape)


def mina(input: Array) -> float:
	return min(input._vals)


def maxa(input: Array) -> float:
	return max(input._vals)


def maxm(input: Matrix) -> float:
	return max(max(inp) for inp in input._vals)


def _abs(input: list[float]) -> list[float]:
	return [abs(inp) for inp in input]


def absa(input: Array) -> Array:
	return Array(_abs(input._vals))


def absm(input: Matrix) -> Matrix:
	return Matrix([_abs(inp) for inp in input._vals], input._shape)


def _argsort(input: list[float]) -> list[int]:
	# http://stackoverflow.com/questions/3071415/efficient-method-to-calculate-the-rank-vector-of-a-list-in-python
	return sorted(range(len(input)), key=input.__getitem__)


def argsorta(input: Array) -> list[int]:
	return _argsort(input._vals)


def _take[_T](input: list[_T], indices: list[int]) -> list[_T]:
	return [input[i] for i in indices]


def takea(input: Array, indices: list[int]) -> Array:
	return Array(_take(input._vals, indices))


def takem(input: Matrix, indices: list[int]) -> Matrix:
	return Matrix(_take(input._vals, indices), input._shape)


def reducem(input: Matrix, func: Callable[[Array, Array], Array]) -> Array:
	result = input[0]
	for inp in input[1:]:
		result = func(result, inp)
	return result



class _MaxFuncCallError(RuntimeError):
	pass


def minimize(fun: Callable[[Array], float], x0: Array, *, disp: bool = False, bounds: tuple[float, float] | None = None) -> Array:
	return _minimize_neldermead(fun, x0, disp=disp, bounds=bounds)


def _minimize_neldermead(function: Callable[[Array], float], x0: Array, *, disp: bool, xatol: float = 1e-8, fatol: float = 1e-4, bounds: tuple[float, float] | None = None) -> Array:
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
		x0 = clipa(x0, bounds[0], bounds[1])

	N = len(x0)
	sim: Matrix = emptym((N + 1, N))
	sim[0] = x0
	for k in range(N):
		y = array(*x0)
		if y[k] != 0:
			y[k] = (1 + nonzdelt)*y[k]
		else:
			y[k] = zdelt
		sim[k + 1] = y

	# If neither are set, then set both to default
	maxiter = N * 200
	maxfun = N * 200

	if bounds is not None:
		sim = clipm(sim, bounds[0], bounds[1])

	one2np1 = list(range(1, N + 1))
	fsim: Array = fulla((N + 1,), inf)

	fcalls = 0

	def func(x: Array) -> float:
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
		ind = argsorta(fsim)
		sim = takem(sim, ind)
		fsim = takea(fsim, ind)

	ind = argsorta(fsim)
	fsim = takea(fsim, ind)
	# sort so sim[0,:] has the lowest function value
	sim = takem(sim, ind)

	iterations = 1

	while fcalls < maxfun and iterations < maxiter:
		try:
			if (maxm(absm(sim[1:] - sim[0])) <= xatol and
					maxa(absa(fsim[0] - fsim[1:])) <= fatol):
				break

			xbar = reducem(sim[:-1], operator.add) / N
			xr = 2 * xbar - sim[-1]
			if bounds is not None:
				xr = clipa(xr, bounds[0], bounds[1])

			fxr = func(xr)
			doshrink = 0

			if fxr < fsim[0]:
				xe = 3 * xbar - 2 * sim[-1]
				if bounds is not None:
					xe = clipa(xe, bounds[0], bounds[1])
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
							xc = clipa(xc, bounds[0], bounds[1])
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
							xcc = clipa(xcc, bounds[0], bounds[1])
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
								sim[j] = clipa(sim[j], bounds[0], bounds[1])
							fsim[j] = func(sim[j])
			iterations += 1
		except _MaxFuncCallError:
			pass
		finally:
			ind = argsorta(fsim)
			sim = takem(sim, ind)
			fsim = takea(fsim, ind)

	x = sim[0]
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
		fval = mina(fsim)
		print("  Function evaluations: %d" % fcalls)
		print("  Iterations: %d" % iterations)
		print("  Current function value: %f" % fval)

	return x
