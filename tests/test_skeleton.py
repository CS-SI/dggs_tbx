# Copyright (C) 2024-2025 CS GROUP, https://cs-soprasteria.com
#
# This file is part of DGGS Toolbox:
#
#     https://github.com/CS-SI/dggs_tbx
#
# SPDX-License-Identifier: LGPL-3.0-or-later
#
# DGGS Toolbox is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# DGGS Toolbox is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with DGGS Toolbox. If not, see
# https://www.gnu.org/licenses/.

import shutil

import pytest
import os

from dggs_tbx.utils import down_s2, db_connect

__author__ = "CS GROUP (Benatia Fahd, Nicolas Vila)"


def test_down_s2():
    test_dir = down_s2("32TQM","20220902")
    num_down = len(os.listdir(test_dir))
    shutil.rmtree(test_dir)
    assert num_down == 2

def test_db_connect():
    db_name = "DGGS"
    engine = db_connect(db_name)
    conn = engine.connect()
    conn.close()
