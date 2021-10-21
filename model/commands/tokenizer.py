import re
from enum import Enum

from Cat.Serializable import RegisterContainer, SerializableContainer, Serialized
from model.commands.argumentTypes import LiteralsArgumentType
from model.commands.command import Keyword, ArgumentInfo
from model.commands.commands import BASIC_COMMAND_INFO
from model.commands.parsedCommands import ParsedComment, ParsedCommand
from model.commands.parser import parseMCFunction
from model.parsingUtils import Position, Span


class TokenType(Enum):
	Default = 0
	Command = 1
	String = 2
	Number = 3
	Constant = 4
	TargetSelector = 5
	Operator = 6
	Keyword = 7

	Complex = 12
	Comment = 13
	Error = 14

	# KeyWord = 14
	# Variable = 11
	# BuiltinFunction = 17


@RegisterContainer
class Token1(SerializableContainer):
	__slots__ = ()
	text: str = Serialized(default='')
	start: int = Serialized(default=0)
	row: int = Serialized(default=0)
	column: int = Serialized(default=0)
	style: TokenType = Serialized(default=TokenType.Default)


def tokenizeMCFunction1(text: str, start: int, end: int) -> list[Token1]:
	# Initialize the styling
	# splitter = re.compile(r"(`[^`]*`|'[^']*'|\$[\w_]+|\d+\.\d+|[\w_]+|[\.\(,\)\{;\}\!]|&&|\|\||==|!=|->|\n)")
	splitter = re.compile(r'([\w]+|@\w|"[^"]*"|=|\+=|-=|\*=|/=|%=|><|<|>|\[|]|{|}|\.|:|/|#.*)')
	# Tokenize the text that needs to be styled using regular expressions.
	# To style a sequence of characters you need to know the length of the sequence
	# and which style you wish to apply to the sequence. It is up to the implementer
	# to figure out which style the sequence belongs to.
	# THE PROCEDURE SHOWN BELOW IS JUST ONE OF MANY!
	# Scintilla works with bytes, so we have to adjust the start and end boundaries.
	# Like all Qt objects the lexers parent is the QScintilla editor.
	findIter = splitter.finditer(text)
	tokens: list[Token1] = []
	lineNo: int = 0
	lineStartIndex: int = 0
	for i, match in enumerate(findIter):
		tokenText: str = match.group(0)
		tokenStart: int = match.start()
		token: Token1 = Token1.create(text=tokenText, start=tokenStart, row=lineNo, column=tokenStart - lineStartIndex)
		if tokenText.startswith('@'):
			token.style = TokenType.TargetSelector
		elif tokenText.startswith('"'):
			token.style = TokenType.String
		elif tokenText in {'true', 'false', 'null'}:
			token.style = TokenType.Constant
		elif tokenText in {'.', '(', ',', ')', '{', ';', '}', '[', ']', '=', '+=', '-=', '*=', '/=', '%=', '><', '<', '>', ':', '/'}:
			token.style = TokenType.Operator
		elif re.fullmatch(r'\d+(?:\.\d*)?', tokenText) is not None:
			token.style = TokenType.Number
		elif tokenText in BASIC_COMMAND_INFO:
			token.style = TokenType.Command
		elif tokenText.startswith('#'):
			token.style = TokenType.Comment
		elif tokenText == '\n':
			lineNo += 1
			lineStartIndex = tokenStart+1
			continue
		else:  # TokenType with the default style
			token.style = TokenType.Default
		tokens.append(token)

	return tokens


@RegisterContainer
class Token2(SerializableContainer):
	__slots__ = ()
	text: str = Serialized(default='')
	span: Span = Serialized(default_factory=Span)
	style: TokenType = Serialized(default=TokenType.Default)


def tokenizeMCFunction2(text: str, start: int, end: int) -> list[Token2]:

	function, errors = parseMCFunction(text)
	if function is None:
		return []

	tokens: list[Token2] = []
	for child in function.children:
		if child is None:
			continue
		elif isinstance(child, ParsedComment):
			token: Token2 = Token2.create(text=child.content, span=child.span, style=TokenType.Comment)
			tokens.append(token)
		else:
			tokens.extend(tokenizeCommand(child))

	return tokens

_allArgumentTypeStyles: dict[str, TokenType] = {
	'brigadier:bool': TokenType.Constant,
	'brigadier:double': TokenType.Number,
	'brigadier:float': TokenType.Number,
	'brigadier:integer': TokenType.Number,
	'brigadier:long': TokenType.Number,
	'brigadier:string': TokenType.String,
	'minecraft:angle': TokenType.Number,
	'minecraft:block_pos': TokenType.Number,
	'minecraft:block_predicate': TokenType.Complex,
	'minecraft:block_state': TokenType.Complex,
	'minecraft:color': TokenType.Constant,
	'minecraft:column_pos': TokenType.Number,
	'minecraft:component': TokenType.Complex,
	'minecraft:dimension': TokenType.String,
	'minecraft:entity': TokenType.TargetSelector,
	'minecraft:entity_anchor': TokenType.Constant,
	'minecraft:entity_summon': TokenType.String,
	'minecraft:float_range': TokenType.Number,
	'minecraft:function': TokenType.String,
	'minecraft:game_profile': TokenType.TargetSelector,
	'minecraft:int_range': TokenType.Number,
	'minecraft:item_enchantment': TokenType.String,
	'minecraft:item_predicate': TokenType.Complex,
	'minecraft:item_slot': TokenType.Constant,
	'minecraft:item_stack': TokenType.Complex,
	'minecraft:message': TokenType.String,
	'minecraft:mob_effect': TokenType.String,
	'minecraft:nbt_compound_tag': TokenType.Complex,
	'minecraft:nbt_path': TokenType.Complex,
	'minecraft:nbt_tag': TokenType.Complex,
	'minecraft:objective': TokenType.String,
	'minecraft:objective_criteria': TokenType.String,
	'minecraft:operation': TokenType.Operator,
	'minecraft:particle': TokenType.Complex,
	'minecraft:resource_location': TokenType.String,
	'minecraft:rotation': TokenType.Number,
	'minecraft:score_holder': TokenType.TargetSelector,
	'minecraft:scoreboard_slot': TokenType.Constant,
	'minecraft:swizzle': TokenType.Constant,
	'minecraft:team': TokenType.Constant,
	'minecraft:time': TokenType.Number,
	'minecraft:uuid': TokenType.String,
	'minecraft:vec2': TokenType.Number,
	'minecraft:vec3': TokenType.Number,
	'dpe:compare_operation': TokenType.Operator,
}


def tokenizeComment(comment: ParsedComment) -> list[Token2]:
	token: Token2 = Token2.create(text=comment.content, span=comment.span, style=TokenType.Comment)
	return [token]


def tokenizeCommand(command: ParsedCommand) -> list[Token2]:
	tokens: list[Token2] = []
	token: Token2 = Token2.create(text=command.name, span=command.span, style=TokenType.Command)
	tokens.append(token)

	argument = command
	while argument.next is not None:
		argument = argument.next

		if isinstance(argument, ParsedCommand):
			tokens += tokenizeCommand(argument)
			break

		token: Token2 = Token2.create(text=argument.content, span=argument.span)
		tokens.append(token)

		info = argument.info
		if isinstance(info, Keyword):
			token.style = TokenType.Keyword
		elif isinstance(info, ArgumentInfo):
			if isinstance(info.type, LiteralsArgumentType):
				token.style = TokenType.Constant
			else:
				typeName = info.typeName
				style = _allArgumentTypeStyles.get(typeName, TokenType.Error)
				token.style = style
	return tokens


Token = Token2
tokenizeMCFunction = tokenizeMCFunction2