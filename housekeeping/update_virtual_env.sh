#!/bin/bash
# installs/updates all necessary packages.

set -e # Subsequent commands which fail will cause the shell script to exit immediately.
       # This prevents accidentally overriding your local python installation.

source .venv/bin/activate  # select virtual environment
pip install -r ./requirements.txt  # update requirements
