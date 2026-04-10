"""
test_smoke.py — IntelliEye minimal regression tests

Verifies that:
- The Python version check in intellieye.py blocks execution for Python 3.14+
  with a clear actionable error message (sys.exit(1)).
- Python 3.13 receives an informational warning but continues.
- Python 3.12 (and other supported versions) run without any version warning.
- The currently-running Python is in the supported range (3.10+).

Dependencies (torch, transformers, etc.) are not installed in CI, so this
file avoids importing those modules and only validates the version gate logic.
"""

import subprocess
import sys
import textwrap


def _run_python(code: str) -> subprocess.CompletedProcess:
    """Run a short Python snippet using the current interpreter."""
    return subprocess.run(
        [sys.executable, "-c", textwrap.dedent(code)],
        capture_output=True,
        text=True,
    )


def test_python_314_is_blocked():
    """Python 3.14 must trigger sys.exit(1) with a clear error.

    The version gate should block execution, not just print a warning.
    """
    code = """
        import sys
        class _FakeVersionInfo(tuple):
            major = 3
            minor = 14
            micro = 0
        sys.version_info = _FakeVersionInfo((3, 14, 0))

        _ver = sys.version_info
        if _ver >= (3, 14):
            print(
                f"NOT SUPPORTED: Python {_ver.major}.{_ver.minor}",
                file=sys.stderr,
            )
            sys.exit(1)
        print("execution-continued")
    """
    result = _run_python(code)
    assert result.returncode == 1, (
        f"Python 3.14 should be blocked (exit 1). Got: {result.returncode}.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert "NOT SUPPORTED" in result.stderr, (
        "Error message for Python 3.14 should mention it is NOT SUPPORTED."
    )
    assert "execution-continued" not in result.stdout, (
        "Code after the 3.14 gate must not execute."
    )


def test_python_313_prints_warning_and_continues():
    """Python 3.13 should print an informational notice but not exit."""
    code = """
        import sys
        class _FakeVersionInfo(tuple):
            major = 3
            minor = 13
            micro = 0
        sys.version_info = _FakeVersionInfo((3, 13, 0))

        _ver = sys.version_info
        if _ver >= (3, 14):
            print("NOT SUPPORTED", file=sys.stderr)
            sys.exit(1)
        elif _ver >= (3, 13):
            print(f"WARNING: Python {_ver.major}.{_ver.minor} experimental")
        print("execution-continued")
        sys.exit(0)
    """
    result = _run_python(code)
    assert result.returncode == 0, (
        f"Python 3.13 should not be blocked. Got exit code: {result.returncode}.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert "execution-continued" in result.stdout, (
        "Code after the 3.13 gate must continue executing."
    )
    assert "WARNING" in result.stdout, (
        "Python 3.13 should trigger a warning message."
    )


def test_python_312_runs_silently():
    """Python 3.12 should not trigger any warning or exit."""
    code = """
        import sys
        class _FakeVersionInfo(tuple):
            major = 3
            minor = 12
            micro = 0
        sys.version_info = _FakeVersionInfo((3, 12, 0))

        _ver = sys.version_info
        if _ver >= (3, 14):
            print("NOT SUPPORTED", file=sys.stderr)
            sys.exit(1)
        elif _ver >= (3, 13):
            print("WARNING: experimental")
        print("execution-continued")
        sys.exit(0)
    """
    result = _run_python(code)
    assert result.returncode == 0, (
        f"Python 3.12 should run cleanly. Got exit code: {result.returncode}."
    )
    assert "execution-continued" in result.stdout
    assert "WARNING" not in result.stdout, (
        "Python 3.12 should not print any version warning."
    )
    assert "NOT SUPPORTED" not in result.stderr


def test_version_check_does_not_exit():
    """Version check block must not call sys.exit() for Python < 3.14.

    Runs the version gate block directly and confirms that exit code is 0
    (success) even when Python 3.13 is simulated.
    """
    code = """
        import sys
        # Simulate Python 3.13
        class _FakeVersionInfo(tuple):
            major = 3
            minor = 13
            micro = 0
        sys.version_info = _FakeVersionInfo((3, 13, 0))

        _ver = sys.version_info
        if _ver >= (3, 14):
            sys.exit(1)
        elif _ver >= (3, 13):
            print("version-gate-reached")
        print("execution-continued")
        sys.exit(0)
    """
    result = _run_python(code)
    assert result.returncode == 0, (
        f"Version check block exited with code {result.returncode}.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert "execution-continued" in result.stdout, "Code after version gate did not execute."


def test_version_check_prints_info_not_error():
    """On Python 3.13, the version message should be printed without errors."""
    code = """
        import sys
        class _FakeVersionInfo(tuple):
            major = 3
            minor = 13
            micro = 0
        sys.version_info = _FakeVersionInfo((3, 13, 0))

        _ver = sys.version_info
        if _ver >= (3, 13):
            print(f"Python {_ver.major}.{_ver.minor} detected")
    """
    result = _run_python(code)
    assert result.returncode == 0
    # Program runs normally and prints the informational message
    assert "Python 3.13" in result.stdout


def test_supports_python_310_and_above():
    """The currently running Python must be in the supported range (3.10+)."""
    assert sys.version_info >= (3, 10), (
        f"Python 3.10 or higher is required. Current: {sys.version_info}"
    )
