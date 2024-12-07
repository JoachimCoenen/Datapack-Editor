import os
import sys

from PyQt5.QtGui import QIcon

from base.model.application import AppInfo
from base.startup import start
from cat.utils import HTMLStr


def run() -> None:
	iconPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icon/icon.png')
	appOptions = AppInfo(
		appName="Datapack Editor",
		appDisplayName="Datapack Editor",
		appVersion="0.8.0-alpha",
		organization="Joachim Coenen",
		windowIcon=lambda: QIcon(iconPath),
		copyright=HTMLStr("© 2023 Joachim Coenen. All Rights Reserved"),
		about=HTMLStr("""Written and maintained by <a href="https://www.github.com/JoachimCoenen">Joachim Coenen</a>.\n<br/>""" +
					  """If you have any questions, bugs or improvements, please share them on GitHub.\n<br/>"""),
		homepageLink="https://www.github.com/JoachimCoenen/Datapack-Editor",
		disclaimer=HTMLStr("""Some information is taken from the Minecraft Wiki (see <a href="https://minecraft.wiki/w/Minecraft_Wiki:General_disclaimer">Minecraft Wiki:General disclaimer</a>).\n<br/>""" +
						   """\n<br/>""" +
						   """This program is not affiliated with Mojang Studios.""")
	)
	start(sys.argv, appOptions)


if __name__ == '__main__':
	run()
