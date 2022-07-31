from Cat.utils.logging_ import logError
from model.datapack.datapackContents import DatapackContents, collectAllEntries
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

		from model.data.json.schemas.dependency import DEPENDENCIES_SCHEMA
		node, errors = parseNPrepare(file, language=LANGUAGES.JSON, schema=DEPENDENCIES_SCHEMA, allowMultilineStr=False)
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

