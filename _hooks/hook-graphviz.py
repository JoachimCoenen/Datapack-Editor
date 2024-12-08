
# ------------------------------------------------------------------
# This file is a straight copy of hook-pygraphviz.py from the pyinstaller repository.
# The original license still applies.
# Original License for hook-pygraphviz.py:
# ------------------------------------------------------------------
# Copyright (c) 2021 PyInstaller Development Team.
#
# This file is distributed under the terms of the GNU General Public
# License (version 2.0 or later).
#
# The full license is available in LICENSE.GPL.txt, distributed with
# this software.
#
# SPDX-License-Identifier: GPL-2.0-or-later
# ------------------------------------------------------------------

import glob
import os
import shutil

from PyInstaller.compat import is_darwin, is_win, is_linux
from PyInstaller.depend.bindepend import findLibrary

binaries = []
datas = []

# List of binaries agraph.py may invoke.
progs = [
    "neato",
    "dot",
    "twopi",
    "circo",
    "fdp",
    "nop",
    "acyclic",
    "gvpr",
    "gvcolor",
    "ccomps",
    "sccmap",
    "tred",
    "sfdp",
    "unflatten",
]

if is_win:
    for prog in progs:
        for binary in glob.glob("c:/Program Files/Graphviz*/bin/" + prog + ".exe"):
            binaries.append((binary, "."))
    for binary in glob.glob("c:/Program Files/Graphviz*/bin/*.dll"):
        binaries.append((binary, "."))
    for data in glob.glob("c:/Program Files/Graphviz*/bin/config*"):
        datas.append((data, "."))
else:
    if is_linux:
        # see: https://stackoverflow.com/questions/78014447/pyinstaller-unable-to-find-usr-sbin-neato-when-adding-binary-and-data-files
        # graphviz_bindir = '/usr/bin'
        graphviz_bindir = os.path.dirname(shutil.which("dot"))
    else:
        # The dot binary in PATH is typically a symlink, handle that.
        # graphviz_bindir is e.g. /usr/local/Cellar/graphviz/2.46.0/bin
        graphviz_bindir = os.path.dirname(os.path.realpath(shutil.which("dot")))

    for binary in progs:
        binary_path = os.path.realpath(graphviz_bindir + "/" + binary)
        binaries.append((binary_path, "."))
    if is_darwin:
        suffix = "dylib"
        # graphviz_libdir is e.g. /usr/local/Cellar/graphviz/2.46.0/lib/graphviz
        graphviz_libdir = os.path.realpath(graphviz_bindir + "/../lib/graphviz")
    else:
        suffix = "so.6"  # suffix = "so"; strange, but the built DatapackEditor expects the libraries with a '.6' appended...
        # graphviz_libdir is e.g. /usr/lib64/graphviz
        graphviz_libdir = os.path.join(os.path.dirname(findLibrary('libcdt')), 'graphviz')
    for binary in glob.glob(graphviz_libdir + "/*." + suffix):
        binaries.append((binary, "graphviz"))
    for data in glob.glob(graphviz_libdir + "/config*"):
        datas.append((data, "graphviz"))
