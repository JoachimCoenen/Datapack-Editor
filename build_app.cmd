pip install PyQt5 QScintilla QtAwesome recordclass timerit watchdog markdown nbtlib
mkdir build
cd build
rem DANGER!:
rmdir /s /q ".\build\"

pyinstaller --onefile ..\main.py ^
--additional-hooks-dir ..\_hooks ^
--hidden-import PyQt5.QtPrintSupport ^
--exclude-module bprofile ^
--exclude-module cat.utils.bprofileCustom ^
--exclude-module javalang ^
--exclude-module numpy.distutils ^
--exclude-module setuptools._distutils ^
--exclude-module markdown.extensions.codehilite ^
--exclude-module PIL ^
--icon=..\icon\icon.png ^
--noconfirm

cd dist

del DatapackEditor.exe
ren "main.exe" "DatapackEditor.exe"
@pause