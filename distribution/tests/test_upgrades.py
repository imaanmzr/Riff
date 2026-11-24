"""Managed upgrades preserve substantive content and resolve host copies explicitly."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from distribution.install import hashes, inspect_installation, install


class UpgradeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project = Path(temporary.name)
        (self.project / '.riff').mkdir()
        (self.project / '.riff/project.json').write_text('{"custom":true}')

    def skill(self, folder, version='0.8.0'):
        path = self.project / folder / 'skills/riff'
        (path / 'references').mkdir(parents=True)
        (path / 'SKILL.md').write_bytes(f'---\nname: riff\n---\nVersion {version}.\n'.encode())
        (path / 'references/guide.md').write_bytes(b'Preserve this guidance.\n')
        (path / 'asset.js').write_bytes(b'const bytes = 1;\n')
        manifest = {name.replace('/', '\\'): value for name, value in hashes(path).items()}
        (path / '.installation.json').write_text(json.dumps(dict(version=version, hashes=manifest)))
        return path

    def cli(self, *args, answers=None):
        return subprocess.run([sys.executable, '-B', str(ROOT / 'riff.py'), *args,
                               '--project', str(self.project)], input=answers, capture_output=True,
                              text=True, encoding='utf-8', timeout=30)

    def test_newline_only_text_is_managed_and_can_be_updated(self):
        path = self.skill('.agents', '0.7.0')
        for file in (path / 'SKILL.md', path / 'references/guide.md'):
            file.write_bytes(file.read_bytes().replace(b'\n', b'\r\n'))
        result = inspect_installation(path)
        self.assertEqual('newline-only', result['integrity'])
        self.assertEqual(['SKILL.md', 'references/guide.md'], result['newline_only_files'])
        install(self.project, update=True)
        self.assertEqual('unchanged', inspect_installation(path)['integrity'])
        self.assertEqual('{"custom":true}', (self.project / '.riff/project.json').read_text())

    def test_actual_edits_and_binary_newline_changes_are_protected(self):
        path = self.skill('.agents')
        for name, data in [('references/guide.md', b'Changed meaning.\n'),
                           ('asset.js', b'const bytes = 1;\r\n')]:
            with self.subTest(file=name):
                file = path / name
                before = file.read_bytes()
                file.write_bytes(data)
                self.assertEqual('modified', inspect_installation(path)['integrity'])
                with self.assertRaisesRegex(ValueError, 'Preserve your edits'):
                    install(self.project, update=True)
                self.assertEqual(data, file.read_bytes())
                file.write_bytes(before)
        (path / 'notes.txt').write_text('User notes')
        self.assertEqual('modified', inspect_installation(path)['integrity'])
        (path / 'notes.txt').unlink()
        (path / 'references/guide.md').unlink()
        self.assertEqual('modified', inspect_installation(path)['integrity'])

    def test_doctor_reports_conflicting_discoverable_copies(self):
        self.skill('.agents')
        self.skill('.cursor', '0.7.0')
        result = self.cli('doctor', '--host', 'cursor')
        self.assertEqual(1, result.returncode, result.stderr)
        self.assertIn('0.7.0', result.stdout)
        self.assertIn('0.8.0', result.stdout)
        self.assertIn('Conflicting Riff copies', result.stdout)

    def test_nested_installation_named_file_is_user_content_not_ignored_metadata(self):
        path = self.skill('.agents')
        nested = path / 'references/.installation.json'
        nested.write_bytes(b'{"user":"preserve"}')
        self.assertIn('references/.installation.json', inspect_installation(path)['changed_files'])
        with self.assertRaisesRegex(ValueError, 'Preserve your edits'):
            install(self.project, update=True)
        self.assertEqual(b'{"user":"preserve"}', nested.read_bytes())

    def test_doctor_accepts_equivalent_copies_despite_text_newlines(self):
        self.skill('.agents')
        cursor = self.skill('.cursor')
        file = cursor / 'SKILL.md'
        file.write_bytes(file.read_bytes().replace(b'\n', b'\r\n'))
        result = self.cli('doctor', '--host', 'cursor')
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_cursor_update_changes_its_direct_copy_and_preserves_native_copy(self):
        native = self.skill('.agents', '0.7.0')
        cursor = self.skill('.cursor', '0.7.0')
        before = hashes(native)
        result = self.cli('update', '--host', 'cursor', answers='\n' * 6 + 'no\n')
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual('0.8.0', inspect_installation(cursor)['version'])
        self.assertEqual(before, hashes(native))
        self.assertEqual('{"custom":true}', (self.project / '.riff/project.json').read_text())

    def test_ambiguous_shared_cursor_update_requires_explicit_native_host(self):
        first = self.skill('.agents')
        second = self.skill('.claude')
        before = (hashes(first), hashes(second))
        result = self.cli('update', '--host', 'cursor')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('explicitly', result.stderr)
        self.assertEqual(before, (hashes(first), hashes(second)))
        self.assertFalse((self.project / '.cursor').exists())


if __name__ == '__main__':
    unittest.main()
