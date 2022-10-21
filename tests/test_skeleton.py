import shutil

import pytest
import os

from dggs_tbx.utils import down_s2, db_connect

__author__ = "Benatia Fahd"


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