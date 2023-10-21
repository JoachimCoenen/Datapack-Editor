from abc import ABC, abstractmethod
from typing import TypeVar, Generic

from cat.GUI.propertyDecorators import ValidatorResult
from cat.Serializable.serializableDataclasses import SerializableDataclass
from base.model.project.project import Project
from gui.datapackEditorGUI import DatapackEditorGUI


_T = TypeVar('_T', bound=SerializableDataclass)


class ProjectCreator(Generic[_T], ABC):
	"""
	GUI + Actions to be performed when creating a new Project.
	Inheritors must provide a parameterless __init__ method (i.e. def __init__(self):...)
	"""

	def __init__(self, data: _T):
		self.data = data

	@property
	@abstractmethod
	def title(self) -> str:
		...

	def validate(self) -> list[ValidatorResult]:
		return self.data.validate()

	@abstractmethod
	def onGUI(self, gui: DatapackEditorGUI) -> None:
		pass

	@abstractmethod
	def initializeProject(self, gui: DatapackEditorGUI, project: Project) -> None:
		pass
