from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from contextlib import closing

from django.test import SimpleTestCase

from .backups import backup_database, verify_backup


class BackupTests(SimpleTestCase):
    def test_backup_copies_committed_wal_data_without_uncommitted_changes(self):
        with TemporaryDirectory() as directory:
            source = Path(directory) / 'live.sqlite3'
            target = Path(directory) / 'backup.sqlite3'
            with closing(sqlite3.connect(source)) as writer:
                writer.execute('PRAGMA journal_mode=WAL')
                writer.execute('CREATE TABLE sample (value TEXT)')
                writer.execute('INSERT INTO sample VALUES (?)', ['committed'])
                writer.commit()
                writer.execute('INSERT INTO sample VALUES (?)', ['not committed'])
                backup_database(source, target)
                with closing(sqlite3.connect(target)) as result:
                    self.assertEqual(result.execute('SELECT value FROM sample').fetchall(), [('committed',)])
                writer.rollback()
            verify_backup(target)
            self.assertFalse(list(Path(directory).glob('*.partial')))

    def test_existing_destination_and_live_database_cannot_be_overwritten(self):
        with TemporaryDirectory() as directory:
            source, target = Path(directory) / 'live.sqlite3', Path(directory) / 'existing.sqlite3'
            source.write_bytes(b'source')
            target.write_bytes(b'keep this')
            with self.assertRaises(FileExistsError):
                backup_database(source, target)
            with self.assertRaises(ValueError):
                backup_database(source, source)
            self.assertEqual(target.read_bytes(), b'keep this')
            self.assertEqual(source.read_bytes(), b'source')

    def test_missing_source_is_not_created(self):
        with TemporaryDirectory() as directory:
            source, target = Path(directory) / 'missing.sqlite3', Path(directory) / 'backup.sqlite3'
            with self.assertRaises(FileNotFoundError):
                backup_database(source, target)
            self.assertFalse(source.exists())
            self.assertFalse(target.exists())

    def test_corrupt_source_leaves_no_partial_backup(self):
        with TemporaryDirectory() as directory:
            source, target = Path(directory) / 'corrupt.sqlite3', Path(directory) / 'backup.sqlite3'
            source.write_bytes(b'not a sqlite database')
            with self.assertRaises(sqlite3.DatabaseError):
                backup_database(source, target)
            self.assertFalse(target.exists())
            self.assertFalse(list(Path(directory).glob('*.partial')))
