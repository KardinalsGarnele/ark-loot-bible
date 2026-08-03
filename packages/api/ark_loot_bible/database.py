from contextlib import contextmanager
import sqlite3
from .config import settings

@contextmanager
def connection():
    con = sqlite3.connect(settings.database_path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    try:
        yield con
    finally:
        con.close()
