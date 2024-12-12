import sys
from pathlib import Path

# Add local LightRAG source to Python path
sys.path.insert(0, str(Path.cwd()))

import lightrag
print('Chemin de lightrag:', lightrag.__file__)
