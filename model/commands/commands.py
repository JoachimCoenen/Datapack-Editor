from typing import Optional

from Cat.Serializable import SerializableContainer, Serialized
from model.commands.command import CommandInfo
from model.data.v1_17.commands import BASIC_COMMAND_INFO  # temporarily


class AllCommands(SerializableContainer):
	BASIC_COMMAND_INFO: dict[str, CommandInfo] = Serialized(default_factory=dict)


def getCommandInfo(name: str) -> Optional[CommandInfo]:
	return BASIC_COMMAND_INFO.get(name, None)

