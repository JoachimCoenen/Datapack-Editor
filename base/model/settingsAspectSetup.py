from abc import ABC, abstractmethod
from typing import override

from base.model.applicationSettings import ApplicationSettings, SettingsAspect, getApplicationSettings
from cat.GUI.propertyDecorators import ValidatorResult
from gui.datapackEditorGUI import DatapackEditorGUI


class SettingsSetup(ABC):
	"""
	GUI + Actions to be performed when (some) settingsAspects are not set up correctly. For example when a Plugin is loaded for the first time.
	Inheritors must provide a parameterless __init__ method (i.e. def __init__(self):...)
	"""

	@property
	@abstractmethod
	def title(self) -> str:
		pass

	@abstractmethod
	def validate(self, settings: ApplicationSettings) -> list[ValidatorResult]:
		pass

	@abstractmethod
	def onGUI(self, gui: DatapackEditorGUI, settings: ApplicationSettings) -> None:
		pass

	def reset(self, settings: ApplicationSettings) -> None:
		pass


class SettingsAspectSetup[T: SettingsAspect](SettingsSetup, ABC):
	"""
	GUI + Actions to be performed when (some) settingsAspects are not set up correctly. For example when a Plugin is loaded for the first time.
	Inheritors must provide a parameterless __init__ method (i.e. def __init__(self):...)
	"""

	@abstractmethod
	def getSettingsAspect(self, settings: ApplicationSettings) -> T:
		pass

	@abstractmethod
	def aspectGUI(self, gui: DatapackEditorGUI, aspect: T) -> None:
		pass

	@staticmethod
	def validateAspect(aspect: T) -> list[ValidatorResult]:
		return aspect.validate()

	def resetAspect(self, aspect: T) -> None:
		pass

	@override
	def validate(self, settings: ApplicationSettings) -> list[ValidatorResult]:
		return self.validateAspect( self.getSettingsAspect(settings))

	@override
	def onGUI(self, gui: DatapackEditorGUI, settings: ApplicationSettings) -> None:
		self.aspectGUI(gui, self.getSettingsAspect(settings))

	@override
	def reset(self, settings: ApplicationSettings) -> None:
		self.resetAspect(self.getSettingsAspect(settings))
