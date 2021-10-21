from Cat.Serializable import RegisterContainer, SerializableContainer, ComputedCached


@RegisterContainer
class Message(SerializableContainer):
	__slots__ = ()
	rawMessage: str = ComputedCached(default='', shouldSerialize=True, shouldPrint=True)
	argsCount: int = ComputedCached(default=-1, shouldSerialize=True, shouldPrint=True)

	def __init__(self, message: str, argsCount: int):
		super(Message, self).__init__()
		self.rawMessageProp.setCachedValue(self, message)
		self.argsCountProp.setCachedValue(self, argsCount)

	def format(self, *args) -> str:
		if len(args) > self.argsCount:
			raise ValueError(f"too many arguments supplied. expected {self.argsCount}, but got {len(args)}")
		elif len(args) < self.argsCount:
			raise ValueError(f"too few arguments supplied. expected {self.argsCount}, but got {len(args)}")

		return self.rawMessage.format(*args)