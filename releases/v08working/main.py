import sys
import os

# Фикс для PyInstaller --windowed: когда нет консоли,
# sys.stdin/stdout/stderr могут быть None, что ломает
# некоторые библиотеки (например logging, rich, input())
if sys.stdin is None:
    sys.stdin = open(os.devnull, "r")
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui import *