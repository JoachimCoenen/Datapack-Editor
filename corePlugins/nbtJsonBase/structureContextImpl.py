from collections import OrderedDict
from dataclasses import dataclass
from typing import Iterable

from base.model.messages import UNKNOWN_MSG
from base.model.parsing.contextProvider import CtxInfo, Suggestions
from base.model.pathUtils import joinFilePath, dirFromFilePath, FilePath
from base.model.session import getSession
from base.model.utils import GeneralError, SemanticsError, MDStr, Position, Span, Message
from .argTypes import *
from .core import *
from .context import structureStringContext, StringNodeContext, getStringNodeContext
from .schemaStore import STRUCTURE_SCHEMA_LOADER
from .schemaBuilder import SchemaLibrary
from .structureReader import SchemaTemplate, TemplateParam

INVALID_NUMBER_MSG = Message("Invalid number `{0}`", 1)


@structureStringContext(DPE_FLOAT.name)
class FloatStrContext(StringNodeContext):

	def prepare(self, node: StringNode, info: CtxInfo[StringNode], errorsIO: list[GeneralError]) -> None:
		data = node.data
		try:
			if data and data[0] == '-':
				valToCHeck = data[1:]
			else:
				valToCHeck = data
			if valToCHeck.isdigit():
				number = int(data)
			else:
				number = float(data)
			node.parsedValue = number

		except ValueError:
			errorsIO.append(SemanticsError(INVALID_NUMBER_MSG.format(data), span=node.span))

	def validate(self, node: StringNode, errorsIO: list[GeneralError]) -> None:
		if isinstance(node.schema, StringSchema):
			pass  # todo test min max

	def getSuggestions(self, node: StringNode, pos: Position, replaceCtx: str, info: CtxInfo[StructureNode]) -> Suggestions:
		return []


@structureStringContext(DPE_STRUCTURE_ARG_TYPE.name)
class StructureArgTypeStrContext(StringNodeContext):

	def prepare(self, node: StringNode, info: CtxInfo[StringNode], errorsIO: list[GeneralError]) -> None:
		pass

	def validate(self, node: StringNode, errorsIO: list[GeneralError]) -> None:
		if isinstance(node.schema, StringSchema):
			pass
		if node.data not in ALL_NAMED_STRUCTURE_ARG_TYPES:
			errorsIO.append(SemanticsError(UNKNOWN_MSG.format("StructureArgType", node.data), node.span))

	def getSuggestions(self, node: StringNode, pos: Position, replaceCtx: str, info: CtxInfo[StructureNode]) -> Suggestions:
		return list(ALL_NAMED_STRUCTURE_ARG_TYPES.keys())

	def getDocumentation(self, node: StringNode, pos: Position) -> MDStr:
		argType = ALL_NAMED_STRUCTURE_ARG_TYPES.get(node.data)
		if argType is not None:
			description = argType.description
		else:
			description = MDStr('')

		docs = [
			super().getDocumentation(node, pos),
			description
		] if node.parsedValue is not None else []
		return MDStr('\n\n'.join(docs))


def _getLibrary(dirPath: FilePath, libraryPath: str) -> SchemaLibrary:
	libraryFilePath = joinFilePath(dirPath, libraryPath)
	library = STRUCTURE_SCHEMA_LOADER.orchestrator.getSchemaLibrary(path=libraryFilePath)
	return library


@structureStringContext(DPE_LIB_PATH.name)
class LibPathStrContext(StringNodeContext):

	def prepare(self, node: StringNode, info: CtxInfo[StringNode], errorsIO: list[GeneralError]) -> None:
		dirPath = dirFromFilePath(info.filePath)
		data = node.data
		tree = info.ctxProvider.tree
		libraryPath = node
		if isinstance(libraryPath, StringNode):
			library = _getLibrary(dirPath, libraryPath.data)
			libraryFilePath = library.filePath
		else:
			libraryFilePath = None
		node.parsedValue = tree, libraryFilePath, dirPath

	def validate(self, node: StringNode, errorsIO: list[GeneralError]) -> None:
		if isinstance(node.schema, StringSchema):
			pass
		if node.parsedValue is None or node.parsedValue[1] is None:
			errorsIO.append(SemanticsError(UNKNOWN_MSG.format("library", node.data), node.span))

	def getSuggestions(self, node: StringNode, pos: Position, replaceCtx: str, info: CtxInfo[StructureNode]) -> Suggestions:
		return []

	def getDocumentation(self, node: StringNode, pos: Position) -> MDStr:
		if node.parsedValue is None or node.parsedValue[1] is None:
			description = MDStr('')
		else:
			description = MDStr(node.parsedValue[1])

		docs = [
			super(LibPathStrContext, self).getDocumentation(node, pos),
			description
		] if node.parsedValue is not None else []
		return MDStr('\n\n'.join(docs))

	def getClickableRanges(self, node: StringNode) -> Iterable[Span] | None:
		if node.parsedValue is not None and node.parsedValue[1] is not None:
			return (node.span,)

	def onIndicatorClicked(self, node: StringNode, pos: Position) -> None:
		if node.parsedValue is not None and node.parsedValue[1] is not None:
			getSession().tryOpenOrSelectDocument(node.parsedValue[1])


@dataclass
class TmplRefStrValue:
	definition: StructureDataSchema | SchemaTemplate | ObjectNode | None
	tree: StructureNode
	libraryFilePath: FilePath | None
	dirPath: FilePath


@structureStringContext(DPE_DEF_REF.name, propKey='$definitions', libraryAttr='definitions', unknownMsg="definition")
@structureStringContext(DPE_TMPL_REF.name, propKey='$templates', libraryAttr='templates', unknownMsg="template")
@dataclass
class TmplRefStrContext(StringNodeContext):
	propKey: str
	libraryAttr: str
	unknownMsg: str

	def prepare(self, node: StringNode, info: CtxInfo[StructureNode], errorsIO: list[GeneralError]) -> None:
		dirPath = dirFromFilePath(info.filePath)
		data = node.data
		tree = info.ctxProvider.tree
		if ':' in data:
			ns, _, ref = data.rpartition(':')
			libraryPath = resolvePath(tree, ("$libraries", ns))
			if isinstance(libraryPath, StringNode):
				library = _getLibrary(dirPath, libraryPath.data)
				definition = getattr(library, self.libraryAttr).get(ref)
				libraryFilePath = library.filePath
			else:
				definition = None
				libraryFilePath = None
		else:
			definition = resolvePath(tree, (self.propKey, data))
			libraryFilePath = info.filePath
		node.parsedValue = TmplRefStrValue(definition, tree, libraryFilePath, dirPath)

	def validate(self, node: StringNode, errorsIO: list[GeneralError]) -> None:
		if not isinstance(node.parsedValue, TmplRefStrValue) or node.parsedValue.definition is None:
			errorsIO.append(SemanticsError(UNKNOWN_MSG.format(self.unknownMsg, node.data), node.span))
		else:
			pass

	def getSuggestions(self, node: StringNode, pos: Position, replaceCtx: str, info: CtxInfo[StructureNode]) -> Suggestions:
		if not isinstance(node.parsedValue, TmplRefStrValue):
			return []
		tree = node.parsedValue.tree
		definitions = resolvePath(tree, (self.propKey,))
		if not isinstance(definitions, ObjectNode):
			definitions = []
		else:
			definitions = list(definitions.data.keys())

		libraries = resolvePath(tree, ("$libraries",))
		if not isinstance(libraries, ObjectNode):
			return definitions
		dirPath = node.parsedValue.dirPath
		for ns, prop in libraries.data.items():
			if isinstance(prop.value.data, str):
				# definition, tree, libraryFilePath, dirPath
				libraryPath = prop.value.data
				library = _getLibrary(dirPath, libraryPath)
				definitions.extend(f'{ns}:{d}' for d in getattr(library, self.libraryAttr).keys())
		return definitions

	def getDocumentation(self, node: StringNode, pos: Position) -> MDStr:
		if not isinstance(node.parsedValue, TmplRefStrValue) or (definition := node.parsedValue.definition) is None:
			return MDStr('')

		if isinstance(definition, StructureNode):
			description = resolvePath(definition, ("description",))
		else:
			description = node.parsedValue.definition.description

		docs = [
			super().getDocumentation(node, pos),
			description
		] if description is not None else []
		return MDStr('\n\n'.join(docs))

	def getClickableRanges(self, node: StringNode) -> Iterable[Span] | None:
		if isinstance(node.parsedValue, TmplRefStrValue) and node.parsedValue.definition is not None:
			return (node.span,)

	def onIndicatorClicked(self, node: StringNode, pos: Position) -> None:
		if isinstance(node.parsedValue, TmplRefStrValue) and node.parsedValue.definition is not None:
			getSession().tryOpenOrSelectDocument(node.parsedValue.libraryFilePath, Span(node.parsedValue.definition.span.start))


@structureStringContext(DPE_TMPL_REF_ARG_KEYS.name)
@dataclass
class TmplRefStrArgKeysContext(StringNodeContext):

	def _getTmplRefStrValue(self, node: StringNode) -> TmplRefStrValue | None:
		if isinstance(parent := node.parent, ObjectNode):
			if isinstance(refNode := parent.getValue('$ref'), StringNode):
				if isinstance(tmplRefStrValue := refNode.parsedValue, TmplRefStrValue):
					return tmplRefStrValue
		return None

	def _makeTemplateParam(self, name: str, node: StructureNode, span: Span) -> TemplateParam:
		type_ = resolvePath(node, ('type',))
		description = resolvePath(node, ('description',))
		default = resolvePath(node, ('default',))
		return TemplateParam(name, type_, description, default, span)

	def _getTemplate(self, node: StringNode) -> SchemaTemplate | ObjectNode | None:
		if (tmplRefStrValue := self._getTmplRefStrValue(node)) is not None:
			if isinstance(definition := tmplRefStrValue.definition, SchemaTemplate):
				return definition
			elif isinstance(definition, ObjectNode):
				paramsNode = resolvePath(definition, ("$params",))
				if isinstance(paramsNode, ObjectNode):
					params = {
						key: self._makeTemplateParam(key, prop.value, prop.key.span)
						for key, prop in paramsNode.data.items()
						if prop.value is not None
					}
				else:
					params = {}
				return SchemaTemplate(MDStr(''), OrderedDict(params), definition, definition.span)
		return None

	def prepare(self, node: StringNode, info: CtxInfo[StringNode], errorsIO: list[GeneralError]) -> None:
		pass

	def validate(self, node: StringNode, errorsIO: list[GeneralError]) -> None:
		if (template := self._getTemplate(node)) is None:
			return
		if (param := template.params.get(node.data)) is None:
			errorsIO.append(SemanticsError(UNKNOWN_MSG.format("argument", node.data), node.span))
		else:
			node.parsedValue = param

	def getSuggestions(self, node: StringNode, pos: Position, replaceCtx: str, info: CtxInfo[StructureNode]) -> Suggestions:
		template = self._getTemplate(node)
		if template is None:
			return []
		return list(template.params.keys())

	def getDocumentation(self, node: StringNode, pos: Position) -> MDStr:
		if not isinstance(node.parsedValue, TemplateParam):
			return MDStr('')
		return node.parsedValue.description

	def getClickableRanges(self, node: StringNode) -> Iterable[Span] | None:
		if isinstance(node.parsedValue, TemplateParam):
			return (node.span,)

	def onIndicatorClicked(self, node: StringNode, pos: Position) -> None:
		if isinstance(node.parsedValue, TemplateParam):
			if (tmplRefStrValue := self._getTmplRefStrValue(node)) is not None and tmplRefStrValue.definition is not None:
				getSession().tryOpenOrSelectDocument(tmplRefStrValue.libraryFilePath, Span(node.parsedValue.span.start))


@structureStringContext(DPE_MARKDOWN.name)
class MarkdownStrContext(StringNodeContext):

	def prepare(self, node: StringNode, info: CtxInfo[StringNode], errorsIO: list[GeneralError]) -> None:
		pass

	def validate(self, node: StringNode, errorsIO: list[GeneralError]) -> None:
		pass


##########################################################################################
################## Providers for calculated schemas in jsonSchema.json ###################
##########################################################################################


def getStringSchemaArgTypeArgsSchema(parent: ObjectNode) -> ObjectSchema | None:

	typeProp_ = parent.data.get('type', None)
	type_ = typeProp_.value.data if typeProp_ is not None else None

	jsonArgType = ALL_NAMED_STRUCTURE_ARG_TYPES.get(type_) if isinstance(type_, str) else None

	# validate args:
	if jsonArgType is not None:
		if (ctx := getStringNodeContext(jsonArgType.name)) is not None:
			argsSchema, requireArgs = ctx.getArgsSchema()
			return argsSchema
	return None
