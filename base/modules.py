from __future__ import annotations

import importlib.util
import os
import sys
from types import ModuleType
from typing import Optional, Callable, Iterable, NamedTuple

from Cat.extensions import processRecursively
from Cat.utils import openOrCreate, format_full_exc
from Cat.utils.logging_ import logError, logInfo, loggingIndent, loggingIndentInfo
from Cat.utils.profiling import TimedFunction
from base.model.pathUtils import FilePathStr, normalizeDirSeparatorsStr
from base.model.utils import Message


def _ensureModule(csDir: FilePathStr, name: str) -> None:
	initPath = os.path.join(csDir, '__init__.py')
	try:
		with openOrCreate(initPath, 'w'):
			pass
	except OSError as e:
		logError(e, f"Failed to open or create {name} module at path: '{initPath}'")


def collectAllModules(baseModuleName: str, baseModuleDir: FilePathStr, folderFilter: str, fileFilterRegex: Optional[str], setDefaultFilesFunc: Optional[Callable[[FilePathStr], None]]) -> list[tuple[str, FilePathStr]]:
	logInfo(f"{baseModuleName} dir = {baseModuleDir}")

	_ensureModule(baseModuleDir, baseModuleName)
	if setDefaultFilesFunc is not None:
		setDefaultFilesFunc(baseModuleDir)

	allModulePaths: list[str] = []  # next(os.walk(baseModuleDir))[1]
	processRecursively(baseModuleDir, folderFilter, allModulePaths.append, filenameRegex=fileFilterRegex)
	allModulePaths = [normalizeDirSeparatorsStr(p) for p in allModulePaths]

	allModuleNames = [(mp.removeprefix(baseModuleDir).removesuffix('.py').removesuffix('/__init__').lstrip('/'), mp) for mp in allModulePaths]
	allModules = [(f'{baseModuleName}.' + '.'.join(mn.split('/')), mp) for mn, mp in allModuleNames]
	# allModules = [(f'plugins.{mn}', joinFilePath(baseModuleDir, mn)) for mn in allModuleNames]
	return allModules


def _importModuleFromFile(moduleName: str, path: str):
	spec = importlib.util.spec_from_file_location(moduleName, path)
	foo = importlib.util.module_from_spec(spec)
	sys.modules[moduleName] = foo
	spec.loader.exec_module(foo)
	return foo


_CANNOT_LOAD_MSG = Message("{0} module '{1}' cannot be loaded, because {2}", 3)


def loadModules(baseModuleName: str, baseModulePath: FilePathStr, names: list[tuple[str, FilePathStr]], ) -> dict[str, ModuleType]:
	_importModuleFromFile(baseModuleName, os.path.join(baseModulePath, '__init__.py'))
	modules: dict[str, ModuleType] = {}
	for moduleName, modPath in names:
		try:
			thisMod = _importModuleFromFile(moduleName, modPath)
		except Exception as ex:
			logError(
				_CANNOT_LOAD_MSG.format(baseModuleName, moduleName, f"the following Exception occurred while loading the python module:"),
				format_full_exc(ex, indentLvl=1)
			)
			continue

		modules[moduleName] = thisMod
		# if getattr(thisMod, 'enabled') is True:
		# 	modules[moduleName] = thisMod
		# 	logInfo(f"imported {baseModuleName} {moduleName}")
		# else:
		# 	logInfo(f"imported {baseModuleName} {moduleName}: DISABLED")
	return modules


def reloadModules(baseModuleName: str, modules: Iterable[ModuleType]):
	for module in modules:
		moduleName = module.__name__
		try:
			importlib.reload(module)
		except Exception as ex:
			logError(
				_CANNOT_LOAD_MSG.format(baseModuleName, moduleName, f"the following Exception occurred while reloading the python module:"),
				format_full_exc(ex, indentLvl=1)
			)
			continue


def callModuleMethod(baseModuleName: str, modules: dict[str, ModuleType], methodName: str) -> None:
	for moduleName, module in modules.items():
		method = getattr(module, methodName, None)
		if method is None:
			logError(_CANNOT_LOAD_MSG.format(baseModuleName, moduleName, f"no '{methodName}()' function can be found."))
			continue
		if not callable(method):
			logError(_CANNOT_LOAD_MSG.format(baseModuleName, moduleName, f" '{moduleName}.{methodName}' is not callable. ('{type(method).__name__}' object is not callable)"))
			continue
		try:
			method()
		except Exception as ex:
			logError(
				_CANNOT_LOAD_MSG.format(baseModuleName, moduleName, f"the following Exception occurred while calling '{moduleName}.{methodName}()':"),
				format_full_exc(ex, indentLvl=1)
			)
			continue


class FolderAndFileFilter(NamedTuple):
	folderFilter: str
	fileFilterRegex: Optional[str]


@TimedFunction(details=lambda baseModuleName, baseModuleDir, *args, **kwargs: f"{baseModuleName} from directory '{baseModuleDir}'")
def loadAllModules(
		baseModuleName: str,
		baseModuleDir: FilePathStr,
		folderAndFileFilters: list[FolderAndFileFilter],
		*,
		setDefaultFilesFunc: Optional[Callable[[FilePathStr], None]] = None,
		initMethodName: Optional[str] = None
) -> dict[str, ModuleType]:
	with loggingIndent():
		baseModuleDir = normalizeDirSeparatorsStr(baseModuleDir)

		with loggingIndentInfo(f"collecting {baseModuleName} modules..."):
			pluginModuleNames = []
			for folderFilter, fileFilterRegex in folderAndFileFilters:
				pluginModuleNames.extend(collectAllModules(baseModuleName, baseModuleDir, folderFilter, fileFilterRegex, setDefaultFilesFunc))
		with loggingIndentInfo(f"loading {baseModuleName} modules..."):
			pluginModules = loadModules(baseModuleName, baseModuleDir, pluginModuleNames)
		# with loggingIndentInfo(f"reloading {baseModuleName} modules..."):
		# 	reloadModules(baseModuleName, pluginModules.values())
		if initMethodName:
			with loggingIndentInfo(f"calling {initMethodName}() for {baseModuleName} modules..."):
				callModuleMethod(baseModuleName, pluginModules, initMethodName)
		return pluginModules
