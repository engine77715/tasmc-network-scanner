import sys
import os
import multiprocessing

# Фикс для PyInstaller --onefile/--windowed на Windows:
# без freeze_support() и без защиты __name__ == "__main__"
# дочерние процессы (через subprocess/threading) могут повторно
# импортировать и исполнять весь скрипт с нуля, открывая окна
# приложения в бесконечном цикле.
multiprocessing.freeze_support()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    from gui import *