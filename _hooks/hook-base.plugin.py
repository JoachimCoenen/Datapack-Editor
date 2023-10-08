import os

basePluginsResourcesPath = os.path.abspath(os.path.dirname(__file__) + '/../basePlugins/')
corePluginsResourcesPath = os.path.abspath(os.path.dirname(__file__) + '/../corePlugins/')

datas = [
    (basePluginsResourcesPath, 'basePlugins/'),
    (corePluginsResourcesPath, 'corePlugins/'),
]