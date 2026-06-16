import importlib, traceback, sys, os

# Ensure project root is on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

try:
    importlib.import_module('app.main')
    print('IMPORT_OK')
except Exception:
    traceback.print_exc()
