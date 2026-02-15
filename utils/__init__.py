import os
import sys


def resource_path(rel):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, rel)  # type: ignore
    return os.path.join(os.path.abspath("."), rel)
