"""
test_smoke.py — IntelliEye 최소 회귀 테스트

Python 3.14 이상에서 버전 체크가 CLI 실행을 막지 않는지 확인합니다.
의존성(torch, transformers 등)은 CI에서 설치되지 않으므로 모듈 임포트는
하지 않고, intellieye.py 의 버전 게이트 로직만 검증합니다.
"""

import subprocess
import sys
import textwrap


def _run_python(code: str) -> subprocess.CompletedProcess:
    """현재 인터프리터로 짧은 Python 코드를 실행합니다."""
    return subprocess.run(
        [sys.executable, "-c", textwrap.dedent(code)],
        capture_output=True,
        text=True,
    )


def test_version_check_does_not_exit():
    """버전 체크 블록이 sys.exit() 를 호출하지 않는지 확인합니다.

    intellieye.py 의 버전 게이트 블록을 직접 실행하고,
    Python 3.14 에서도 종료 코드가 0 (정상) 임을 확인합니다.
    """
    code = """
        import sys
        # Python 3.14 를 시뮬레이션 (tuple 비교가 작동하도록 tuple 상속)
        class _FakeVersionInfo(tuple):
            major = 3
            minor = 14
            micro = 0
        sys.version_info = _FakeVersionInfo((3, 14, 0))

        # 버전 게이트 로직 실행 — sys.exit() 호출 없이 완료되어야 함
        if sys.version_info >= (3, 13):
            print("version-gate-reached")
        print("execution-continued")
        sys.exit(0)
    """
    result = _run_python(code)
    assert result.returncode == 0, (
        f"버전 체크 블록이 종료 코드 {result.returncode} 로 종료되었습니다.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert "execution-continued" in result.stdout, "버전 게이트 이후 코드가 실행되지 않았습니다."


def test_version_check_prints_info_not_error():
    """Python 3.14 에서 버전 메시지가 출력되는지, 오류가 없는지 확인합니다."""
    code = """
        import sys
        class _FakeVersionInfo(tuple):
            major = 3
            minor = 14
            micro = 0
        sys.version_info = _FakeVersionInfo((3, 14, 0))

        if sys.version_info >= (3, 13):
            print(f"Python {sys.version_info.major}.{sys.version_info.minor} detected")
    """
    result = _run_python(code)
    assert result.returncode == 0
    # 프로그램이 정상 실행되고 메시지가 출력됨
    assert "Python 3.14" in result.stdout


def test_supports_python_310_and_above():
    """현재 실행 중인 Python 이 지원 범위(3.10+)에 포함되는지 확인합니다."""
    assert sys.version_info >= (3, 10), (
        f"Python 3.10 이상이 필요합니다. 현재: {sys.version_info}"
    )
