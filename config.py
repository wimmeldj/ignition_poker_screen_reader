import ctypes
from pathlib import Path
import pytesseract as pt
import platform
import re
import cv2


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

# GLOBALS ==============================================================================================================
DEBUG = CONFIG["DEBUG"]

# contains all images in assets/templates/tables converted to grayscale and sorted according to file name
TEMPLATES = [cv2.imread(str(_), cv2.IMREAD_GRAYSCALE) for _ in sorted(CONFIG["TABLE_PATTERNS_PATH"].glob('*'))]
HEADS_UP_TEMPLATES = TEMPLATES[7:8]
SIX_HANDED_TEMPLATES = TEMPLATES[0:4]
NINE_HANDED_TEMPLATES = TEMPLATES[3:7]

TABLE_ID_P = re.compile(r" (\d*?)$")
STAKE_P = re.compile(r"^\$(.*?)\/\$(.*?) ")
MONEY_P = re.compile("^\$(\d*?\.\d\d)$")
