"""Compile QML resources before launching or packaging GoodbyeDPI-UI.

Blocking execution is required: otherwise the app may load the old
resource_rc.py before pyside6-rcc has regenerated it.
"""
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parent
QRC = ROOT / "src" / "resource.qrc"
OUTPUT = ROOT / "src" / "resource_rc.py"


def find_rcc():
    executable = shutil.which("pyside6-rcc")
    if executable:
        return executable
    scripts = Path(sys.prefix) / ("Scripts" if sys.platform == "win32" else "bin")
    executable = scripts / ("pyside6-rcc.exe" if sys.platform == "win32" else "pyside6-rcc")
    if executable.is_file():
        return str(executable)
    raise FileNotFoundError(
        "pyside6-rcc is not installed. Install PySide6 from requirements.txt."
    )


if __name__ == "__main__":
    subprocess.run(
        [find_rcc(), str(QRC), "-o", str(OUTPUT)],
        check=True,
        cwd=str(ROOT),
    )
    if not OUTPUT.exists() or OUTPUT.stat().st_size == 0:
        raise RuntimeError("Qt resource compilation produced no output")
    print(f"Qt resources regenerated: {OUTPUT}")
