"""Force UTF-8 stdout/stderr so Unicode prints work on Windows consoles.

Windows terminals default to a legacy code page (e.g. cp1252), which raises
UnicodeEncodeError when a script tries to print characters like the check/cross
marks used in verify_model_available(). Calling force_utf8_output() at the top
of an entry-point script fixes this permanently, with no need to set
PYTHONIOENCODING manually before every run.
"""

import sys


def force_utf8_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8")
        except (ValueError, OSError):
            pass
