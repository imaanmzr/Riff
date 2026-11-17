import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from riff_core import records, storage


class RecordsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.task = self.root / "task"
        self.task.mkdir()
        (self.task / "plan.md").write_text("# Goal\nA reviewed behavior.\n", encoding="utf-8")
        (self.root / "src.py").write_text("pass\n")
        self.context = dict(project=self.root, task_dir=self.task, effective_behavior={"checks": ["test"]})

    def plan(self):
        p = dict(records.new_fields(), route="standard", status="READY", revision=1,
                 source_revision="baseline", requirements=["R1"], tasks=[dict(
                     id="T1", dependencies=[], requirements=["R1"],
                     **{key: "specified" for key in ("objective", "inputs", "scope", "outputs", "owner", "capability", "reviewer", "verification")})])
        p["requirement_details"] = [dict(id="R1", description="Useful behavior", acceptance_checks=["C1"])]
        p["acceptance_checks"] = [dict(id="C1", requirements=["R1"], procedure="Run test", expected="Pass")]
        p["source_manifest"] = {"src.py": hashlib.sha256((self.root / "src.py").read_bytes()).hexdigest()}
        p["behavior_config"] = self.context["effective_behavior"]
        p["config_digest"] = records.digest(p["behavior_config"])
        p["authored_digest"] = records.authored_digest(self.task, p)
        p["reviews"] = [dict(revision=1, source_revision="baseline", verdict="pass", reviewer="review-session", independent=True,
                             authored_digest=p["authored_digest"], config_digest=p["config_digest"], plan_digest=records.plan_digest(p))]
        return p

    def test_ready_live_and_no_mutation(self):
        p = self.plan()
        before = copy.deepcopy(p)
        self.assertEqual([], records.validate(p, self.context))
        self.assertEqual(before, p)
        self.assertTrue(records.validate(p))

    def test_prose_edit_without_revision_blocks(self):
        p = self.plan()
        (self.task / "plan.md").write_text("A different contract.")
        self.assertTrue(any("Authored" in e for e in records.validate(p, self.context)))

    def test_config_change_blocks(self):
        p = self.plan()
        context = dict(self.context, effective_behavior={"checks": []})
        self.assertTrue(any("configuration changed" in e for e in records.validate(p, context)))

    def test_changed_source_or_missing_manifest_blocks(self):
        p = self.plan()
        (self.root / "src.py").write_text("changed")
        self.assertTrue(any("Source changed" in e for e in records.validate(p, self.context)))
        p["source_manifest"] = {}
        self.assertTrue(any("freshness unknown" in e for e in records.validate(p, self.context)))

    def test_review_must_bind_all_fields_together(self):
        p = self.plan()
        good = p["reviews"][0]
        p["reviews"] = [dict(good, authored_digest="wrong"), dict(good, config_digest="wrong")]
        self.assertIn("Missing current qualifying review", records.validate(p, self.context))

    def test_simulated_review_rejected(self):
        p = self.plan()
        p["reviews"][0]["simulated"] = True
        self.assertIn("Missing current qualifying review", records.validate(p, self.context))

    def test_generated_content_verified(self):
        p = self.plan()
        path = self.task / "plan.md"
        original = path.read_text()
        section = records.generated_sections(p)["tasks"]
        path.write_text(original + "<!-- riff:generated:tasks -->\n" + section + "\n<!-- /riff:generated:tasks -->")
        self.assertEqual(p["authored_digest"], records.authored_digest(self.task, p))
        path.write_text(path.read_text().replace("specified", "invented"))
        with self.assertRaisesRegex(ValueError, "differs"):
            records.authored_digest(self.task, p)

    def test_malformed_nested_and_duplicate_markers(self):
        p = self.plan()
        for text in ("<!-- riff:generated:tasks-->", "<!-- /riff:generated:tasks -->",
                     "<!-- riff:generated:tasks --><!-- riff:generated:graph -->"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                records.authored_text(text, p)

    def test_structured_orphans_and_missing_references(self):
        p = self.plan()
        p["requirement_details"][0]["id"] = "R2"
        p["acceptance_checks"][0]["requirements"] = ["missing"]
        errors = records.validate(p, self.context)
        self.assertIn("Orphan requirement_details", errors)
        self.assertTrue(any("unknown requirements" in e for e in errors))

    def test_malformed_inputs_return_errors(self):
        for value in (None, [], {"tasks": None}, {"tasks": [{"id": []}]},
                      {"schema_version": True}, {"schema_version": 3},
                      {"schema_version": 2, "requirements": None, "reviews": None}):
            with self.subTest(value=value):
                self.assertTrue(records.validate(value))

    def test_deep_graph_no_recursion_limit(self):
        tasks = [dict(id="T" + str(i), dependencies=["T" + str(i - 1)] if i else []) for i in range(2000)]
        self.assertEqual([], records.graph_errors({"tasks": tasks}))
        tasks[0]["dependencies"] = ["T1999"]
        self.assertTrue(records.graph_errors({"tasks": tasks}))

    def test_artifact_escape_and_report_binding(self):
        p = self.plan()
        p["reviewed_artifacts"].append("../src.py")
        with self.assertRaises(ValueError):
            records.authored_digest(self.task, p)
        p["reports"] = [dict(id="REPORT1", kind="research", path="reports/research.md")]
        self.assertTrue(any("report missing" in e for e in records.validate(p, self.context)))

    def test_legacy_original_contract(self):
        p = self.plan()
        for key in (*records.new_fields(), "authored_digest", "config_digest"):
            p.pop(key, None)
        self.assertEqual([], records.validate(p))


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "plan.json"
        self.original = b'{"revision":3,"status":"READY","reviews":[{"verdict":"pass"}],"custom":{"preserve":true}}\n'
        self.path.write_bytes(self.original)

    def test_preview_then_atomic_migration(self):
        preview = storage.migrate(self.path)
        self.assertFalse(preview["applied"])
        self.assertEqual(self.original, self.path.read_bytes())
        result = storage.migrate(self.path, apply=True)
        self.assertEqual(self.original, Path(result["backup"]).read_bytes())
        p = records.load(self.path)
        self.assertEqual(4, p["revision"])
        self.assertEqual("DRAFT", p["status"])
        self.assertEqual([], p["reviews"])
        self.assertEqual({"preserve": True}, p["custom"])
        self.assertFalse(storage.migrate(self.path, apply=True)["changed"])

    def test_stale_writer_and_failed_replace(self):
        with self.assertRaisesRegex(ValueError, "Concurrent"):
            storage.atomic_json(self.path, {}, b"stale", backup=True)
        self.assertEqual(self.original, self.path.read_bytes())
        with patch("riff_core.storage.os.replace", side_effect=OSError("interrupted")):
            with self.assertRaises(OSError):
                storage.migrate(self.path, apply=True)
        self.assertEqual(self.original, self.path.read_bytes())
        self.assertEqual(self.original, next(self.path.parent.glob("*.backup-*")).read_bytes())

    def test_future_schema_untouched(self):
        self.path.write_text('{"schema_version":99}')
        with self.assertRaises(ValueError):
            storage.migrate(self.path, apply=True)
        self.assertEqual('{"schema_version":99}', self.path.read_text())


if __name__ == "__main__":
    unittest.main()
