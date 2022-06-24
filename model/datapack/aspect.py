from model.datapack.datapackContents import DatapackContents, collectAllEntries
from model.project import Dependency, AspectType, ProjectAspect

DATAPACK_ASPECT_TYPE = AspectType('dpe:datapack')
DATAPACK_CONTENTS_TYPE = AspectType('dpe:datapack_contents')


class DatapackAspect(ProjectAspect):
	@classmethod
	def getAspectType(cls) -> AspectType:
		return DATAPACK_ASPECT_TYPE

	@property
	def dependencies(self) -> list[Dependency]:
		return []  # todo: compute/load from file

	def analyzeProject(self) -> None:
		contents = self.parent.setdefaultIndex(DatapackContents)
		from session.session import getSession
		allEntryHandlers = getSession().datapackData.structure
		collectAllEntries(self.parent.files, allEntryHandlers, self.parent)

