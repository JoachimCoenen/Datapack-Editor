from abc import abstractmethod, ABC
from dataclasses import replace, dataclass
from typing import Optional, Iterable, Any

from PyQt5.QtWidgets import QWidget

from Cat.utils.logging_ import logError
from model.commands.stringReader import StringReader
from model.data.json.argTypes import *
from model.data.json.schemas.tags import GLOBAL_SCHEMA_STORE
from model.datapack.datapackContents import ResourceLocationNode, ResourceLocationSchema
from model.json.core import *
from model.json.core import OPTIONS_JSON_ARG_TYPE, ALL_NAMED_JSON_ARG_TYPES
from model.json.jsonContext import jsonStringContext, JsonStringContext
from model.messages import *
from model.nbt.tags import NBTTagSchema
from model.parsing.bytesUtils import strToBytes
from model.parsing.contextProvider import Suggestions, validateTree, getSuggestions, getDocumentation, onIndicatorClicked, getClickableRanges, parseNPrepare, CtxInfo
from model.parsing.tree import Schema
from model.pathUtils import joinFilePath, dirFromFilePath
from model.utils import GeneralError, Position, Span, MDStr, LanguageId


@jsonStringContext(MINECRAFT_RESOURCE_LOCATION.name)
class ResourceLocationHandler(JsonStringContext):
	def schema(self, node: JsonString) -> ResourceLocationSchema:
		schema = node.schema
		if isinstance(schema, JsonStringSchema):
			args = schema.args
			schema = (args or {}).get('schema')
		else:
			schema = None

		if schema is None:
			schema = ResourceLocationSchema('', 'any')

		if isinstance(schema, str):
			schema = ResourceLocationSchema('', schema)
		if not isinstance(schema, ResourceLocationSchema):
			logError(f"invalid 'schema' argument for JsonArgType '{MINECRAFT_RESOURCE_LOCATION.name}' in JsonStringSchema: {schema}. Expected an instance of ResourceLocationContext.")
			schema = ResourceLocationSchema('', 'any')
		return schema

	def prepare(self, node: JsonString, info: CtxInfo[JsonString], errorsIO: list[GeneralError]) -> None:
		data = strToBytes(node.data)
		sr = StringReader(data, 0, 0, 0, data)

		allowTag = True
		location = sr.readResourceLocation(allowTag=allowTag)
		if len(location) != len(node.data):
			errorsIO.append(JsonSemanticsError(EXPECTED_BUT_GOT_MSG.format(MINECRAFT_RESOURCE_LOCATION.name, node.data), node.span))
			# node.parsedValue = node.data
			# return
		schema = self.schema(node)
		start = node.span.start
		start = replace(start, column=start.column + 1, index=start.index + 1)
		end = node.span.end
		if node.typeName == 'string':
			offset = node.indexMapper.toEncoded(end.index - start.index) + start.index - end.index  # todo: test
		else:
			offset = 0
		end = replace(end, column=end.column + offset, index=end.index + offset)
		if len(node.data) + 2 == node.span.length:
			end = replace(end, column=end.column - 1, index=end.index - 1)
		span = Span(start, end)
		location = ResourceLocationNode.fromString(location, span, schema)
		node.parsedValue = location

	def validate(self, node: JsonString, errorsIO: list[JsonSemanticsError]) -> None:
		if isinstance(node.parsedValue, ResourceLocationNode):
			validateTree(node.parsedValue, b'', errorsIO)

	# def getSuggestions2(self, ai: ArgumentSchema, contextStr: str, cursorPos: int, replaceCtx: str) -> Suggestions:
	# 	return self.context.getSuggestions(contextStr, cursorPos, replaceCtx)

	def getSuggestions(self, node: JsonString, pos: Position, replaceCtx: str) -> Suggestions:
		posInContextStr = pos.index - node.span.start.index
		return getSuggestions(node.parsedValue, b'', pos, replaceCtx)

	def getDocumentation(self, node: JsonString, position: Position) -> MDStr:
		tips = []
		valueDoc = getDocumentation(node.parsedValue, b'', position)
		if valueDoc:
			tips.append(valueDoc)

		propertyDoc = super(ResourceLocationHandler, self).getDocumentation(node, position)
		if propertyDoc:
			tips.append(propertyDoc)

		return MDStr('\n\n'.join(tips))  # '\n<br>\n'.join(tips)

	def getClickableRanges(self, node: JsonString) -> Optional[Iterable[Span]]:
		return getClickableRanges(node.parsedValue, b'')

	def onIndicatorClicked(self, node: JsonString, pos: Position, window: QWidget) -> None:
		return onIndicatorClicked(node.parsedValue, b'', pos, window)


class ParsingJsonCtx(JsonStringContext, ABC):

	@abstractmethod
	def getSchema(self, node: JsonString) -> Optional[Schema]:
		pass

	@abstractmethod
	def getLanguage(self, node: JsonString) -> LanguageId:
		pass

	def getParserKwArgs(self, node: JsonString) -> dict[str, Any]:
		return {}

	def prepare(self, node: JsonString, info: CtxInfo[JsonString], errorsIO: list[GeneralError]) -> None:
		# remainder = sr.tryReadRemaining()
		schema = self.getSchema(node)
		language = self.getLanguage(node)

		data, errors = parseNPrepare(
			strToBytes(node.data),
			filePath=info.filePath,
			language=language,
			schema=schema,
			line=node.span.start.line,
			lineStart=node.span.start.index - node.span.start.column,
			cursor=0,
			cursorOffset=node.span.start.index + 1,
			indexMapper=node.indexMapper,
			**self.getParserKwArgs(node)
		)
		errorsIO.extend(errors)
		node.parsedValue = data

	def validate(self, node: JsonString, errorsIO: list[GeneralError]) -> None:
		validateTree(node.parsedValue, b'', errorsIO)

	def getSuggestions(self, node: JsonString, pos: Position, replaceCtx: str) -> Suggestions:
		if node.parsedValue is not None:
			return getSuggestions(node.parsedValue, b'', pos, replaceCtx)
		return []

	def getDocumentation(self, node: JsonString, pos: Position) -> MDStr:
		docs = [
			super(ParsingJsonCtx, self).getDocumentation(node, pos),
			getDocumentation(node.parsedValue, b'', pos)
		] if node.parsedValue is not None else []
		return MDStr('\n\n'.join(docs))

	def getClickableRanges(self, node: JsonString) -> Optional[Iterable[Span]]:
		if node.parsedValue is not None:
			return getClickableRanges(node.parsedValue, b'')

	def onIndicatorClicked(self, node: JsonString, pos: Position, window: QWidget) -> None:
		if node.parsedValue is not None:
			onIndicatorClicked(node.parsedValue, b'', pos, window)


@jsonStringContext(MINECRAFT_NBT_COMPOUND_TAG.name)
@jsonStringContext(MINECRAFT_NBT_TAG.name)
class NBTJsonStrContext(ParsingJsonCtx):

	def getSchema(self, node: JsonString) -> Optional[Schema]:
		if isinstance(node.schema, JsonStringSchema):
			return node.schema.args.get('schema') or NBTTagSchema('')

	def getLanguage(self, node: JsonString) -> LanguageId:
		return LanguageId('SNBT')


@jsonStringContext(MINECRAFT_CHAT_COMMAND.name)
class CommandJsonStrContext(ParsingJsonCtx):

	def getSchema(self, node: JsonString) -> Optional[Schema]:
		from model.commands.command import MCFunctionSchema
		from session.session import getSession
		if isinstance(node.schema, JsonStringSchema):
			schema = node.schema.args.get('schema') if node.schema.args is not None else None
			return schema or MCFunctionSchema('', commands=getSession().minecraftData.commands)

	def getLanguage(self, node: JsonString) -> LanguageId:
		return LanguageId('MCCommand')


@jsonStringContext(OPTIONS_JSON_ARG_TYPE.name)
class OptionsJsonStrContext(JsonStringContext):

	def prepare(self, node: JsonString, info: CtxInfo[JsonString], errorsIO: list[GeneralError]) -> None:
		pass

	def validate(self, node: JsonString, errorsIO: list[GeneralError]) -> None:
		if isinstance(node.schema, JsonStringSchema):
			if node.data not in node.schema.args.get('values', ()):
				errorsIO.append(JsonSemanticsError(UNKNOWN_MSG.format("Option", node.data), node.span))

	def getSuggestions(self, node: JsonString, pos: Position, replaceCtx: str) -> Suggestions:
		if isinstance(node.schema, JsonStringSchema):
			return list(node.schema.args.get('values', ()))
		return []


@jsonStringContext(DPE_FLOAT.name)
class FloatJsonStrContext(JsonStringContext):

	def prepare(self, node: JsonString, info: CtxInfo[JsonString], errorsIO: list[GeneralError]) -> None:
		data = node.data
		try:
			if data and data[0] == ord('-'):
				valToCHeck = data[1:]
			else:
				valToCHeck = data
			if valToCHeck.isdigit():
				number = int(data)
			else:
				number = float(data)
			node.parsedValue = number

		except ValueError:
			self._error(MDStr(f"Invalid number: `{data}`"), node.span)

	def validate(self, node: JsonString, errorsIO: list[GeneralError]) -> None:
		if isinstance(node.schema, JsonStringSchema):
			pass  # todo test min max

	def getSuggestions(self, node: JsonString, pos: Position, replaceCtx: str) -> Suggestions:
		return []


@jsonStringContext(DPE_JSON_ARG_TYPE.name)
class JsonStrCtxJsonStrContext(JsonStringContext):

	def prepare(self, node: JsonString, info: CtxInfo[JsonString], errorsIO: list[GeneralError]) -> None:
		pass

	def validate(self, node: JsonString, errorsIO: list[GeneralError]) -> None:
		if isinstance(node.schema, JsonStringSchema):
			pass
		if node.data not in ALL_NAMED_JSON_ARG_TYPES:
			errorsIO.append(JsonSemanticsError(UNKNOWN_MSG.format("JsonArgType", node.data), node.span))

	def getSuggestions(self, node: JsonString, pos: Position, replaceCtx: str) -> Suggestions:
		return list(ALL_NAMED_JSON_ARG_TYPES.keys())

	def getDocumentation(self, node: JsonString, pos: Position) -> MDStr:
		argType = ALL_NAMED_JSON_ARG_TYPES.get(node.data)
		if argType is not None:
			description = argType.description
		else:
			description = MDStr('')

		docs = [
			super(JsonStrCtxJsonStrContext, self).getDocumentation(node, pos),
			description
		] if node.parsedValue is not None else []
		return MDStr('\n\n'.join(docs))


def _getLibrary(dirPath, libraryPath):
	libraryFilePath = joinFilePath(dirPath, libraryPath)
	library = GLOBAL_SCHEMA_STORE.orchestrator.getSchemaLibrary(path=libraryFilePath)
	return library


@jsonStringContext(DPE_LIB_PATH.name)
class LibPathJsonStrContext(JsonStringContext):

	def prepare(self, node: JsonString, info: CtxInfo[JsonString], errorsIO: list[GeneralError]) -> None:
		dirPath = dirFromFilePath(info.filePath)
		data = node.data
		tree = info.ctxProvider.tree
		libraryPath = node
		if isinstance(libraryPath, JsonString):
			library = _getLibrary(dirPath, libraryPath.data)
			libraryFilePath = library.filePath
		else:
			libraryFilePath = None
		node.parsedValue = tree, libraryFilePath, dirPath

	def validate(self, node: JsonString, errorsIO: list[GeneralError]) -> None:
		if isinstance(node.schema, JsonStringSchema):
			pass
		if node.parsedValue is None or node.parsedValue[1] is None:
			errorsIO.append(JsonSemanticsError(UNKNOWN_MSG.format("library", node.data), node.span))

	def getSuggestions(self, node: JsonString, pos: Position, replaceCtx: str) -> Suggestions:
		return []

	def getDocumentation(self, node: JsonString, pos: Position) -> MDStr:
		if node.parsedValue is None or node.parsedValue[1] is None:
			description = MDStr('')
		else:
			description = MDStr(node.parsedValue[1])

		docs = [
			super(LibPathJsonStrContext, self).getDocumentation(node, pos),
			description
		] if node.parsedValue is not None else []
		return MDStr('\n\n'.join(docs))

	def getClickableRanges(self, node: JsonString) -> Optional[Iterable[Span]]:
		if node.parsedValue is not None and node.parsedValue[1] is not None:
			return (node.span,)

	def onIndicatorClicked(self, node: JsonString, pos: Position, window: QWidget) -> None:
		if node.parsedValue is not None and node.parsedValue[1] is not None:
			window._tryOpenOrSelectDocument(node.parsedValue[1])


@jsonStringContext(DPE_DEF_REF.name, propKey='$definitions', libraryAttr='definitions', unknownMsg="definition")
@jsonStringContext(DPE_TMPL_REF.name, propKey='$templates', libraryAttr='templates', unknownMsg="template")
@dataclass
class TmplRefJsonStrContext(JsonStringContext):
	propKey: str
	libraryAttr: str
	unknownMsg: str

	def prepare(self, node: JsonString, info: CtxInfo[JsonString], errorsIO: list[GeneralError]) -> None:
		dirPath = dirFromFilePath(info.filePath)
		data = node.data
		tree = info.ctxProvider.tree
		if ':' in data:
			ns, _, ref = data.rpartition(':')
			libraryPath = resolvePath(tree, ("$libraries", ns))
			if isinstance(libraryPath, JsonString):
				library = _getLibrary(dirPath, libraryPath.data)
				definition = getattr(library, self.libraryAttr).get(ref)
				libraryFilePath = library.filePath
			else:
				definition = None
				libraryFilePath = None
		else:
			definition = resolvePath(tree, (self.propKey, data))
			libraryFilePath = info.filePath
		node.parsedValue = definition, tree, libraryFilePath, dirPath

	def validate(self, node: JsonString, errorsIO: list[GeneralError]) -> None:
		if isinstance(node.schema, JsonStringSchema):
			pass
		if node.parsedValue is None or node.parsedValue[0] is None:
			errorsIO.append(JsonSemanticsError(UNKNOWN_MSG.format(self.unknownMsg, node.data), node.span))

	def getSuggestions(self, node: JsonString, pos: Position, replaceCtx: str) -> Suggestions:
		if node.parsedValue is None:
			return []
		tree = node.parsedValue[1]
		definitions = resolvePath(tree, (self.propKey,))
		if not isinstance(definitions, JsonObject):
			definitions = []
		else:
			definitions = list(definitions.data.keys())

		libraries = resolvePath(tree, ("$libraries",))
		if not isinstance(libraries, JsonObject):
			return definitions
		dirPath = node.parsedValue[3]
		for ns, prop in libraries.data.items():
			if isinstance(prop.value.data, str):
				# definition, tree, libraryFilePath, dirPath
				libraryPath = prop.value.data
				library = _getLibrary(dirPath, libraryPath)
				definitions.extend(f'{ns}:{d}' for d in getattr(library, self.libraryAttr).keys())
		return definitions

	def getDocumentation(self, node: JsonString, pos: Position) -> MDStr:
		if node.parsedValue is None or node.parsedValue[0] is None:
			return MDStr('')

		description = resolvePath(node.parsedValue[0], ("description",))
		if isinstance(description, JsonString):
			description = MDStr(description.data)
		else:
			description = MDStr('')

		docs = [
			super(TmplRefJsonStrContext, self).getDocumentation(node, pos),
			description
		] if node.parsedValue is not None else []
		return MDStr('\n\n'.join(docs))

	def getClickableRanges(self, node: JsonString) -> Optional[Iterable[Span]]:
		if node.parsedValue is not None and node.parsedValue[0] is not None:
			return (node.span,)

	def onIndicatorClicked(self, node: JsonString, pos: Position, window: QWidget) -> None:
		if node.parsedValue is not None and node.parsedValue[0] is not None:
			window._tryOpenOrSelectDocument(node.parsedValue[2], Span(node.parsedValue[0].span.start))



def init() -> None:
	pass
