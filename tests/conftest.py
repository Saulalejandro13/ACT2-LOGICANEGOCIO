import sys
from pathlib import Path

# Permite `from edutech...` sin instalar el paquete (estructura src/edutech/...)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
