# Umožní testom importovať moduly z priečinka src/
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
