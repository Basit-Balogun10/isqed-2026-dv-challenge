"""Legacy compatibility shim.

Some internal tooling may reference a secondary engine filename.
"""

from .cdg_engine import main

if __name__ == "__main__":
    raise SystemExit(main())
