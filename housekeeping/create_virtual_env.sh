#!/bin/bash
# creates virtual environment and installs all necessary packages.
if [ ! -d ".git" ]
then
  echo "you are not in the top-most folder of the project. execute the script from the top-most folder using:"
  echo ">> ./housekeeping/create_virtual_env.sh"
  exit 1
fi
python3 -m venv .venv
./housekeeping/update_virtual_env.sh
