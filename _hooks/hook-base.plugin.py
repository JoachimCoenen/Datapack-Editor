import os
from os.path import abspath, dirname, join

from PyInstaller.utils.hooks import collect_submodules


def getResourcesPath(name: str) -> str:
	return abspath(dirname(__file__) + f'/../{name}/')


def getDatas(name: str, path: str) -> list[tuple[str, str]]:
	immediateResourceDirs = []

	for dirName in next(os.walk(path), (None, (), None))[1]:
		dirPath = join(path, dirName)
		if dirName == 'resources':
			immediateResourceDirs.append((dirPath, f'{name}/{dirName}/'))
		else:
			immediateResourceDirs += getDatas(f'{name}/{dirName}', dirPath)
	return immediateResourceDirs


pluginFolderNames = ['basePlugins', 'corePlugins']
hiddenimports = [submodule for pluginFolderName in pluginFolderNames for submodule in collect_submodules(pluginFolderName)]
datas = [resourceDir for pluginFolderName in pluginFolderNames for resourceDir in getDatas(pluginFolderName, getResourcesPath(pluginFolderName))]