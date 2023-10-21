from __future__ import annotations

from dataclasses import dataclass
from cat.utils.collections_ import OrderedDict, AddToDictDecorator
from base.model.parsing.bytesUtils import bytesToStr


@dataclass(unsafe_hash=True)  # unsafe_hash=True is required, because in py3.11 the module dataclasses uses the existence of __hash__() to detect mutable default values :(
class ArgumentType:
	def __post_init__(self):
		if type(self) is ArgumentType:
			registerNamedArgumentType(self)

	name: str
	description: str = ''
	description2: str = ''
	example: str = ''
	examples: str = ''
	jsonProperties: str = ''


ALL_NAMED_ARGUMENT_TYPES: OrderedDict[str, ArgumentType] = OrderedDict()
_registerNamedArgumentType: AddToDictDecorator[str, ArgumentType] = AddToDictDecorator(ALL_NAMED_ARGUMENT_TYPES)


def registerNamedArgumentType(argumentType: ArgumentType, forceOverride: bool = False) -> None:
	_registerNamedArgumentType(argumentType.name, forceOverride)(argumentType)


@dataclass
class LiteralsArgumentType(ArgumentType):
	def __post_init__(self):
		if not self.options:
			raise ValueError("options must be set for a LiteralsArgumentType.")
		assert all(isinstance(o, bytes) for o in self.options)

	options: list[bytes] = None


def makeLiteralsArgumentType(options: list[bytes], description: str = '', description2: str = '', example: str = '', examples: str = '', jsonProperties: str = '') -> LiteralsArgumentType:
	name = f"({bytesToStr(b'|'.join(options))})"
	return LiteralsArgumentType(name, description, description2, example, examples, jsonProperties, options)


BRIGADIER_BOOL = ArgumentType(
	name='brigadier:bool',
	description="Must be a boolean (either true or false).",
	description2="""""",
	examples="""
	* {{cd|true}}
	* {{cd|false}}""",
)

BRIGADIER_DOUBLE = ArgumentType(
	name='brigadier:double',
	description="{{Arg desc|je=double}}",
	description2="""
	Each double argument may have a custom minimum and maximum value.
	Precision varies throughout number line; the maximum absolute value is about 1.8*10<sup>308</sup>.""",
	examples="""
	* {{cd|0}}
	* {{cd|1.2}}
	* {{cd|.5}}
	* {{cd|-1}}
	* {{cd|-.5}}
	* {{cd|-1234.56}}""",
	jsonProperties="""
	* {{nbt|compound|properties}}: The root properties object.
	** {{nbt|double|max}}: The maximum value of this double argument.
	** {{nbt|double|min}}: The minimum value of this double argument.""",
)

BRIGADIER_FLOAT = ArgumentType(
	name='brigadier:float',
	description="{{Arg desc|je=float}}",
	description2="""
	Each float argument type may have a custom minimum and maximum value.
	Precision varies throughout number line; the maximum absolute value is about 3.4*10<sup>38</sup>.""",
	examples="""
	* {{cd|0}}
	* {{cd|1.2}}
	* {{cd|.5}}
	* {{cd|-1}}
	* {{cd|-.5}}
	* {{cd|-1234.56}}""",
	jsonProperties="""
	* {{nbt|compound|properties}}: The root properties object.
	** {{nbt|float|max}}: The maximum value of this float argument.
	** {{nbt|float|min}}: The minimum value of this float argument.""",
)

BRIGADIER_INTEGER = ArgumentType(
	name='brigadier:integer',
	description="{{Arg desc|je=integer}}",
	description2="""
	Each integer argument type may have a custom minimum and maximum value.
	Maximum range is from −(2<sup>31</sup>) to (2<sup>31</sup> − 1), or from (−2,147,483,648) to (2,147,483,647).""",
	examples="""
	* {{cd|0}}
	* {{cd|123}}
	* {{cd|-123}}""",
	jsonProperties="""
	* {{nbt|compound|properties}}: The root properties object.
	** {{nbt|int|max}}: The maximum value of this integer argument.
	** {{nbt|int|min}}: The minimum value of this integer argument.""",
)

BRIGADIER_LONG = ArgumentType(
	name='brigadier:long',
	description="{{Arg desc|je=long}}",
	description2="""
	Note: Although a long argument type is present in [[brigadier]], it is not used by ''Minecraft''.
	Each long argument type may have a custom minimum and maximum value.
	Maximum range is from &minus;(2<sup>63</sup>) to (2<sup>63</sup>&minus;1), or from (&minus;9,223,372,036,854,775,808) to (9,223,372,036,854,775,807).""",
	examples="""
	* {{cd|0}}
	* {{cd|123}}
	* {{cd|-123}}""",
	jsonProperties="""
	* {{nbt|compound|properties}}: The root properties object.
	** {{nbt|long|max}}: The maximum value of this long argument.
	** {{nbt|long|min}}: The minimum value of this long argument.""",
)

BRIGADIER_STRING = ArgumentType(
	name='brigadier:string',
	description="{{Arg desc|je=string}}",
	description2="""Each string argument type can accept either a single word (no spaces), a quotable phrase (either single word or quoted string), or a greedy phrase (taking the rest of the command as the string argument).""",
	examples="""
	Single word
	* {{cd|word}}
	* {{cd|word_with_underscores}}
	Quotable phrase
	* {{cd|"quoted phrase"}}
	* {{cd|word}}
	* {{cd|""}}
	Greedy phrase
	* {{cd|word}}
	* {{cd|words with spaces}}
	* {{cd|"and symbols"}}""",
	jsonProperties="""
	* {{nbt|compound|properties}}: The root properties object.
	** {{nbt|string|type}}: The type of this string argument. Can be {{cd|word}}, {{cd|phrase}}, or {{cd|greedy}}""",
)

__all__ = [
	'ArgumentType',
	'ALL_NAMED_ARGUMENT_TYPES',
	'LiteralsArgumentType',
	'makeLiteralsArgumentType',

	'BRIGADIER_BOOL',
	'BRIGADIER_DOUBLE',
	'BRIGADIER_FLOAT',
	'BRIGADIER_INTEGER',
	'BRIGADIER_LONG',
	'BRIGADIER_STRING',
]