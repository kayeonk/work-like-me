#!/usr/bin/env python3
"""rules.json → 지시형 시스템 프롬프트(마크다운) 컴파일.

- enabled=true 규칙만 포함 (disabled = 일시정지 = 제외).
- 카테고리별로 그룹, 각 카테고리 안에서 favorite(★) 우선 정렬.
- meta.identity / meta.priority_order를 상단에 배치.
- 결과는 stdout 또는 --out 경로.
"""
import argparse, json, os

DATA_DIR = os.path.expanduser(os.environ.get("WORK_LIKE_ME_DATA", "~/.work-like-me"))
RULES = os.path.join(DATA_DIR, "rules.json")

# 카테고리 정렬 힌트일 뿐. 여기 없는 카테고리도 전부 출력된다(도메인 무관, 누락 없음).
# 섹션 제목은 카테고리 이름을 그대로 쓴다 → 언어·도메인 자동 대응.
CAT_ORDER = ["절대규칙", "가치관", "판단", "검증", "소통", "상황별"]

# 프롬프트의 고정 문구(크롬)는 meta.lang(ko/en)에 맞춘다. 규칙 내용·카테고리는 데이터 언어 그대로.
STRINGS = {
    "ko": {
        "header": "# 시스템 프롬프트 — 나의 페르소나",
        "intro1": "> work-like-me 스킬이 로컬 AI 세션 기록에서 추출·컴파일한 지시형 규칙이다.",
        "intro2": "> 너는 아래 규칙에 따라 판단하고 응답한다. (★ = 즐겨찾기 = 특히 중요)",
        "identity": "너의 정체성",
        "priority": "최우선 원칙 — 충돌하면 이 순서로 (위쪽이 이긴다)",
        "appendix": "부록 — 근거(발화 빈도)",
        "tbl_rule": "규칙",
        "tbl_count": "근거 발화 수",
    },
    "en": {
        "header": "# System Prompt — My Persona",
        "intro1": "> Directive rules compiled by the work-like-me skill from local AI session logs.",
        "intro2": "> Reason and respond according to the rules below. (★ = favorite = especially important)",
        "identity": "Identity",
        "priority": "Top priorities — on conflict, higher wins",
        "appendix": "Appendix — evidence (mention frequency)",
        "tbl_rule": "Rule",
        "tbl_count": "Mentions",
    },
}


def pick_lang(meta):
    return meta.get("lang") if meta.get("lang") in STRINGS else "en"


def compile_md(data):
    rules = [r for r in data["rules"] if r.get("enabled", True)]
    meta = data.get("meta", {})
    s = STRINGS[pick_lang(meta)]
    out = []
    out.append(s["header"])
    out.append("")
    out.append(s["intro1"])
    out.append(s["intro2"])
    out.append("")

    if meta.get("identity"):
        out.append(f"## 0. {s['identity']}")
        out.append("")
        out.append(meta["identity"])
        out.append("")

    if meta.get("priority_order"):
        out.append(f"## 1. {s['priority']}")
        out.append("")
        for i, p in enumerate(meta["priority_order"], 1):
            out.append(f"{i}. **{p}**")
        out.append("")

    n = 2
    by_cat = {}
    for r in rules:
        by_cat.setdefault(r.get("category", "기타"), []).append(r)
    # 알려진 카테고리 먼저, 그다음 나머지(첫 등장 순) — 어떤 카테고리도 누락하지 않는다
    ordered = [c for c in CAT_ORDER if c in by_cat] + [c for c in by_cat if c not in CAT_ORDER]

    for cat in ordered:
        items = sorted(by_cat[cat], key=lambda r: (not r.get("favorite", False)))
        out.append(f"## {n}. {cat}")   # 카테고리 이름을 그대로 제목으로
        out.append("")
        for r in items:
            star = "★ " if r.get("favorite") else ""
            out.append(f"- {star}**{r['title']}** — {r['text']}")
        out.append("")
        n += 1

    # 근거 부록
    ev = [(r["title"], r.get("evidence", {}).get("count", 0)) for r in rules
          if r.get("evidence", {}).get("count")]
    if ev:
        out.append(f"## {n}. {s['appendix']}")
        out.append("")
        out.append(f"| {s['tbl_rule']} | {s['tbl_count']} |")
        out.append("|------|------|")
        for title, cnt in sorted(ev, key=lambda x: -x[1]):
            out.append(f"| {title} | {cnt} |")
        out.append("")

    return "\n".join(out).rstrip() + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rules", default="", help="rules.json 경로 직접 지정(기본: ~/.work-like-me/rules.json)")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    rules = a.rules or RULES
    data = json.load(open(rules, encoding="utf-8"))
    md = compile_md(data)
    if a.out:
        with open(os.path.expanduser(a.out), "w", encoding="utf-8") as w:
            w.write(md)
        enabled = sum(1 for r in data["rules"] if r.get("enabled", True))
        disabled = len(data["rules"]) - enabled
        print(f"컴파일 완료: {a.out}  (활성 {enabled} / 일시정지 {disabled})")
    else:
        print(md)


if __name__ == "__main__":
    main()
