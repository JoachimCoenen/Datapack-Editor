from abc import abstractmethod
from typing import Sequence, Optional, Any

from Cat.Serializable import RegisterContainer, Serialized, ComputedCached
from Cat.CatPythonGUI.AutoGUI import propertyDecorators as pd
from Cat.utils.logging_ import logError
from Cat.utils.profiling import TimedMethod
from model.commands.command import MCFunctionSchema
from model.datapack.datapackContents import MetaInfo, JsonMeta, getMetaInfo
from model.json.core import JsonSchema
from model.nbt.tags import NBTTagSchema
from base.model.parsing.contextProvider import getContextProvider, parseNPrepare
from base.model.parsing.tree import Node, Schema
from base.model.pathUtils import FilePath
from base.model.utils import WrappedError, GeneralError
from base.model.documents import RegisterDocument, TextDocument
from sessionOld.session import getSession


def initPlugin():
	pass


class DatapackDocument(TextDocument):
	__slots__ = ()

	def __typeCheckerInfo___(self):
		# giving the type checker a helping hand...
		super(DatapackDocument, self).__typeCheckerInfo___()
		self.tree: Optional[Node] = None
		self.metaInfo: Optional[MetaInfo] = None

	# tree: Optional[Node] = Serialized(default=None, shouldSerialize=False, shouldPrint=False, decorators=[pd.NoUI()])

	@ComputedCached(shouldSerialize=False)
	def metaInfo(self) -> Optional[MetaInfo]:
		return getMetaInfo(self.filePath, getSession().datapackData.structure)

	@property
	@abstractmethod
	def schema(self) -> Optional[Schema]:
		pass

	@property
	def parseKwArgs(self) -> dict[str, Any]:
		return {}

	@TimedMethod(enabled=True)
	def parse(self, text: bytes) -> tuple[Optional[Node], Sequence[GeneralError]]:
		try:
			schema = self.schema
			language = schema.language if schema is not None else self.language
			return parseNPrepare(text, filePath=self.filePath, language=language, schema=schema, **self.parseKwArgs)
		except Exception as e:
			logError(e)
			return None, [WrappedError(e)]

	@TimedMethod(enabled=True)
	def validate(self) -> Sequence[GeneralError]:
		errors = []
		try:
			if (tree := self.tree) is not None:
				ctxProvider = getContextProvider(tree, self.content)
				if ctxProvider is not None:
					ctxProvider.validateTree(errors)
			return errors
		except Exception as e:
			logError(e)
			return [WrappedError(e)]


@RegisterDocument('JSON', ext=['.json', '.mcmeta'], defaultLanguage='MCJson')
@RegisterContainer
class JsonDocument(DatapackDocument, TextDocument):
	"""docstring for Document"""

	__slots__ = ()

	def __typeCheckerInfo___(self):
		# giving the type checker a helping hand...
		super(JsonDocument, self).__typeCheckerInfo___()
		self.filePath: FilePath = ''
		self.fileChanged: bool = False
		self.documentChanged: bool = False
		self.encoding: str = 'utf-8'
		self.content: bytes = b''

	filePath: FilePath = Serialized(default='', decorators=[
		pd.FilePath(filters=[('JSON', '.json')])
	])

	encoding: str = Serialized(default='utf-8')

	@property
	def schema(self) -> Optional[JsonSchema]:
		if isinstance(self.metaInfo, JsonMeta):
			schemaId = self.metaInfo.schemaId
			return getSession().datapackData.jsonSchemas.get(schemaId)
		else:
			return getSession().datapackData.jsonSchemas.get('dpe:json_schema')

	@property
	def parseKwArgs(self) -> dict[str, Any]:
		return dict(allowMultilineStr=True)

	# def parseStr(self, text: bytes) -> tuple[Optional[Node], list[GeneralError]]:
	# 	parser = JsonParser(text, self.schema, allowMultilineStr=True)
	# 	node = parser.parse()
	# 	return node, parser.errors
	# 	# return parseJsonStr(self.content, True, self.schema)

	# def validate(self) -> Sequence[Error]:
	# 	schema = self.schema
	# 	try:
	# 		tree, errors = parseJsonStr(self.content, True, schema)
	# 		if tree is not None:
	# 			self.tree = tree
	# 			prepareTree(tree, self.content)
	# 			errors += validateJson(tree)
	# 	except Exception as e:
	# 		print(format_full_exc(e))
	# 		return [WrappedError(e)]
	# 	return errors


@RegisterDocument('mcFunction', ext=['.mcFunction'], defaultLanguage='MCFunction')
@RegisterContainer
class MCFunctionDocument(DatapackDocument, TextDocument):
	"""docstring for Document"""
	__slots__ = ()

	def __typeCheckerInfo___(self):
		# giving the type checker a helping hand...
		super(MCFunctionDocument, self).__typeCheckerInfo___()
		self.filePath: FilePath = ''
		self.fileChanged: bool = False
		self.documentChanged: bool = False
		self.encoding: str = 'utf-8'
		self.content: bytes = b''
		self.strContent: str = ''

	filePath: FilePath = Serialized(default='', decorators=[
		pd.FilePath(filters=[('mcFunction', '.mcFunction')])
	])

	encoding: str = Serialized(default='utf-8')

	@property
	def schema(self) -> Optional[MCFunctionSchema]:
		return MCFunctionSchema('', commands=getSession().minecraftData.commands)


@RegisterDocument('SNBT', ext=['.snbt'], defaultLanguage='SNBT')
@RegisterContainer
class SNBTDocument(DatapackDocument, TextDocument):
	"""docstring for Document"""
	__slots__ = ()

	def __typeCheckerInfo___(self):
		# giving the type checker a helping hand...
		super(SNBTDocument, self).__typeCheckerInfo___()
		self.filePath: FilePath = ''
		self.fileChanged: bool = False
		self.documentChanged: bool = False
		self.encoding: str = 'utf-8'
		self.content: bytes = b''

	filePath: FilePath = Serialized(default='', decorators=[
		pd.FilePath(filters=[('SNBT', '.snbt')])
	])

	encoding: str = Serialized(default='utf-8')

	@property
	def schema(self) -> Optional[NBTTagSchema]:
		return NBTTagSchema('')
		# if isinstance(self.metaInfo, JsonMeta):
		# 	schemaId = self.metaInfo.schemaId
		# 	return getSession().datapackData.jsonSchemas.get(schemaId)
		# else:
		# 	return None