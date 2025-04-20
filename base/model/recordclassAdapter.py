import dataclasses
import inspect
from typing import dataclass_transform, Callable, overload, Any

from recordclass import adapter  # type: ignore


@dataclass_transform(eq_default=True, order_default=True, kw_only_default=False, frozen_default=False)
def _as_dataclass[T](
		cls: type[T],
		*,
		use_dict: bool,
		use_weakref: bool,
		hashable: bool,
		sequence: bool,
		mapping: bool,
		iterable: bool,
		readonly: bool,
		module: str | None,
		fast_new: bool,
		rename: bool,
		gc: bool
) -> type[T]:
	annotations = inspect.get_annotations(cls)
	default_values = {
		name: getattr(cls, name, _SENTINEL) 
		for name in annotations.keys()
	}
	
	dataclass = adapter.as_dataclass(
		use_dict=use_dict,
		use_weakref=use_weakref,
		hashable=hashable,
		sequence=sequence,
		mapping=mapping,
		iterable=iterable,
		readonly=readonly,
		module=module,
		fast_new=fast_new,
		rename=rename,
		gc=gc,
	)(cls)
	
	fields = {
		name: _make_field(name=name, type_=annotations.get(name), default=default_values[name])  # type: ignore
		for name in dataclass.__fields__
	}
	
	setattr(dataclass, dataclasses._FIELDS, fields)  # type: ignore
	
	return dataclass


_SENTINEL = object()


def _make_field(name: str, type_: type, default: Any = _SENTINEL) -> dataclasses.Field:
	if default is _SENTINEL:
		field = dataclasses.field()
	else:
		field = dataclasses.field(default=default)
	field.name = name
	field.type = type_
	return field



@overload
@dataclass_transform(eq_default=True, order_default=True, kw_only_default=False, frozen_default=False)
def as_dataclass[T](
		*,
		use_dict: bool = False,
		use_weakref: bool = False,
		hashable: bool = False,
		sequence: bool = False,
		mapping: bool = False,
		iterable: bool = False,
		frozen: bool = False,
		fast_new: bool = True,
		gc: bool = False
) -> Callable[[type[T]], type[T]]:
	...


@overload
@dataclass_transform(eq_default=True, order_default=True, kw_only_default=False, frozen_default=False)
def as_dataclass[T](
		cls: type[T],
		/, *,
		use_dict: bool = False,
		use_weakref: bool = False,
		hashable: bool = False,
		sequence: bool = False,
		mapping: bool = False,
		iterable: bool = False,
		frozen: bool = False,
		fast_new: bool = True,
		gc: bool = False
) -> type[T]:
	...


@dataclass_transform(eq_default=True, order_default=True, kw_only_default=False, frozen_default=False)
def as_dataclass[T](
		cls: type[T] | None = None,
		/, *,
		use_dict: bool = False,
		use_weakref: bool = False,
		hashable: bool = False,
		sequence: bool = False,
		mapping: bool = False,
		iterable: bool = False,
		frozen: bool = False,
		fast_new: bool = True,
		gc: bool = False
) -> Callable[[type[T]], type[T]] | type[T]:
	def func(cls2: type[T]) -> type[T]:
		return _as_dataclass(
			cls2,
			use_dict=use_dict,
			use_weakref=use_weakref,
			hashable=hashable,
			sequence=sequence,
			mapping=mapping,
			iterable=iterable,
			readonly=frozen,
			module=None,
			fast_new=fast_new,
			rename=False,
			gc=gc,
		)
	if cls is None:
		return func
	else:
		return func(cls)


__all__ = [
	'as_dataclass'
]
