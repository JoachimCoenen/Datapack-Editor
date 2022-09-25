from Cat.utils.logging_ import logWarning
from model.data.json.schemas.tags import GLOBAL_SCHEMA_STORE
from model.datapack.datapackContents import collectAllEntries
from model.parsing.contextProvider import parseNPrepare, validateTree
from model.pathUtils import ZipFilePool, loadBinaryFile
from model.project import Dependency, AspectType, ProjectAspect
from model.utils import LANGUAGES, GeneralError, MDStr
from settings import applicationSettings

DATAPACK_ASPECT_TYPE = AspectType('dpe:datapack')
DATAPACK_CONTENTS_TYPE = AspectType('dpe:datapack_contents')


class DatapackAspect(ProjectAspect):
	@classmethod
	def getAspectType(cls) -> AspectType:
		return DATAPACK_ASPECT_TYPE

	@property
	def dependencies(self) -> list[Dependency]:
		fileName = 'dependencies.json'
		projectPath = self.parent.path
		schema = GLOBAL_SCHEMA_STORE.get('dpe:dependencies')

		if projectPath == applicationSettings.minecraft.executable:
			# Minecraft does not need to itself as a dependency.
			return []

		dependencies = [Dependency(applicationSettings.minecraft.executable, mandatory=True)]
		filePath = (projectPath, fileName)
		try:
			with ZipFilePool() as pool:
				file = loadBinaryFile(filePath, pool)
		except (OSError, KeyError) as e:
			node, errors = None, [GeneralError(MDStr(f"{type(e).__name__}: {str(e)}"))]
		else:
			node, errors = parseNPrepare(file, filePath=filePath, language=LANGUAGES.JSON, schema=schema, allowMultilineStr=False)

		if node is not None:
			validateTree(node, file, errors)

		if node is not None and not errors:
			for element in node.data:
				dependencies.append(Dependency(
					element.data['name'].value.data,
					element.data['mandatory'].value.data,
					element.data['name'].value.span
				))
		if errors:
			logWarning(f"Failed to read '{fileName}' for project '{projectPath}':")
			for error in errors:
				logWarning(error, indentLvl=1)

		return dependencies

	def analyzeProject(self) -> None:
		from session.session import getSession
		allEntryHandlers = getSession().datapackData.structure
		collectAllEntries(self.parent.files, allEntryHandlers, self.parent)

