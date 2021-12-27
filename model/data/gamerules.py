from dataclasses import dataclass
from model.commands.argumentTypes import ArgumentType


@dataclass
class Gamerule:
	name: str
	description: str
	type: ArgumentType
	defaultValue: str



