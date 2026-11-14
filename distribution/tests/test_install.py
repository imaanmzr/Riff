import sys
import tempfile
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from install import install

class InstallTests(unittest.TestCase):
    def test_install_preserves_project_and_updates(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/'AGENTS.md').write_text('keep project rules')
            install(root)
            skill=root/'.agents/skills/riff'
            self.assertTrue((skill/'SKILL.md').exists())
            self.assertTrue((skill/'references/routing/router.py').exists())
            config=root/'.engineering-workflow/project.json'; config.write_text('{"custom":true}')
            install(root,True)
            self.assertEqual('{"custom":true}',config.read_text())
            self.assertEqual('keep project rules',(root/'AGENTS.md').read_text())
    def test_refuses_unmanaged_and_modified(self):
        with tempfile.TemporaryDirectory() as d:
            install(d)
            skill=Path(d)/'.agents/skills/riff/SKILL.md'
            skill.write_text('local changes')
            with self.assertRaises(ValueError): install(d,True)
            self.assertEqual('local changes',skill.read_text())
    def test_requires_update_flag(self):
        with tempfile.TemporaryDirectory() as d:
            install(d)
            with self.assertRaises(ValueError): install(d)
    def test_symlink_refusal(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as other:
            try:
                (Path(d)/'.agents').symlink_to(other, target_is_directory=True)
            except OSError as exc:
                if getattr(exc, 'winerror', None) == 1314:
                    self.skipTest('Creating a Windows symlink requires additional privileges')
                raise
            with self.assertRaises(ValueError): install(d)
    def test_skill_frontmatter_and_links(self):
        root=Path(__file__).resolve().parents[1]/'skills/riff'
        s=(root/'SKILL.md').read_text()
        front=s.split('---',2)[1]
        values=dict(line.split(': ',1) for line in front.strip().splitlines())
        self.assertEqual({'name','description'},set(values))
        self.assertEqual('riff',values['name'])
        for phase in ('planning','execution','recovery','routing'):
            self.assertTrue((root/'references'/phase/'WORKFLOW.md').exists())

class MultiHostTests(unittest.TestCase):
    def test_host_paths(self):
        for host,folder in [('codex','.agents'),('cursor','.cursor'),('claude','.claude'),
                            ('vscode','.github')]:
            with self.subTest(host=host), tempfile.TemporaryDirectory() as d:
                install(d,host=host)
                self.assertTrue((Path(d)/folder/'skills/riff/SKILL.md').exists())
                install(d,True,host)
    def test_cursor_reuses_discoverable_copy(self):
        with tempfile.TemporaryDirectory() as d:
            install(d,host='claude')
            with self.assertRaisesRegex(ValueError,'already discover'): install(d,host='cursor')
            self.assertFalse((Path(d)/'.cursor').exists())
    def test_host_instructions_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'CLAUDE.md'; p.write_text('existing rules')
            install(d,host='claude'); self.assertEqual('existing rules',p.read_text())
    def test_update_moves_managed_legacy_skill(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            install(project)
            skill = project / '.agents/skills/riff'
            legacy = skill.rename(skill.with_name('engineering-workflow'))
            config = project / '.engineering-workflow/project.json'
            config.write_text('{"custom": true}')

            install(project, update=True)

            self.assertFalse(legacy.exists())
            self.assertIn('name: riff', (skill / 'SKILL.md').read_text())
            self.assertEqual('{"custom": true}', config.read_text())

    def test_unknown_host(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError): install(d,host='unknown')

if __name__=='__main__': unittest.main()
