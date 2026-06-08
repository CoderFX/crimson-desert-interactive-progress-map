"""Launch CD Companion position tracker. Run as Administrator."""
import sys, os

# Search common locations for CD Companion source
SEARCH_PATHS = [
    os.path.expandvars(r"%USERPROFILE%\Desktop\CD_Companion source 0.6.0"),
    os.path.expandvars(r"%USERPROFILE%\Desktop\cd-companion"),
    os.path.expandvars(r"%USERPROFILE%\Downloads\CD_Companion source 0.6.0"),
    os.path.join(os.path.dirname(__file__), '..', 'cd-companion'),
]

found = None
for p in SEARCH_PATHS:
    if os.path.exists(os.path.join(p, 'engine.py')):
        found = p
        break

if not found:
    print("CD Companion source not found. Checked:")
    for p in SEARCH_PATHS:
        print(f"  {p}")
    print("\nDownload from Nexus Mods and extract to your Desktop.")
    input("Press Enter to exit...")
    sys.exit(1)

sys.path.insert(0, found)
from main import _main
import asyncio
asyncio.run(_main())
