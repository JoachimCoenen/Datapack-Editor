import json
import re
from collections import OrderedDict
from functools import partial
from typing import Any, Optional, Union, Type, Callable

from cat.utils.collections_ import AddToDictDecorator
from .core import *


class ComplexEncoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, JsonNode):
			nh = _nodeHandlers[obj.typeName]
			return nh(self, obj)
		return super(ComplexEncoder, self).default(obj)


def emitJson(
		data: JsonData,
		*,
		skipkeys: bool = False,
		ensure_ascii: bool = True,
		check_circular: bool = True,
		allow_nan: bool = True,
		cls: Type[ComplexEncoder] = ComplexEncoder,
		indent: Union[None, int, str] = None,
		separators: Optional[tuple[str, str]] = None,
		default: Optional[Callable[[Any], Any]] = None,
		sort_keys: bool = False,
		collapseSingleElementArray: bool = True,
		collapseSinglePropObject: bool = True,
) -> str:
	text = json.dumps(
		data,
		skipkeys=skipkeys,
		ensure_ascii=ensure_ascii,
		check_circular=check_circular,
		allow_nan=allow_nan,
		cls=cls,
		indent=indent,
		separators=separators,
		default=default,
		sort_keys=sort_keys,
	)
	# beautify json file:
	if collapseSingleElementArray:
		text = collapseSingleLineArray(text)
	if collapseSinglePropObject:
		text = collapseSingleLineObject(text)
	if collapseSingleElementArray:
		text = collapseSingleLineArray(text)
	if collapseSinglePropObject:
		text = collapseSingleLineObject(text)
	return text


SINGLE_LINE_ARRAY_REGEX = re.compile(r'(?:\[(?:[^\n[\]]*|\s+)\])').pattern
SINGLE_LINE_OBJECT_REGEX = re.compile(r'(?:\{(?:[^\n{}]*|\s+)\})').pattern
SIMPLE_VAL_REGEX = re.compile(rf'(?:"[^"\n]*"|[\d.+-]+|null|true|false|{SINGLE_LINE_ARRAY_REGEX}|{SINGLE_LINE_OBJECT_REGEX})').pattern

COLLAPSE_SINGLE_LINE_ARRAY = re.compile(rf'\[\s*({SIMPLE_VAL_REGEX})\s*\]')
collapseSingleLineArray = partial(COLLAPSE_SINGLE_LINE_ARRAY.sub, r'[ \1 ]')
COLLAPSE_SINGLE_LINE_OBJECT = re.compile(rf'\{{\s*("[^"\n]*"\s*:\s*{SIMPLE_VAL_REGEX})\s*\}}')
collapseSingleLineObject = partial(COLLAPSE_SINGLE_LINE_OBJECT.sub, r'{ \1 }')

_nodeHandlers: dict[str, Callable[[ComplexEncoder, JsonData], str]] = {}

nodeHandler = AddToDictDecorator(_nodeHandlers)


@nodeHandler('property')
def propertyHandler(self: ComplexEncoder, node: JsonProperty) -> JsonData:  # tuple[str, JsonData]:
	return node.value


@nodeHandler('object')
def objectHandler(self: ComplexEncoder, node: JsonObject) -> OrderedDict[str, JsonData]:
	return OrderedDict(node.data.items())


@nodeHandler('array')
@nodeHandler('string')
@nodeHandler('boolean')
@nodeHandler('number')
@nodeHandler('null')
def arrayHandler(self: ComplexEncoder, node: JsonArray) -> list[JsonData]:
	return node.data