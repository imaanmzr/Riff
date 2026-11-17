"""Explicit bounded diagnostic execution in a caller-provided isolated directory.

This helper is not a sandbox. Inspect commands before invoking it. It never reads
commands from reports and does not authorize product changes or external effects.
"""
import ctypes
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time


class _WindowsJob:
    """Kill-on-close job, assigned before the wrapper may start user commands."""
    def __init__(self, process):
        from ctypes import wintypes
        size = ctypes.c_size_t
        class Basic(ctypes.Structure):
            _fields_ = [("PerProcessUserTimeLimit", ctypes.c_longlong),
                        ("PerJobUserTimeLimit", ctypes.c_longlong), ("LimitFlags", wintypes.DWORD),
                        ("MinimumWorkingSetSize", size), ("MaximumWorkingSetSize", size),
                        ("ActiveProcessLimit", wintypes.DWORD), ("Affinity", size),
                        ("PriorityClass", wintypes.DWORD), ("SchedulingClass", wintypes.DWORD)]
        class IO(ctypes.Structure):
            _fields_ = [(name, ctypes.c_ulonglong) for name in
                        ("ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
                         "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]
        class Extended(ctypes.Structure):
            _fields_ = [("BasicLimitInformation", Basic), ("IoInfo", IO),
                        ("ProcessMemoryLimit", size), ("JobMemoryLimit", size),
                        ("PeakProcessMemoryUsed", size), ("PeakJobMemoryUsed", size)]
        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        self.kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        self.kernel.CreateJobObjectW.restype = wintypes.HANDLE
        self.kernel.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
        self.kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        self.kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        self.handle = self.kernel.CreateJobObjectW(None, None)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        limits = Extended()
        limits.BasicLimitInformation.LimitFlags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        try:
            if not self.kernel.SetInformationJobObject(self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
                raise ctypes.WinError(ctypes.get_last_error())
            if not self.kernel.AssignProcessToJobObject(self.handle, int(process._handle)):
                raise ctypes.WinError(ctypes.get_last_error())
        except BaseException:
            self.close()
            raise

    def close(self):
        if self.handle:
            from ctypes import wintypes
            class Accounting(ctypes.Structure):
                _fields_ = [(name, ctypes.c_longlong) for name in
                            ("TotalUserTime", "TotalKernelTime", "ThisPeriodTotalUserTime", "ThisPeriodTotalKernelTime")] + [
                            (name, wintypes.DWORD) for name in
                            ("TotalPageFaultCount", "TotalProcesses", "ActiveProcesses", "TotalTerminatedProcesses")]
            self.kernel.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
            self.kernel.QueryInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p,
                                                              wintypes.DWORD, ctypes.c_void_p]
            try:
                if not self.kernel.TerminateJobObject(self.handle, 1):
                    raise ctypes.WinError(ctypes.get_last_error())
                deadline = time.monotonic() + 5
                while True:
                    state = Accounting()
                    if not self.kernel.QueryInformationJobObject(self.handle, 1, ctypes.byref(state), ctypes.sizeof(state), None):
                        raise ctypes.WinError(ctypes.get_last_error())
                    if state.ActiveProcesses == 0:
                        break
                    if time.monotonic() >= deadline:
                        raise RuntimeError("Could not verify diagnostic process-tree cleanup")
                    time.sleep(0.01)
            finally:
                self.kernel.CloseHandle(self.handle)
                self.handle = None


def _positive(value, name):
    if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
        raise ValueError(name + " must be a finite positive number")


def run(command, cwd, command_timeout=60, total_timeout=300, elapsed=0):
    """Run argv once; close its process tree on success, failure, or timeout.

    Pass accumulated duration_seconds as elapsed for a multi-command session.
    The caller remains responsible for isolation, side-effect inspection, and
    persisting the actual result. Output captures at most 1 MiB per stream.
    """
    if not isinstance(command, list) or not command or any(not isinstance(x, str) or not x for x in command):
        raise ValueError("command must be a nonempty argv array")
    for name, value in (("command_timeout", command_timeout), ("total_timeout", total_timeout)):
        _positive(value, name)
    if type(elapsed) not in (int, float) or not math.isfinite(elapsed) or elapsed < 0:
        raise ValueError("elapsed must be finite and nonnegative")
    remaining = total_timeout - elapsed
    if remaining <= 0:
        raise ValueError("Diagnostic total execution budget exhausted")
    directory = Path(cwd).resolve(strict=True)
    if not directory.is_dir():
        raise ValueError("cwd must be an isolated directory")
    # Isolated Python ignores user site hooks and waits until assigned to a job.
    wrapper = ("import subprocess,sys; "
               "token=sys.stdin.buffer.read(1); "
               "sys.exit(subprocess.call(sys.argv[1:], stdin=subprocess.DEVNULL) if token==b'1' else 125)")
    kwargs = dict(cwd=directory, stdin=subprocess.PIPE)
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    began = time.monotonic()
    timed_out = False
    job = None
    process = None
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        try:
            process = subprocess.Popen([sys.executable, "-I", "-S", "-c", wrapper, *command],
                                       stdout=stdout, stderr=stderr, **kwargs)
            if os.name == "nt":
                job = _WindowsJob(process)
            process.stdin.write(b"1")
            process.stdin.close()
            try:
                process.wait(timeout=min(command_timeout, remaining))
            except subprocess.TimeoutExpired:
                timed_out = True
        finally:
            try:
                if job is not None:
                    job.close()
                elif process is not None and os.name != "nt":
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
            finally:
                if process is not None:
                    if process.poll() is None:
                        process.kill()
                    process.wait(timeout=10)
                    if process.stdin and not process.stdin.closed:
                        process.stdin.close()
        output = {}
        for name, stream in (("stdout", stdout), ("stderr", stderr)):
            stream.seek(0)
            data = stream.read(1024 * 1024 + 1)
            output[name] = data[:1024 * 1024].decode("utf-8", errors="replace")
            output[name + "_truncated"] = len(data) > 1024 * 1024
    return dict(command=list(command), cwd=str(directory), exit_code=process.returncode,
                timed_out=timed_out, duration_seconds=time.monotonic() - began,
                cleanup="process tree terminated", **output)
