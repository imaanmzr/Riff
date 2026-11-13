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
            skill=root/'.agents/skills/engineering-workflow'
            self.assertTrue((skill/'SKILL.md').exists())
            self.assertTrue((skill/'references/routing/router.py').exists())
            config=root/'.engineering-workflow/project.json'; config.write_text('{"custom":true}')
            install(root,True)
            self.assertEqual('{"custom":true}',config.read_text())
            self.assertEqual('keep project rules',(root/'AGENTS.md').read_text())
    def test_refuses_unmanaged_and_modified(self):
        with tempfile.TemporaryDirectory() as d:
            install(d)
            skill=Path(d)/'.agents/skills/engineering-workflow/SKILL.md'
            skill.write_text('local changes')
            with self.assertRaises(ValueError): install(d,True)
            self.assertEqual('local changes',skill.read_text())
    def test_requires_update_flag(self):
        with tempfile.TemporaryDirectory() as d:
            install(d)
            with self.assertRaises(ValueError): install(d)
    def test_symlink_refusal(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as other:
            (Path(d)/'.agents').symlink_to(other)
            with self.assertRaises(ValueError): install(d)
    def test_skill_frontmatter_and_links(self):
        root=Path(__file__).resolve().parents[1]/'skills/engineering-workflow'
        s=(root/'SKILL.md').read_text()
        front=s.split('---',2)[1]
        values=dict(line.split(': ',1) for line in front.strip().splitlines())
        self.assertEqual({'name','description'},set(values))
        self.assertEqual('engineering-workflow',values['name'])
        for phase in ('planning','execution','recovery','routing'):
            self.assertTrue((root/'references'/phase/'WORKFLOW.md').exists())

class MultiHostTests(unittest.TestCase):
    def test_host_paths(self):
        for host,folder in [('codex','.agents'),('cursor','.cursor'),('claude','.claude')]:
            with self.subTest(host=host), tempfile.TemporaryDirectory() as d:
                install(d,host=host)
                self.assertTrue((Path(d)/folder/'skills/engineering-workflow/SKILL.md').exists())
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
    def test_unknown_host(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError): install(d,host='unknown')

if __name__=='__main__': unittest.main()
