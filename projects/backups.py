"""Consistent SQLite snapshots, including committed data still in the WAL."""
import os
import shutil
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path


def verify_backup(path):
    path = Path(path).resolve()
    with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=10)) as connection:
        result = connection.execute('PRAGMA integrity_check').fetchall()
        if result != [('ok',)]:
            raise ValueError('SQLite integrity check failed.')


def backup_database(source, destination):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if source == destination:
        raise ValueError('Backup destination must differ from the live database.')
    if destination.exists():
        raise FileExistsError('Backup destination already exists; choose a new filename.')
    if not source.is_file():
        raise FileNotFoundError('Source database does not exist.')
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    created = False
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent, suffix='.partial', delete=False) as file:
            temporary = Path(file.name)
        with closing(sqlite3.connect(source.as_uri() + '?mode=ro', uri=True, timeout=10)) as reader:
            with closing(sqlite3.connect(temporary)) as writer:
                reader.backup(writer)
        verify_backup(temporary)
        with destination.open('xb') as output:
            created = True
            with temporary.open('rb') as input_file:
                shutil.copyfileobj(input_file, output)
            output.flush()
            os.fsync(output.fileno())
        return destination
    except Exception:
        if created:
            destination.unlink(missing_ok=True)
        raise
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)
