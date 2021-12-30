"""Lexer functions, based on www.github.com/tusharsadhwani/json_parser"""
from collections import deque
from enum import Enum
from typing import Deque, NamedTuple, Tuple
from string import whitespace as WHITESPACE

from model.utils import Span, GeneralParsingError, Position


class TokenType(Enum):
	invalid = 0
	string = 1
	number = 2
	boolean = 3
	null = 4
	left_bracket = 5
	left_brace = 6
	right_bracket = 7
	right_brace = 8
	comma = 9
	colon = 10


class Token(NamedTuple):
	"""Represents a Token extracted by the parser"""
	value: str
	type: TokenType
	span: Span


class TokenizeErrorData(GeneralParsingError):
	pass


class TokenizeError(Exception):
	"""Error thrown when an invalid JSON string is tokenized"""
	def __init__(self, data: TokenizeErrorData):
		super(TokenizeError, self).__init__(str(data))
		self.data: TokenizeErrorData = data


def extract_string(
		json_string: str,
		index: int,
		tokens: Deque[Token],
		line: int,
		column: int) -> Tuple[int, int, int]:
	"""Extracts a single string token from JSON string"""
	end = len(json_string)
	start = Position(line, column, index)
	index += 1
	column += 1

	while index < end:
		char = json_string[index]

		if char == '\\':
			if index + 1 == end:
				end = Position(line, column, index)
				raise TokenizeError(TokenizeErrorData("Incomplete escape at end of string", Span(start, end)))

			index += 2
			column += 2
			continue

		if char == '"':
			index += 1
			column += 1
			end = Position(line, column, index)
			string = json_string[start.index:end.index]
			tokens.append(Token(string, TokenType.string, Span(start, end)))

			return index, line, column

		index += 1
		if char == '\n':
			column = 0
			line += 1
		else:
			column += 1

	end = Position(line, column, index)
	err = f"Expected end of string"
	raise TokenizeError(TokenizeErrorData(err, Span(start, end)))


def extract_number(
		json_string: str,
		index: int,
		tokens: Deque[Token],
		line: int,
		column: int) -> Tuple[int, int, int]:
	"""Extracts a single number token (eg. 42, -12.3) from JSON string"""
	end = len(json_string)
	start = Position(line, column, index)

	leading_minus_found = False
	decimal_point_found = False

	while index < end:
		char = json_string[index]
		if char == '.':
			if decimal_point_found:
				end = Position(line, column, index)
				raise TokenizeError(TokenizeErrorData("Too many decimal points in number", Span(start, end)))

			decimal_point_found = True

		elif char == '-':
			if leading_minus_found:
				end = Position(line, column, index)
				raise TokenizeError(TokenizeErrorData("Minus sign in between number", Span(start, end)))

			leading_minus_found = True

		elif not char.isdigit():
			break

		index += 1

	end = Position(line, column, index)
	number = json_string[start.index:end.index]
	tokens.append(Token(number, TokenType.number, Span(start, end)))
	length = index - start.index
	column += length
	return index, line, column


def extract_special(
		json_string: str,
		index: int,
		tokens: Deque[Token],
		line: int,
		column: int) -> Tuple[int, int, int]:
	"""Extracts true, false and null from JSON string"""
	end = len(json_string)
	start = Position(line, column, index)

	word = ''
	while index < end:
		char = json_string[index]
		if not char.isalpha():
			break

		word += char
		index += 1

	if word in ('true', 'false', 'null'):
		end = Position(line, column, index)
		token = Token(
			word,
			type=TokenType.null if word == 'null' else TokenType.boolean,
			span=Span(start, end)
		)
		tokens.append(token)
		column += len(word)
		return index, line, column

	err = f"Unknown token found: {word}"
	end = Position(line, column, index)
	raise TokenizeError(TokenizeErrorData(err, Span(start, end)))


_TOKEN_TYPE_FOR_OPERATOR = {
	'[': TokenType.left_bracket,
	']': TokenType.right_bracket,
	'{': TokenType.left_brace,
	'}': TokenType.right_brace,
	',': TokenType.comma,
	':': TokenType.colon,
}


def tokenize(json_string: str) -> Deque[Token]:
	"""Converts a JSON string into a queue of tokens"""
	tokens: Deque[Token] = deque()
	line = 0
	column = 0
	index = 0
	end = len(json_string)
	while index < end:
		char = json_string[index]

		if char in WHITESPACE:
			index += 1

			if char == '\n':
				column = 0
				line += 1
			else:
				column += 1

		elif char in '[]{},:':
			span = Span(Position(line, column, index), Position(line, column + 1, index + 1))
			token = Token(
				char,
				type=_TOKEN_TYPE_FOR_OPERATOR[char],
				span=span,
			)
			tokens.append(token)
			index += 1
			column += 1

		elif char == '"':
			index, line, column = extract_string(
				json_string, index, tokens, line, column)

		elif char == '-' or char.isdigit():
			index, line, column = extract_number(
				json_string, index, tokens, line, column)

		else:
			index, line, column = extract_special(
				json_string, index, tokens, line, column)

	if len(tokens) == 0:
		raise TokenizeError(TokenizeErrorData("Cannot parse empty string", Span()))

	return tokens
