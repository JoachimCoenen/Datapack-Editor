import os
import sys

from PyQt5.QtGui import QIcon

from base.model.applicationSettings import getApplicationSettings
from base.startup import AppOptions, start


def run() -> None:
	iconPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icon/icon.png')
	appOptions = AppOptions(
		appName=getApplicationSettings().applicationName,
		appDisplayName=getApplicationSettings().applicationName,
		appVersion=getApplicationSettings().version,
		organization=getApplicationSettings().organization,
		windowIcon=lambda: QIcon(iconPath)
	)
	start(sys.argv, appOptions)


if __name__ == '__main__':
	run()
