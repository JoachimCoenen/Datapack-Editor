from typing import Sequence, Optional

from Cat.CatPythonGUI.GUI.codeEditor import Error
from Cat.Serializable import RegisterContainer, Serialized, ComputedCached
from Cat.CatPythonGUI.AutoGUI import propertyDecorators as pd
from Cat.utils import format_full_exc
from model.commands.parser import parseMCFunction
from model.commands.validator import checkMCFunction, getSession
from model.datapackContents import MetaInfo, getEntryHandlerForFile, JsonMeta
from model.json.core import JsonSchema
from model.json.parser import parseJsonStr
from model.json.validator import validateJson
from model.pathUtils import FilePath
from model.utils import WrappedError
from session.documents import RegisterDocument, TextDocument, Document


class DatapackDocument(Document):
	__slots__ = ()

	def __typeCheckerInfo___(self):
		# giving the type checker a helping hand...
		super(DatapackDocument, self).__typeCheckerInfo___()
		self.metaInfo: Optional[MetaInfo] = None

	@ComputedCached(shouldSerialize=False)
	def metaInfo(self) -> Optional[MetaInfo]:
		entryHandlers = getSession().datapackData.structure
		if (resLocHandler := getEntryHandlerForFile(self.filePath, entryHandlers)) is not None:
			rl, handler = resLocHandler
			metaInfo = handler.buildMetaInfo(self.filePath, rl)
			return metaInfo


@RegisterDocument('JSON', ext=['.json', '.mcmeta'], defaultLanguage='MCJson')
@RegisterContainer
class JsonDocument(TextDocument, DatapackDocument):
	"""docstring for Document"""
	__slots__ = ()

	def __typeCheckerInfo___(self):
		# giving the type checker a helping hand...
		super(JsonDocument, self).__typeCheckerInfo___()
		self.filePath: FilePath = ''
		self.filePathForDisplay: str = ''
		self.fileName: str = ''
		self.fileLocationAbsolute: FilePath = ''
		self.fileChanged: bool = False
		self.documentChanged: bool = False
		self.encoding: str = 'utf-8'
		self.content: str = ''

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
			return None

	def validate(self) -> Sequence[Error]:
		schema = self.schema
		try:
			tree, errors = parseJsonStr(self.content, True, schema)
			if tree is not None:
				self.tree = tree
				errors += validateJson(tree)
		except Exception as e:
			print(format_full_exc(e))
			return [WrappedError(e)]
		return errors


@RegisterDocument('mcFunction', ext=['.mcFunction'], defaultLanguage='MCFunction')
@RegisterContainer
class MCFunctionDocument(TextDocument, DatapackDocument):
	"""docstring for Document"""
	__slots__ = ()

	def __typeCheckerInfo___(self):
		# giving the type checker a helping hand...
		super(MCFunctionDocument, self).__typeCheckerInfo___()
		self.filePath: FilePath = ''
		self.filePathForDisplay: str = ''
		self.fileName: str = ''
		self.fileLocationAbsolute: FilePath = ''
		self.fileChanged: bool = False
		self.documentChanged: bool = False
		self.encoding: str = 'utf-8'
		self.content: str = ''

	filePath: FilePath = Serialized(default='', decorators=[
		pd.FilePath(filters=[('mcFunction', '.mcFunction')])
	])

	encoding: str = Serialized(default='utf-8')

	def validate(self) -> Sequence[Error]:
		tree, errors = parseMCFunction(getSession().minecraftData.commands, self.content)
		if tree is not None:
			self.tree = tree
			errors += checkMCFunction(tree)
		return errors


def init() -> None:
	pass
