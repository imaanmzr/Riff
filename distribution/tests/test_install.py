import json
import re
import sys
import tempfile
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from install import hashes, install

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / 'distribution/skills/riff/references'
GUIDES = (
    'planning/INTERVIEW.md',
    'planning/DESIGN.md',
    'planning/DOCUMENTATION.md',
    'execution/IMPLEMENTATION.md',
    'execution/REVIEW.md',
    'planning/DEBUG.md',
)

class InstallTests(unittest.TestCase):
    def test_install_preserves_project_and_updates(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/'AGENTS.md').write_text('keep project rules')
            install(root)
            self.assertEqual('docs/riff', json.loads((root / '.riff/project.json').read_text())['artifacts_directory'])
            skill=root/'.agents/skills/riff'
            self.assertTrue((skill/'SKILL.md').exists())
            self.assertTrue((skill/'references/routing/router.py').exists())
            self.assertFalse((root / '.engineering-workflow').exists())
            config=root/'.riff/project.json'; config.write_text('{"custom":true}')
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
    def test_legacy_settings_are_preserved_on_install_and_update(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            settings = project / '.engineering-workflow'
            (settings / 'hosts').mkdir(parents=True)
            originals = {'project.json': b'{"artifacts_directory":"notes/tasks","custom":true}',
                         'routing-codex.json': b'{"profiles":{"coding":"custom-model"}}',
                         'hosts/codex.json': b'{"custom_capability":true}'}
            for name, content in originals.items():
                (settings / name).write_bytes(content)
            install(project)
            install(project, update=True)
            self.assertFalse((project / '.riff').exists())
            for name, content in originals.items():
                self.assertEqual(content, (settings / name).read_bytes())

    def test_duplicate_settings_are_rejected_before_installing(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            for name in ('.riff', '.engineering-workflow'):
                settings = project / name
                settings.mkdir()
                (settings / 'project.json').write_bytes(b'{"preserve":true}')
            with self.assertRaisesRegex(ValueError, 'Both .riff and .engineering-workflow'):
                install(project)
            self.assertFalse((project / '.agents').exists())
            for name in ('.riff', '.engineering-workflow'):
                self.assertEqual(b'{"preserve":true}', (project / name / 'project.json').read_bytes())
    def test_symlink_refusal(self):
        for name in ('.agents', '.riff', '.engineering-workflow'):
            with self.subTest(path=name), tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as other:
                try:
                    (Path(d) / name).symlink_to(other, target_is_directory=True)
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
        for target in re.findall(r'\]\(([^)]+)\)', s):
            if '://' in target:
                continue
            with self.subTest(link=target):
                self.assertTrue((root / target.split('#', 1)[0]).is_file())

    def test_bundled_workflow_references_match_source(self):
        for path in (*GUIDES, 'planning/WORKFLOW.md', 'execution/WORKFLOW.md',
                     'planning/tests/scenarios.md'):
            with self.subTest(path=path):
                self.assertEqual((REPO / path).read_bytes(), (BUNDLE / path).read_bytes())

    def test_update_preserves_locally_edited_guide(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            install(root)
            guide = root / '.agents/skills/riff/references' / GUIDES[0]
            guide.write_text('local design instructions')
            with self.assertRaisesRegex(ValueError, 'Installed files changed'):
                install(root, update=True)
            self.assertEqual(guide.read_text(), 'local design instructions')

class MultiHostTests(unittest.TestCase):
    def test_host_paths(self):
        for host,folder in [('codex','.agents'),('cursor','.cursor'),('claude','.claude'),
                            ('vscode','.github')]:
            with self.subTest(host=host), tempfile.TemporaryDirectory() as d:
                project = Path(d)
                skill = project / folder / 'skills/riff'
                install(project, host=host)
                self.assertTrue((skill / 'SKILL.md').exists())
                for path in GUIDES:
                    guide = skill / 'references' / path
                    self.assertEqual(guide.read_bytes(), (BUNDLE / path).read_bytes())
                    guide.unlink()

                # Model an older managed bundle whose manifest predates the guides.
                metadata_file = skill / '.installation.json'
                metadata = json.loads(metadata_file.read_text())
                metadata['hashes'] = hashes(skill)
                metadata_file.write_text(json.dumps(metadata))
                settings = project / '.riff/project.json'
                settings.write_text('{"custom": true}')
                install(project, update=True, host=host)
                self.assertEqual(settings.read_text(), '{"custom": true}')
                for path in GUIDES:
                    self.assertEqual((skill / 'references' / path).read_bytes(),
                                     (BUNDLE / path).read_bytes())
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
            config = project / '.riff/project.json'
            config.write_text('{"custom": true}')

            install(project, update=True)

            self.assertFalse(legacy.exists())
            self.assertIn('name: riff', (skill / 'SKILL.md').read_text())
            self.assertEqual('{"custom": true}', config.read_text())

    def test_unknown_host(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError): install(d,host='unknown')

if __name__=='__main__': unittest.main()
