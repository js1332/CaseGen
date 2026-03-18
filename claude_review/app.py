"""
Unified entrypoint for the Golf Course Map Generator.

Desktop GUI entry for reference when reviewing the web app.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from main_gui import GolfMapApp  # type: ignore


def main() -> None:
    app = GolfMapApp()
    app.mainloop()


if __name__ == "__main__":
    main()

