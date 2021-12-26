import re
from enum import Enum

from Cat.Serializable import RegisterContainer, SerializableContainer, Serialized
from model.commands.argumentTypes import *
from model.commands.command import Keyword, ArgumentInfo
from model.commands.parsedCommands import ParsedComment, ParsedCommand
from model.commands.parser import parseMCFunction
from model.parsingUtils import Span
from session.session import getSession


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
		elif tokenText in getSession().minecraftData.commands:
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
	BRIGADIER_BOOL.name:               TokenType.Constant,
	BRIGADIER_DOUBLE.name:             TokenType.Number,
	BRIGADIER_FLOAT.name:              TokenType.Number,
	BRIGADIER_INTEGER.name:            TokenType.Number,
	BRIGADIER_LONG.name:               TokenType.Number,
	BRIGADIER_STRING.name:             TokenType.String,
	MINECRAFT_ANGLE.name:              TokenType.Number,
	MINECRAFT_BLOCK_POS.name:          TokenType.Number,
	MINECRAFT_BLOCK_PREDICATE.name:    TokenType.Complex,
	MINECRAFT_BLOCK_STATE.name:        TokenType.Complex,
	MINECRAFT_COLOR.name:              TokenType.Constant,
	MINECRAFT_COLUMN_POS.name:         TokenType.Number,
	MINECRAFT_COMPONENT.name:          TokenType.Complex,
	MINECRAFT_DIMENSION.name:          TokenType.String,
	MINECRAFT_ENTITY.name:             TokenType.TargetSelector,
	MINECRAFT_ENTITY_ANCHOR.name:      TokenType.Constant,
	MINECRAFT_ENTITY_SUMMON.name:      TokenType.String,
	MINECRAFT_FLOAT_RANGE.name:        TokenType.Number,
	MINECRAFT_FUNCTION.name:           TokenType.String,
	MINECRAFT_GAME_PROFILE.name:       TokenType.TargetSelector,
	MINECRAFT_INT_RANGE.name:          TokenType.Number,
	MINECRAFT_ITEM_ENCHANTMENT.name:   TokenType.String,
	MINECRAFT_ITEM_PREDICATE.name:     TokenType.Complex,
	MINECRAFT_ITEM_SLOT.name:          TokenType.Constant,
	MINECRAFT_ITEM_STACK.name:         TokenType.Complex,
	MINECRAFT_MESSAGE.name:            TokenType.String,
	MINECRAFT_MOB_EFFECT.name:         TokenType.String,
	MINECRAFT_NBT_COMPOUND_TAG.name:   TokenType.Complex,
	MINECRAFT_NBT_PATH.name:           TokenType.Complex,
	MINECRAFT_NBT_TAG.name:            TokenType.Complex,
	MINECRAFT_OBJECTIVE.name:          TokenType.String,
	MINECRAFT_OBJECTIVE_CRITERIA.name: TokenType.String,
	MINECRAFT_OPERATION.name:          TokenType.Operator,
	MINECRAFT_PARTICLE.name:           TokenType.Complex,
	MINECRAFT_RESOURCE_LOCATION.name:  TokenType.String,
	MINECRAFT_ROTATION.name:           TokenType.Number,
	MINECRAFT_SCORE_HOLDER.name:       TokenType.TargetSelector,
	MINECRAFT_SCOREBOARD_SLOT.name:    TokenType.Constant,
	MINECRAFT_SWIZZLE.name:            TokenType.Constant,
	MINECRAFT_TEAM.name:               TokenType.Constant,
	MINECRAFT_TIME.name:               TokenType.Number,
	MINECRAFT_UUID.name:               TokenType.String,
	MINECRAFT_VEC2.name:               TokenType.Number,
	MINECRAFT_VEC3.name:               TokenType.Number,
	DPE_COMPARE_OPERATION.name:        TokenType.Operator,
	DPE_BIOME_ID.name:                 TokenType.String,
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