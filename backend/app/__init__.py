import sys

try:
    import sqlite3
except ImportError:
    try:
        import pysqlite3
        sys.modules["sqlite3"] = pysqlite3
    except ImportError:
        pass
