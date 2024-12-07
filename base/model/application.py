from dataclasses import dataclass
from typing import Callable, cast

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from cat.utils import HTMLStr


@dataclass
class AppInfo:
	appName: str
	appDisplayName: str
	appVersion: str
	organization: str
	windowIcon: Callable[[], QIcon] | None
	copyright: HTMLStr
	about: HTMLStr
	homepageLink: str
	disclaimer: str | None = None


@dataclass
class App:

	_info: AppInfo
	_qApp: QApplication

	@property
	def qApp(self) -> QApplication:
		return self._qApp

	@property
	def info(self) -> AppInfo:
		return self._info

	def exec(self) -> None:
		self.qApp.exec()


_APP: App | None = None


def getApp() -> App | None:
	return _APP


def instantiateApp(argv: list[str], info: AppInfo) -> App:
	global _APP
	if _APP is not None:
		raise ValueError(f"App already instantiated.")

	qApp = QApplication(argv)
	_APP = App(info, qApp)
	qApp.setApplicationName(info.appName)
	qApp.setApplicationDisplayName(info.appDisplayName)
	qApp.setApplicationVersion(info.appVersion)
	qApp.setOrganizationName(info.organization)
	if info.windowIcon is not None:
		qApp.setWindowIcon(info.windowIcon())

	return _APP


__all__ = [
	'AppInfo',
	'App',
	'getApp',
	'instantiateApp',
]

