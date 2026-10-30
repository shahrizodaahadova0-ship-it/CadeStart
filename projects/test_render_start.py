from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
import subprocess

from django.test import SimpleTestCase

from deploy.render_start import main


class RenderStartTests(SimpleTestCase):
    def run_start(self, existing=False, failure=None):
        with TemporaryDirectory() as directory:
            root = Path(directory) / 'data'
            database = root / 'db.sqlite3'
            if existing:
                root.mkdir()
                database.touch()
            settings = SimpleNamespace(DATA_ROOT=root, DATABASES={'default': {'NAME': database, 'ENGINE': 'django.db.backends.sqlite3'}})
            with patch('django.setup'), patch('django.conf.settings', settings), \
                    patch.dict('os.environ', {'PORT': '12345'}), \
                    patch('deploy.render_start.subprocess.run', side_effect=failure) as run, \
                    patch('deploy.render_start.os.execvp') as launch:
                if failure:
                    with self.assertRaises(subprocess.CalledProcessError):
                        main()
                    launch.assert_not_called()
                else:
                    main()
                    self.assertTrue(root.is_dir())
                    args = launch.call_args.args[1]
                    self.assertIn('0.0.0.0:12345', args)
                    self.assertEqual(args[args.index('--workers') + 1], '1')
                    self.assertIn('config.wsgi:application', args)
                return [call.args[0][2] for call in run.call_args_list]

    def test_new_database_migrates_before_server_starts(self):
        self.assertEqual(self.run_start(), ['migrate'])

    def test_existing_database_is_backed_up_before_migration(self):
        self.assertEqual(self.run_start(existing=True), ['backup_database', 'migrate'])

    def test_failed_migration_prevents_server_start(self):
        self.run_start(failure=subprocess.CalledProcessError(1, 'migrate'))

    def test_postgres_does_not_require_a_local_disk_or_sqlite_backup(self):
        settings = SimpleNamespace(DATABASES={'default': {'NAME': 'neondb', 'ENGINE': 'django.db.backends.postgresql'}})
        with patch('django.setup'), patch('django.conf.settings', settings), \
                patch.dict('os.environ', {}), patch('deploy.render_start.subprocess.run') as run, \
                patch('deploy.render_start.os.execvp') as launch:
            main()
        self.assertEqual([call.args[0][2] for call in run.call_args_list], ['migrate'])
        launch.assert_called_once()
