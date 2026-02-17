import sys
import os

site_packages = r"C:\Users\artur\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\site-packages"
if site_packages not in sys.path:
    sys.path.append(site_packages)

try:
    import app
    print("Import successful")
except Exception as e:
    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()
