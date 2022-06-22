import os

sitePackagesPath = os.path.abspath(os.path.abspath(os.path.dirname(__file__)) + '/../venv/Lib/site-packages')

datas = [
    (sitePackagesPath + '/minecraft_data/data/data', 'minecraft_data/data/data'),
]
