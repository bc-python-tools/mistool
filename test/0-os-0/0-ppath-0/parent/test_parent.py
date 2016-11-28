#!/usr/bin/env python3

# --------------------- #
# -- SEVERAL IMPORTS -- #
# --------------------- #

from pathlib import Path as StdPath
from pytest import fixture

from orpyste.data import ReadBlock as READ


# ------------------- #
# -- MODULE TESTED -- #
# ------------------- #

from mistool import os_use


# ----------------------- #
# -- GENERAL CONSTANTS -- #
# ----------------------- #

THIS_DIR = StdPath(__file__).parent

PPATH_CLASS = os_use.PPath


# ----------------------- #
# -- DATAS FOR TESTING -- #
# ----------------------- #

THE_DATAS_FOR_TESTING = READ(
    content = THIS_DIR / 'parent.txt',
    mode    = {"keyval:: =": ":default:"}
)

@fixture(scope="module")
def or_datas(request):
    THE_DATAS_FOR_TESTING.build()

    def remove_extras():
        THE_DATAS_FOR_TESTING.remove_extras()

    request.addfinalizer(remove_extras)


# ---------------------- #
# -- PARENT DIRECTORY -- #
# ---------------------- #

def test_os_use_parent_dir(or_datas):
    tests = THE_DATAS_FOR_TESTING.mydict("std nosep nonb")

    for testname, infos in tests.items():
        path = infos['path']
        path = PPATH_CLASS(path)

        parent_wanted = infos['parent']
        parent_wanted = PPATH_CLASS(parent_wanted)

        parent_found = path.parent

        assert parent_wanted == parent_found
