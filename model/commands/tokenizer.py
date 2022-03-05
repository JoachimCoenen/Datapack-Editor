from dataclasses import dataclass
from enum import Enum

from model.commands.argumentTypes import *
from model.commands.command import KeywordSchema, ArgumentSchema
from model.commands.command import ParsedComment, ParsedCommand, MCFunction
from model.utils import Span


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


@dataclass
class Token:
	text: str
	span: Span
	style: TokenType


def tokenizeMCFunction(function: MCFunction) -> list[Token]:
	tokens: list[Token] = []
	for child in function.children:
		if child is None:
			continue
		elif isinstance(child, ParsedComment):
			tokens.extend(tokenizeComment(child))
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
	MINECRAFT_PREDICATE.name:          TokenType.String,
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


def tokenizeComment(comment: ParsedComment) -> list[Token]:
	token: Token = Token(comment.content, comment.span, TokenType.Comment)
	return [token]


def tokenizeCommand(command: ParsedCommand) -> list[Token]:
	tokens: list[Token] = []

	argument = command
	while argument is not None:
		if isinstance(argument, ParsedCommand):
			style = TokenType.Command
			text = argument.name
		else:
			text = argument.content
			schema = argument.schema
			if isinstance(schema, KeywordSchema):
				style = TokenType.Keyword
			elif isinstance(schema, ArgumentSchema):
				if isinstance(schema.type, LiteralsArgumentType):
					style = TokenType.Constant
				else:
					typeName = schema.typeName
					style = _allArgumentTypeStyles.get(typeName, TokenType.Error)
			else:
				style = TokenType.Error
		token: Token = Token(text, argument.span, style)
		tokens.append(token)
		argument = argument.next
	return tokens
