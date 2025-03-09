# conftest.py fayli - pytest konfiguratsiyasi uchun

import pytest
import os
import sys

# Asosiy katalog yo'lini qo'shish
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Pytest Hook: Test natijalarini ko'rsatish uchun
def pytest_itemcollected(item):
    par = item.parent.obj
    node = item.obj
    pref = par.__doc__.strip() if par.__doc__ else par.__class__.__name__
    suf = node.__doc__.strip() if node.__doc__ else node.__name__
    if pref or suf:
        item._nodeid = f"{pref}: {suf}"