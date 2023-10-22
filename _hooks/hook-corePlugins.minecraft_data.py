import os

python_minecraft_dataPath = os.path.abspath(os.path.dirname(__file__) + '/../corePlugins/minecraft_data/data/data')

datas = [
    (python_minecraft_dataPath + '/dataPaths.json', 'corePlugins/minecraft_data/data/data'),
    (python_minecraft_dataPath + '/pc', 'corePlugins/minecraft_data/data/data/pc'),
]
