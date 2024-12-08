source .venv/bin/activate  # select virtual environment
#pip install PyQt5 QScintilla QtAwesome recordclass timerit watchdog markdown nbtlib
mkdir build
cd build || exit
#DANGER!
rm -r ./build/

# Explanations:
#   - markdown.extensions.codehilite: Excluded to reduce file size a little (requires: pygments; size: 1.8 MiB for both)
#   - pygments: Excluded to reduce file size a little (requires optionally: PIL)
#   - PIL: Excluded to reduce file size a little (size: 1.2 MiB self)
pyinstaller --onefile ../main.py \
--additional-hooks-dir ../_hooks \
--hidden-import PyQt5.QtPrintSupport \
--exclude-module bprofile \
--exclude-module cat.utils.bprofileCustom \
--exclude-module javalang \
--exclude-module numpy.distutils \
--exclude-module setuptools._distutils \
--exclude-module markdown.extensions.codehilite \
--exclude-module PIL \
--icon=../icon/icon.png \
--noconfirm

cd dist || exit

rm -f ./path/file  DatapackEditor
mv main DatapackEditor