"""install.splice 멱등성/블록 경계 테스트 (무의존성).

실행: python3 tests/test_install.py
"""
import os
import sys

SCRIPTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "plugins", "work-like-me", "scripts")
sys.path.insert(0, SCRIPTS)
import install  # noqa: E402


def test_block_into_empty():
    block = install.build_block("규칙 본문")
    out = install.splice("", block)
    assert out == block
    assert install.START in out and install.END in out


def test_preserves_existing_content():
    existing = "# 내 CLAUDE.md\n\n손으로 쓴 규칙\n"
    out = install.splice(existing, install.build_block("생성된 규칙"))
    assert "손으로 쓴 규칙" in out          # 기존 내용 보존
    assert "생성된 규칙" in out


def test_replaces_not_duplicates():
    existing = "앞부분\n\n" + install.build_block("v1") + "\n뒷부분\n"
    once = install.splice(existing, install.build_block("v2"))
    twice = install.splice(once, install.build_block("v2"))
    assert once.count(install.START) == 1      # 블록은 항상 하나
    assert once.count(install.END) == 1
    assert "v1" not in once                     # 이전 블록 교체됨
    assert "v2" in once
    assert "앞부분" in once and "뒷부분" in once
    assert twice == once                        # 멱등: 다시 넣어도 동일


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"  PASS {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL {fn.__name__}: {e}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
