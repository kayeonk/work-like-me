"""extract.redact 시크릿/PII 마스킹 테스트 (무의존성, pytest 없이도 실행 가능).

실행: python3 tests/test_redact.py   또는   python3 -m pytest tests/
"""
import os
import sys

SCRIPTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "plugins", "work-like-me", "scripts")
sys.path.insert(0, SCRIPTS)
import extract  # noqa: E402


def test_email():
    assert "<email>" in extract.redact("연락은 foo.bar+x@example.co.kr 로")
    assert "example.co.kr" not in extract.redact("foo@example.co.kr")


def test_openai_style_key():
    assert extract.redact("key sk-abcdefghijklmnop1234") == "key <key>"


def test_github_tokens():
    assert "<token>" in extract.redact("ghp_" + "a" * 30)
    assert "<token>" in extract.redact("github_pat_" + "A1b2" * 8)


def test_slack_and_google():
    assert "<token>" in extract.redact("xoxb-123456789012-abcdefABCDEF")
    assert "<key>" in extract.redact("AIza" + "B" * 33)


def test_aws_and_jwt():
    assert "<aws-key>" in extract.redact("AKIAABCDEFGH1234567")
    jwt = "eyJABCDEFGH.eyJ12345678.SflKxwRJSMeKKF"
    assert "<jwt>" in extract.redact(jwt)


def test_bearer():
    assert extract.redact("Authorization: Bearer abcdef123456xyz").endswith("Bearer <token>")


def test_env_secret_value_masked_key_kept():
    out = extract.redact("API_KEY=sup3rs3cr3tvalue")
    assert "API_KEY=<secret>" in out
    assert "sup3rs3cr3tvalue" not in out


def test_env_plain_key_not_over_redacted():
    # 시크릿성 키가 아니면 값 보존(오탐 방지)
    out = extract.redact("count=12345678")
    assert "<secret>" not in out


def test_hash():
    assert "<hash>" in extract.redact("commit " + "a1b2c3d4" * 5)


def test_home_paths_cross_os():
    assert extract.redact("/Users/alice/.claude/x") == "<home>/.claude/x"
    assert extract.redact("/home/bob/project") == "<home>/project"
    assert extract.redact(r"C:\Users\carol\repo") == r"<home>\repo"


def test_current_home_dynamic():
    sample = os.path.join(extract.HOME, ".codex", "sessions")
    assert extract.HOME not in extract.redact(sample)
    assert "<home>" in extract.redact(sample)


def test_ip():
    assert "<ip>" in extract.redact("서버 10.0.12.34 에서")


def test_plain_text_untouched():
    s = "이건 그냥 한국어 문장이다. 코드 리뷰 먼저 하자."
    assert extract.redact(s) == s


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
