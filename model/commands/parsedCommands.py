from __future__ import annotations
from typing import Optional, Union, Any

from Cat.Serializable import RegisterContainer, SerializableContainer, Serialized, Computed, ComputedCached
from Cat.utils import Maybe
from model.commands.command import CommandInfo, CommandNode
from model.parsingUtils import Position, Span


@RegisterContainer
class ParsedNode(SerializableContainer):
	__slots__ = ()
	source: str = Serialized(default='', shouldSerialize=True, shouldPrint=False)

	span: Span = Serialized(default_factory=Span)

	start: Position = Computed(getInitValue=span.start)
	end: Position = Computed(getInitValue=span.end)

	content: str = ComputedCached(getInitValue=lambda s: s.source[s.span.slice], shouldPrint=True)


@RegisterContainer
class ParsedComment(ParsedNode):
	__slots__ = ()
	pass


@RegisterContainer
class ParsedCommandPart(ParsedNode):
	__slots__ = ()
	info: Optional[CommandNode] = Serialized(default=None, customPrintFunc=lambda s, x: Maybe(x).getattr('name').get())
	value: Any = Serialized(default='')
	next: Optional[ParsedCommandPart] = Serialized(default=None)
	prev: Optional[ParsedCommandPart] = ComputedCached(default=None, shouldSerialize=True, shouldPrint=False)

	def _nextOnSet(self, newVal: Optional[ParsedCommandPart], oldVal: Optional[ParsedCommandPart]) -> Optional[ParsedCommandPart]:
		if oldVal is not None:
			oldVal.prevProp.setCachedValue(oldVal, None)
		if newVal is not None:
			newVal.prevProp.setCachedValue(newVal, self)
		return newVal
	next.onSet(_nextOnSet)


@RegisterContainer
class ParsedCommand(ParsedCommandPart):
	__slots__ = ()
	info: Optional[CommandInfo] = Serialized(default=None, customPrintFunc=lambda s, x: Maybe(x).getattr('command').get())
	name: str = Serialized(default='')
	value: str = Computed(getInitValue=name)
	argument: Optional[ParsedArgument] = Serialized(default=None)
	argument.onSet(ParsedCommandPart._nextOnSet)
	next: Optional[ParsedCommandPart] = Computed(getInitValue=argument)


@RegisterContainer
class ParsedArgument(ParsedCommandPart):
	__slots__ = ()


@RegisterContainer
class ParsedMCFunction(SerializableContainer):
	__slots__ = ()
	children: list[Union[ParsedCommand, ParsedComment]] = Serialized(default_factory=list[Union[ParsedCommand, ParsedComment]])
	commands: list[ParsedCommand] = ComputedCached(getInitValue=children.map(lambda x: [c for c in x if isinstance(c, ParsedCommand)], list[ParsedCommand]))
	comments: list[ParsedComment] = ComputedCached(getInitValue=children.map(lambda x: [c for c in x if isinstance(c, ParsedComment)], list[ParsedComment]))

	# see: `FunctionMeta.documentation`
	# @ComputedCached()
	# def documentation(self) -> HTMLStr:
	# 	"""
	# 	TODO: add documentationfor Formatting of MCFunction Documentation
	# 	Special parameters:
	# 		Desc: a short version of the description
	# 		Called by: followed by a comma-separated list of function, other functions that call this function
	# 	:return:
	# 	"""
	# 	allFirstComments = []
	# 	lastLine: Optional[int] = None
	# 	for child in self.children:
	# 		if lastLine is not None and child.span.start.line > lastLine + 1:
	# 			break
	# 		lastLine = child.span.end.line
	#
	# 		if isinstance(child, ParsedComment):
	# 			allFirstComments.append(child)
	# 		else:
	# 			break
	#
	# 	if not allFirstComments:
	# 		return HTMLStr('')
	#
	# 	lines: list[str] = []
	# 	whiteSpaces = 999  # wayyyyy to many
	# 	for comment in allFirstComments:
	# 		# remove '#':
	# 		text = comment.content[1:]
	# 		# remove leading whiteSpaces:
	# 		text2 = text.lstrip()
	# 		if text2:
	# 			whiteSpaces = min(whiteSpaces, len(text) - len(text2))
	# 			text2 = text[whiteSpaces:]
	# 		lines.append(text2)
	#
	# 	finalText = ''
	# 	for line in lines:
	# 		if line.startswith('Desc:'):
	# 			line = '<p><b>Description:</b>' + line[len('Desc:'):] + '</p>'
	# 		elif line.startswith('Called by:'):
	# 			line2 = line[len('Called by:'):]
	# 			functions = line2.split(',')
	#
	# 			line = '<p><b>Called by:</b><ul>'
	# 			for f in functions:
	# 				f = f.strip()
	# 				f = unescapeFromXml(f)
	# 				f = escapeForXmlAttribute(f)
	# 				line += f'\n\t<li><a href="@dpe.function:{f}">`{f}`</a></li>'
	# 			line += '\n</ul></p>'
	# 		finalText += f'\n{line}'
	#
	# 	return HTMLifyMarkDownSubSet(finalText)



