import ctypes
import json
import os
from pathlib import Path
import signal
import sys
import tempfile
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from riff_core import diagnostic_runner, reports


class ReportTests(unittest.TestCase):
    def template(self, kind):
        return json.loads((Path(__file__).resolve().parents[1] / "templates" / (kind + ".json")).read_text())

    def test_draft_templates(self):
        for kind in reports.KINDS:
            with self.subTest(kind=kind):
                self.assertEqual([], reports.validate(self.template(kind)))

    def test_inconclusive_research_is_honest_complete_output(self):
        p = self.template("research")
        p.update(status="inconclusive", question="Can X be proven?", scope="Local source",
                 success_criteria="Evidence sufficient to prove X", limits="No live service access",
                 conclusion="Insufficient evidence", next_action="Obtain service logs",
                 claims=[dict(id="CL1", text="X remains unknown", classification="unresolved", sources=[])])
        self.assertEqual([], reports.validate(p))
        p["claims"][0]["classification"] = "observed"
        self.assertTrue(any("requires a source" in e for e in reports.validate(p)))

    def test_completed_diagnosis_needs_causal_evidence(self):
        p = self.template("debug")
        p.update(status="complete", expected="Zero exit", actual="Nonzero exit", next_action="Plan fix")
        self.assertTrue(any("causal_evidence" in e for e in reports.validate(p)))
        p["evidence"] = [dict(id="E1", source="reports/reproduction.txt", revision="sha256:test")]
        p["causal_evidence"] = ["E1"]
        self.assertEqual([], reports.validate(p))
        p["causal_evidence"] = ["missing"]
        self.assertTrue(any("unknown causal_evidence" in e for e in reports.validate(p)))

    def test_replan_revision_and_malformed_values(self):
        p = self.template("replan")
        p["target_revision"] = p["baseline_revision"]
        self.assertTrue(reports.validate(p))
        for malformed in (None, [], {"schema_version": True}, {"kind": "debug", "evidence": None}):
            self.assertTrue(reports.validate(malformed))


def alive(pid):
    if os.name == "nt":
        from ctypes import wintypes
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = kernel.OpenProcess(0x1000, False, pid)
        if not handle:
            return False
        try:
            code = wintypes.DWORD()
            return bool(kernel.GetExitCodeProcess(handle, ctypes.byref(code))) and code.value == 259
        finally:
            kernel.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        stat = Path("/proc") / str(pid) / "stat"
        return not stat.exists() or stat.read_text().split(") ", 1)[1][0] != "Z"
    except ProcessLookupError:
        return False


class DiagnosticTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.product = self.root / "product"
        self.product.mkdir()
        self.source = self.product / "source.py"
        self.source.write_text("unchanged")
        self.cwd = self.root / "reproduction"
        self.cwd.mkdir()

    def test_success_failure_and_no_product_change(self):
        result = diagnostic_runner.run([sys.executable, "-c", "print('observed'); raise SystemExit(3)"], self.cwd)
        self.assertEqual(3, result["exit_code"])
        self.assertIn("observed", result["stdout"])
        self.assertFalse(result["timed_out"])
        self.assertEqual("unchanged", self.source.read_text())

    def test_timeout_and_total_budget(self):
        result = diagnostic_runner.run([sys.executable, "-c", "import time; time.sleep(30)"], self.cwd,
                                       command_timeout=0.25)
        self.assertTrue(result["timed_out"])
        self.assertLess(result["duration_seconds"], 10)
        with self.assertRaisesRegex(ValueError, "exhausted"):
            diagnostic_runner.run([sys.executable, "-c", "pass"], self.cwd, elapsed=300)

    def test_successful_parent_does_not_leave_child(self):
        script = ("import subprocess,sys,pathlib; p=subprocess.Popen([sys.executable,'-c',"
                  "'import time; time.sleep(30)']); pathlib.Path('child.pid').write_text(str(p.pid))")
        result = diagnostic_runner.run([sys.executable, "-c", script], self.cwd)
        self.assertEqual(0, result["exit_code"])
        pid = int((self.cwd / "child.pid").read_text())
        try:
            deadline = time.monotonic() + 2
            while alive(pid) and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertFalse(alive(pid), "diagnostic descendant survived completed parent")
        finally:
            if alive(pid):
                os.kill(pid, signal.SIGTERM)


if __name__ == "__main__":
    unittest.main()
