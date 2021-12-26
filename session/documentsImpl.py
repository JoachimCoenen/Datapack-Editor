from typing import Sequence

from Cat.CatPythonGUI.GUI.codeEditor import Error
from Cat.Serializable import RegisterContainer, Serialized
from Cat.CatPythonGUI.AutoGUI import propertyDecorators as pd
from model.commands.parser import parseMCFunction
from model.commands.validator import checkMCFunction, getSession
from model.pathUtils import FilePath
from session.documents import RegisterDocument, TextDocument


@RegisterDocument('JSON', ext=['.json', '.mcmeta'], defaultLanguage='JSON')
@RegisterContainer
class JsonDocument(TextDocument):
	"""docstring for Document"""
	__slots__ = ()

	def __typeCheckerInfo___(self):
		# giving the type checker a helping hand...
		super(JsonDocument, self).__typeCheckerInfo___()
		self.filePath: FilePath = ''
		self.filePathForDisplay: str = ''
		self.fileName: str = ''
		self.fileLocationAbsolute: FilePath = ''
		self.fileLocationInProject: FilePath = ''
		self.fileChanged: bool = False
		self.documentChanged: bool = False
		self.encoding: str = 'utf-8'
		self.content: str = ''

	filePath: FilePath = Serialized(default='', decorators=[
		pd.FilePath(filters=[('JSON', '.json')])
	])

	encoding: str = Serialized(default='utf-8')

	def validate(self) -> Sequence[Error]:
		return []


@RegisterDocument('mcFunction', ext=['.mcFunction'], defaultLanguage='MCFunction')
@RegisterContainer
class MCFunctionDocument(TextDocument):
	"""docstring for Document"""
	__slots__ = ()

	def __typeCheckerInfo___(self):
		# giving the type checker a helping hand...
		super(MCFunctionDocument, self).__typeCheckerInfo___()
		self.filePath: FilePath = ''
		self.filePathForDisplay: str = ''
		self.fileName: str = ''
		self.fileLocationAbsolute: FilePath = ''
		self.fileLocationInProject: FilePath = ''
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
			errors += checkMCFunction(tree)
		return errors

def init() -> None:
	pass