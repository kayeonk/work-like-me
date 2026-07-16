#!/usr/bin/env python3
"""rules.json → 지시형 시스템 프롬프트(마크다운) 컴파일.

- enabled=true 규칙만 포함 (disabled = 일시정지 = 제외).
- 카테고리별로 그룹, 각 카테고리 안에서 favorite(★) 우선 정렬.
- meta.identity / meta.priority_order를 상단에 배치.
- 결과는 stdout 또는 --out 경로.
"""
import argparse, json, os

# 카테고리 표시 순서와 제목
CAT_ORDER = [
    ("절대규칙", "절대 규칙 (하지 마라 / 반드시)"),
    ("가치관", "가치관 — 무엇을 우선하는가"),
    ("판단", "판단 규율"),
    ("검증", "검증 & 완료 보고"),
    ("라이브러리", "라이브러리 도입"),
    ("git", "Git 워크플로우"),
    ("소통", "소통 스타일"),
    ("상황별", "상황별 규칙 (트리거 → 행동)"),
]


def compile_md(data):
    rules = [r for r in data["rules"] if r.get("enabled", True)]
    meta = data.get("meta", {})
    out = []
    out.append("# 시스템 프롬프트 — 개발 협업 페르소나")
    out.append("")
    out.append("> my-persona 스킬이 로컬 AI 세션 기록에서 추출·컴파일한 지시형 규칙이다.")
    out.append("> 너는 아래 규칙에 따라 판단하고 응답한다. (★ = 즐겨찾기 = 특히 중요)")
    out.append("")

    if meta.get("identity"):
        out.append("## 0. 너의 정체성")
        out.append("")
        out.append(meta["identity"])
        out.append("")

    if meta.get("priority_order"):
        out.append("## 1. 최우선 원칙 — 충돌하면 이 순서로 (위쪽이 이긴다)")
        out.append("")
        for i, p in enumerate(meta["priority_order"], 1):
            out.append(f"{i}. **{p}**")
        out.append("")

    n = 2
    by_cat = {}
    for r in rules:
        by_cat.setdefault(r["category"], []).append(r)

    for cat, title in CAT_ORDER:
        items = by_cat.get(cat)
        if not items:
            continue
        # favorite 우선, 그다음 원래 순서
        items = sorted(items, key=lambda r: (not r.get("favorite", False)))
        out.append(f"## {n}. {title}")
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
        out.append(f"## {n}. 부록 — 근거(발화 빈도)")
        out.append("")
        out.append("| 규칙 | 근거 발화 수 |")
        out.append("|------|------|")
        for title, cnt in sorted(ev, key=lambda x: -x[1]):
            out.append(f"| {title} | {cnt} |")
        out.append("")

    return "\n".join(out).rstrip() + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rules", default=os.path.expanduser("~/.claude/skills/my-persona/rules.json"))
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    data = json.load(open(a.rules, encoding="utf-8"))
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
