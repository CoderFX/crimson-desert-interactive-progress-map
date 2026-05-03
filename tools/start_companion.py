"""Launch CD Companion server. Run as Administrator."""
import sys
sys.path.insert(0, r"C:\Users\gelum\Desktop\CD_Companion source 0.6.0")
from main import _main
import asyncio
asyncio.run(_main())
