#!/usr/bin/env python3

# --------------------- #
# -- SEVERAL IMPORTS -- #
# --------------------- #

from pathlib import Path
from pytest import fixture

from orpyste.data import ReadBlock as READ


# ------------------- #
# -- MODULE TESTED -- #
# ------------------- #

from mistool import url_use


# ----------------------- #
# -- GENERAL CONSTANTS -- #
# ----------------------- #

THIS_DIR = Path(__file__).parent

ISLINKED_FUNCTION = url_use.islinked


# ----------------------- #
# -- DATAS FOR TESTING -- #
# ----------------------- #

THE_DATAS_FOR_TESTING = READ(
    content = THIS_DIR / 'linked.txt',
    mode    = {"keyval:: =": ":default:"}
)

@fixture(scope="module")
def or_datas(request):
    THE_DATAS_FOR_TESTING.build()

    def remove_extras():
        THE_DATAS_FOR_TESTING.remove_extras()

    request.addfinalizer(remove_extras)


# ---------------- #
# -- CONNECTION -- #
# ---------------- #

def test_url_use_linked(or_datas):
    tests = THE_DATAS_FOR_TESTING.mydict("std nosep nonb")

    for name, datas in tests.items():
        url     = datas['url']
        success = eval(datas['success'])

        success_found = ISLINKED_FUNCTION(url)

        assert success == success_found
