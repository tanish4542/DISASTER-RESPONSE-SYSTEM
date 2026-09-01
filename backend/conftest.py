"""
Pytest configuration file.

Enables imports from the app module.
"""

import sys
from pathlib import Path

# Add backend directory to path so 'app' can be imported
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))
