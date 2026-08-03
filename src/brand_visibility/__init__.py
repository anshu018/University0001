"""
Brand Visibility Agent package initialization.
"""
import sys
from pathlib import Path

# Ensure project root directory is in Python path for root module imports (like config)
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

src_dir = Path(__file__).resolve().parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))
