if [ ! -d ".git" ]
then
  echo "you are not in the top-most folder of the project. execute the script from the top-most folder using:"
  echo ">> ./housekeeping/build_app.sh"
  exit 1
fi
if [ ! -d ".venv" ]
then
  echo "you are missing a virtual environment for python. You can create one using:"
  echo ">> ./housekeeping/create_virtual_env.sh"
  exit 1
fi

source .venv/bin/activate  # select virtual environment

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
