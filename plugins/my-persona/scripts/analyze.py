#!/usr/bin/env python3
"""추출된 발화에서 판단·소통 패턴 빈도를 집계. 원문은 저장/출력하지 않고 빈도만 낸다."""
import json, re, sys, argparse, os
from collections import defaultdict

DATA_DIR = os.path.expanduser(os.environ.get("MY_PERSONA_DATA", "~/.my-persona"))

# 우선순위 축(가치관·기술판단) 중심 패턴
PATTERNS = {
    "교정_아니": [r"^\s*아니[,\s.]", r"아니\s*그게", r"안 그래", r"그거 아니"],
    "범위확장_제동": [r"굳이", r"만들지\s*마", r"빼지\s*마", r"할 필요\s*없", r"오버", r"과하", r"안 시킨"],
    "기존것_재사용": [r"기존", r"원래\s*(있|쓰)", r"그대로 (쓰|둬)", r"쓸 수 있으면", r"재사용", r"이미 있"],
    "더나은방안": [r"더 나은", r"더 좋은", r"베스트", r"best", r"제일 나", r"가장 좋", r"개선", r"최선"],
    "원인규명": [r"왜 이", r"원인", r"이유가", r"뭐 때문", r"왜 그", r"왜 안"],
    "재확인_검증": [r"맞아\??", r"다시 확인", r"확인해", r"진짜\??", r"확실", r"체크해", r"검증"],
    "실측요구": [r"브라우저", r"playwright", r"실제로", r"직접 (봐|확인|실행)", r"돌려봐", r"로그", r"콘솔", r"네트워크"],
    "코드보기": [r"코드 (좀 )?보여", r"diff", r"변경.*보여", r"뭐가 바뀌", r"보여줘"],
    "되돌려": [r"되돌", r"다시 돌", r"원복", r"롤백", r"revert", r"원래대로"],
    "완료의심": [r"진짜 (됐|다\s*됐)", r"됐어\??", r"다 됐", r"끝난 거 맞"],
    "AI티제거": [r"자연스럽", r"ai 느낌", r"사람.*(처럼|같이)", r"티 나", r"다듬", r"딱딱"],
    "요약_간결": [r"간단(히|하게)", r"요약", r"흐름만", r"짧게", r"핵심만", r"정리해"],
    "언어요구": [r"한글로", r"한국어로", r"국문", r"in english", r"영어로"],
    "리스트표": [r"리스트업", r"표로", r"목록", r"번호로", r"정리해줘"],
    "라이브러리결정": [r"라이브러리", r"패키지", r"설치", r"npm|yarn|pnpm", r"의존성", r"버전"],
    "트레이드오프": [r"영향", r"사이드이펙트|사이드 이펙트|부작용", r"리스크", r"얼마나 바꿔", r"안전", r"깨지"],
    "git": [r"커밋|commit", r"브랜치|branch", r"\bpr\b|풀리퀘|머지|merge", r"푸시|push"],
    "추천요구": [r"추천", r"어떻게 (할|해야)", r"뭐가 (나|좋)", r"의견", r"어떤 게", r"골라"],
    "테스트우선": [r"테스트 (먼저|부터)", r"tdd", r"테스트 코드", r"테스트 작성", r"커버리지"],
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default=None)
    a = ap.parse_args()
    path = a.inp or os.path.join(DATA_DIR, ".msgs.jsonl")
    msgs = [json.loads(l)["t"] for l in open(path, encoding="utf-8")]
    comp = {k: [re.compile(p, re.I) for p in v] for k, v in PATTERNS.items()}

    counts = defaultdict(int)
    examples = defaultdict(list)
    for t in msgs:
        for k, ps in comp.items():
            if any(p.search(t) for p in ps):
                counts[k] += 1
                if len(examples[k]) < 5 and 8 <= len(t) <= 120:
                    examples[k].append(t)

    n = len(msgs) or 1
    print(f"# 총 {len(msgs)}건 발화 기준 패턴 빈도\n")
    for k, c in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"{c:4d}  {c/n*100:4.1f}%  {k}")
    print("\n# 대표 사례(카테고리별 최대 3개)\n")
    for k, _ in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"## {k} ({counts[k]}건)")
        for e in examples[k][:3]:
            print("  -", e[:110])


if __name__ == "__main__":
    main()
