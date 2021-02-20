def run():
    import os
    import platform
    from pathlib import Path

    _CWD = Path.cwd()
    _FILE = Path(__file__)
    _REQUIRED_DIR = _FILE.parent

    if platform.system() == "Linux" and _CWD != _REQUIRED_DIR:
        os.chdir(_REQUIRED_DIR)
