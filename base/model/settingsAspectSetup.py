from abc import ABC, abstractmethod
from dataclasses import Field
from typing import override, Callable

from base.model.applicationSettings import ApplicationSettings, SettingsAspect
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
	def onGUI(self, gui: DatapackEditorGUI, settings: ApplicationSettings, vSpacer: Callable[[DatapackEditorGUI], None]) -> None:
		pass

	def additionalReset(self, settings: ApplicationSettings) -> None:
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
	def getAspectFields(self, aspect: T) -> list[Field]:
		pass

	def additionalAspectReset(self, aspect: T) -> None:
		pass

	def validateAspect(self, aspect: T) -> list[ValidatorResult]:
		fields = self.getAspectFields(aspect)
		results = []
		for f in fields:
			results.extend(aspect.validateField(f))
		return results

	def aspectGUI(self, gui: DatapackEditorGUI, aspect: T, vSpacer: Callable[[DatapackEditorGUI], None]) -> None:
		fields = self.getAspectFields(aspect)
		if not fields:
			return

		fieldsIter = iter(fields)
		gui.propertyField(aspect, next(fieldsIter))
		for field in fieldsIter:
			vSpacer(gui)
			gui.propertyField(aspect, field)

	@override
	def validate(self, settings: ApplicationSettings) -> list[ValidatorResult]:
		return self.validateAspect(self.getSettingsAspect(settings))

	@override
	def onGUI(self, gui: DatapackEditorGUI, settings: ApplicationSettings, vSpacer: Callable[[DatapackEditorGUI], None]) -> None:
		self.aspectGUI(gui, self.getSettingsAspect(settings), vSpacer)

	@override
	def additionalReset(self, settings: ApplicationSettings) -> None:
		self.additionalAspectReset(self.getSettingsAspect(settings))
