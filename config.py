import ctypes
from pathlib import Path
import pytesseract as pt
import platform
import multiprocessing as mp


# TODO: Replace this config dict with a parser interpreted by stlib's configparser
CONFIG = {
    "DEBUG": True,
    "TABLE_PATTERNS_PATH": Path('assets/templates/tables'),
    "OS": platform.system()
}

if not CONFIG["DEBUG"]:
    ctypes.windll.user32.SetProcessDPIAware()
    # on windows, it's necessary to install the tesseract binaries and set the correct path for pytesseract to use
    pt.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
