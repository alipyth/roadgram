"""Entry point for PyInstaller (see build_exe.ps1). For normal use: `python -m roadgram` or the installed `roadgram`."""
import sys

from roadgram.cli import main

if __name__ == "__main__":
    sys.exit(main())
