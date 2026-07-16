"""compile.compile_md 테스트 — 도메인 무관(모든 카테고리 출력), 즐겨찾기 우선, 비활성 제외.

실행: python3 tests/test_compile.py
"""
import os
import sys

SCRIPTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "plugins", "work-like-me", "scripts")
sys.path.insert(0, SCRIPTS)
import compile as compiler  # noqa: E402


DATA = {
    "meta": {"lang": "ko", "identity": "리서치 중심 기획자", "priority_order": ["사용자가치", "근거"]},
    "rules": [
        {"id": "a", "category": "전략", "title": "가설먼저", "text": "가설부터", "favorite": True},
        {"id": "b", "category": "리서치", "title": "1차자료", "text": "원자료 확인"},
        {"id": "c", "category": "소통", "title": "존댓말", "text": "담백하게"},
        {"id": "d", "category": "전략", "title": "비활성", "text": "빠짐", "enabled": False},
    ],
}


def test_header_and_identity():
    md = compiler.compile_md(DATA)
    assert "# 시스템 프롬프트 — 나의 페르소나" in md
    assert "리서치 중심 기획자" in md
    assert "개발" not in md.splitlines()[0]      # 개발 종속 헤더가 아님


def test_all_categories_present():
    md = compiler.compile_md(DATA)
    for cat in ("전략", "리서치", "소통"):        # 비개발 카테고리도 전부 출력
        assert f"## " in md and cat in md, cat


def test_disabled_excluded():
    md = compiler.compile_md(DATA)
    assert "비활성" not in md


def test_favorite_marked():
    md = compiler.compile_md(DATA)
    assert "★" in md                              # 즐겨찾기 표시


def test_priority_order():
    md = compiler.compile_md(DATA)
    assert "사용자가치" in md and "근거" in md


def test_lang_default_en_when_missing():
    # meta.lang 없으면 크롬은 영어(공개 기본)
    md = compiler.compile_md({"meta": {"identity": "x"}, "rules": []})
    assert "# System Prompt — My Persona" in md
    assert "## 0. Identity" in md


def test_lang_ko_when_set():
    data = {"meta": {"lang": "ko", "identity": "x"}, "rules": []}
    md = compiler.compile_md(data)
    assert "# 시스템 프롬프트 — 나의 페르소나" in md
    assert "## 0. 너의 정체성" in md


def test_rule_content_language_independent_of_chrome():
    # lang=en이어도 규칙 내용(한국어)은 그대로 보존
    data = {"meta": {"lang": "en"}, "rules": [
        {"id": "x", "category": "전략", "title": "가설먼저", "text": "가설부터"}]}
    md = compiler.compile_md(data)
    assert "전략" in md and "가설먼저" in md and "가설부터" in md


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
