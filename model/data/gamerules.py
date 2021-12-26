from Cat.Serializable import RegisterContainer, SerializableContainer, Serialized
from model.commands.argumentTypes import BRIGADIER_BOOL, ArgumentType, BRIGADIER_INTEGER


@RegisterContainer
class Gamerule(SerializableContainer):
	__slots__ = ()
	name: str = Serialized(default='')
	description: str = Serialized(default='')
	type: ArgumentType = Serialized(default=BRIGADIER_BOOL)
	defaultValue: str = Serialized(default='')



