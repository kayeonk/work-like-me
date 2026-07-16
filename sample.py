#!/usr/bin/env python3
"""추출된 발화(.msgs.jsonl)에서 LLM 귀납용 대표 샘플을 뽑는다.

판단·가치가 드러나는 '중간~긴' 발화를 우선하고, 파일 전체에 고르게 분포하도록
균등 간격 샘플링한다. 무작위 대신 결정적(재현 가능) 방식.
"""
import json, os, argparse


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp",
                    default=os.path.expanduser("~/.claude/skills/my-persona/.msgs.jsonl"))
    ap.add_argument("--n", type=int, default=150)
    ap.add_argument("--min", type=int, default=8)
    ap.add_argument("--max", type=int, default=500)
    a = ap.parse_args()

    rows = [json.loads(l) for l in open(a.inp, encoding="utf-8")]
    # 판단이 드러나는 길이대만
    cand = [r for r in rows if a.min <= len(r["t"]) <= a.max]
    if not cand:
        cand = rows

    if len(cand) <= a.n:
        pick = cand
    else:
        step = len(cand) / a.n
        pick = [cand[int(i * step)] for i in range(a.n)]

    print(f"# 대표 샘플 {len(pick)}건 (전체 {len(rows)}건 중) — 이 사람의 판단·말투 패턴을 귀납하라\n")
    for i, r in enumerate(pick, 1):
        print(f"{i:3d}. [{r['src']}] {r['t']}")


if __name__ == "__main__":
    main()
