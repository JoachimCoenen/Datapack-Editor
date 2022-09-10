from Cat.utils.logging_ import logError
from model.data.json.schemas.tags import GLOBAL_SCHEMA_STORE
from model.datapack.datapackContents import collectAllEntries
from model.parsing.contextProvider import parseNPrepare, validateTree
from model.pathUtils import ZipFilePool, loadBinaryFile
from model.project import Dependency, AspectType, ProjectAspect
from model.utils import LANGUAGES
from settings import applicationSettings

DATAPACK_ASPECT_TYPE = AspectType('dpe:datapack')
DATAPACK_CONTENTS_TYPE = AspectType('dpe:datapack_contents')


class DatapackAspect(ProjectAspect):
	@classmethod
	def getAspectType(cls) -> AspectType:
		return DATAPACK_ASPECT_TYPE

	@property
	def dependencies(self) -> list[Dependency]:
		dependencies = [Dependency(applicationSettings.minecraft.executable, mandatory=True)]
		filePath = (self.parent.path, 'dependencies.json')
		try:
			with ZipFilePool() as pool:
				file = loadBinaryFile(filePath, pool)
		except (OSError, KeyError) as e:
			logError(e)
			return dependencies

		schema = GLOBAL_SCHEMA_STORE.get('dpe:dependencies')
		node, errors = parseNPrepare(file, filePath=filePath, language=LANGUAGES.JSON, schema=schema, allowMultilineStr=False)
		if node is not None:
			validateTree(node, file, errors)

		if node is not None and not errors:
			for element in node.data:
				dependencies.append(Dependency(
					element.data['name'].value.data,
					element.data['mandatory'].value.data
				))

		return dependencies

	def analyzeProject(self) -> None:
		from session.session import getSession
		allEntryHandlers = getSession().datapackData.structure
		collectAllEntries(self.parent.files, allEntryHandlers, self.parent)

