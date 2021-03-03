import sqlite3

import functional.paths as paths


def get_pg_tt_connect():
    sqlite3.connect(paths.get_old_db_path())


def get_sqlite_tt_connect():
    sqlite3.connect(paths.get_tt_db_path())


def get_sqlite_old_connect():
    sqlite3.connect(paths.get_old_db_path())