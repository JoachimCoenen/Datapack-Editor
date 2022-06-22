rem DANGER!:
rmdir /s /q ".\build\"

pyinstaller --onefile main.py ^
-p ..\Cat ^
--additional-hooks-dir _hooks ^
--hidden-import PyQt5.QtPrintSupport ^
--exclude-module bprofile ^
--exclude-module Cat.utils.bprofileCustom ^
--noconfirm
@pause
rem--hidden-import markdown ^