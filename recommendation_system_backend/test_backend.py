import sys
import os
from pathlib import Path

print("Current directory:", os.getcwd())
print("Directory contents:")
for item in os.listdir():
    print("  -", item)

print("\nSrc directory contents:")
for item in os.listdir("src"):
    print("  -", item)

print("\nChecking imports...")
try:
    from src.api.main import start as start_api
    print("Import from src.api.main succeeded")
except ImportError as e:
    print(f"Import from src.api.main failed: {e}")

try:
    import src.database.database
    print("Import from src.database.database succeeded")
except ImportError as e:
    print(f"Import from src.database.database failed: {e}")

try:
    import src.models.model
    print("Import from src.models.model succeeded")
except ImportError as e:
    print(f"Import from src.models.model failed: {e}")

try:
    import src.utils.context_utils
    print("Import from src.utils.context_utils succeeded")
except ImportError as e:
    print(f"Import from src.utils.context_utils failed: {e}")

print("\nPython sys.path:")
for p in sys.path:
    print("  -", p)

print("\nPython version:", sys.version) 