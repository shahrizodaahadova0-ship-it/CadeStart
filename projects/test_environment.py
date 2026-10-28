from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from config.environment import load_environment


class EnvironmentTests(SimpleTestCase):
    def test_quotes_unicode_and_process_precedence(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / '.env'
            path.write_text('# comment\nNAME="Учебный проект"\nexport TOKEN=abc#123=xyz\nEXISTING=local\nEMPTY=\n', encoding='utf-8-sig')
            values = {'EXISTING': 'process'}
            self.assertTrue(load_environment(path, values))
            self.assertEqual(values['NAME'], 'Учебный проект')
            self.assertEqual(values['TOKEN'], 'abc#123=xyz')
            self.assertEqual(values['EXISTING'], 'process')
            self.assertEqual(values['EMPTY'], '')

    def test_values_are_literal_and_not_executed(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / '.env'
            path.write_text("VALUE='$(anything) ${SECRET} `command`'\n", encoding='utf-8')
            values = {}
            load_environment(path, values)
            self.assertEqual(values['VALUE'], '$(anything) ${SECRET} `command`')

    def test_invalid_file_does_not_partially_apply_or_reveal_values(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / '.env'
            path.write_text('VALID=private-test-value\nINVALID LINE\n', encoding='utf-8')
            values = {}
            with self.assertRaises(ImproperlyConfigured) as raised:
                load_environment(path, values)
            self.assertEqual(values, {})
            self.assertNotIn('private-test-value', str(raised.exception))

    def test_missing_file_and_unclosed_quotes(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / '.env'
            self.assertFalse(load_environment(path, {}))
            self.assertFalse(path.exists())
            path.write_text('KEY="unclosed\n', encoding='utf-8')
            with self.assertRaises(ImproperlyConfigured):
                load_environment(path, {})
