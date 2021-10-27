from PyQt5.QtGui import QKeySequence

from Cat import utils
from Cat.utils import CachedProperty


class KeySequences:
	@CachedProperty
	def FIND_ALL(self) -> QKeySequence:
		return QKeySequence('Ctrl+Shift+F')

	@CachedProperty
	def GO_TO_FILE(self) -> QKeySequence:
		return QKeySequence('Ctrl+P')

	@CachedProperty
	def NEW(self) -> QKeySequence:
		return QKeySequence(QKeySequence.New)

	@CachedProperty
	def SAVE_AS(self) -> QKeySequence:
		# windows does not have a standard key sequence for 'Save As':
		return QKeySequence('Ctrl+Shift+S') if utils.PLATFORM_IS_WINDOWS else QKeySequence(QKeySequence.SaveAs)

	@CachedProperty
	def CLOSE_DOCUMENT(self) -> QKeySequence:
		return QKeySequence('Ctrl+W') if utils.PLATFORM_IS_WINDOWS else QKeySequence(QKeySequence.Close)


KEY_SEQUENCES = KeySequences()

__all__ = [
	'KEY_SEQUENCES'
]