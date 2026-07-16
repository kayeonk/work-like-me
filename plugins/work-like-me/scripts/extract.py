#!/usr/bin/env python3
"""로컬 AI 세션에서 '사용자 발화'만 추출 (Claude Code + Codex CLI).

두 가지 모드:
  --list                       사용 가능한 소스를 탐지해 JSON으로 출력(스코프 질문용)
  (기본)                        발화 추출 → --out 경로에 jsonl 저장

필터:
  --sources claude,codex       사용할 소스 (기본: 존재하는 것 전부)
  --projects <substr,substr>   Claude 프로젝트 경로/Codex cwd에 부분일치하는 것만
  --since YYYY-MM-DD           해당 날짜 이후 발화만
  --out <path>                 추출 결과 저장 경로
"""
import json, os, re, glob, argparse
from datetime import datetime, timezone

CLAUDE = os.path.expanduser("~/.claude/projects")
CODEX = os.path.expanduser("~/.codex/sessions")
# 개인 데이터는 스킬/플러그인 폴더가 아니라 안정적 사용자 경로에 저장(플러그인 업데이트에도 보존)
DATA_DIR = os.path.expanduser(os.environ.get("WORK_LIKE_ME_DATA", "~/.work-like-me"))

NOISE = re.compile(
    r"<environment_context>|<system-reminder>|<command-name>|local-command-stdout|"
    r"\[Request interrupted|Caveat:|<user-prompt-submit-hook>|SessionStart|"
    r"UserPromptSubmit|tool_result|stdout|stderr", re.I)


def clean(text):
    if not isinstance(text, str):
        return None
    t = text.strip()
    if not t or NOISE.search(t):
        return None
    return t


# LLM이 샘플을 읽기 전, 로컬에서 시크릿/PII를 지운다 (네트워크 전송 없음).
# 순서 중요: 구체적 토큰 → .env 시크릿 → hash → 홈 경로(크로스 OS) → IP.
HOME = os.path.expanduser("~")

REDACT_RULES = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "<email>"),
    (re.compile(r"\b(?:sk|pk|rk)-[A-Za-z0-9]{16,}\b"), "<key>"),
    (re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"), "<token>"),
    (re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"), "<token>"),          # GitHub fine-grained PAT
    (re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"), "<token>"),          # Slack
    (re.compile(r"\bAIza[0-9A-Za-z_\-]{30,}\b"), "<key>"),                 # Google API key
    (re.compile(r"\bAKIA[0-9A-Z]{12,}\b"), "<aws-key>"),
    (re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"), "<jwt>"),
    (re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._\-]{10,}"), "Bearer <token>"),
    # .env 스타일: 시크릿성 키에 붙은 값만 지운다(키 이름은 남김, 오탐 최소화 위해 8자+ 값만).
    (re.compile(r"(?i)\b([A-Za-z0-9_]*(?:secret|token|password|passwd|api[_-]?key|access[_-]?key|client[_-]?secret)[A-Za-z0-9_]*)\s*[:=]\s*['\"]?([^\s'\"]{8,})"),
     r"\1=<secret>"),
    (re.compile(r"\b[0-9a-fA-F]{32,}\b"), "<hash>"),
    # 홈 경로 → 사용자명 노출 방지. 크로스 OS: macOS /Users, Linux /home, Windows C:\Users.
    (re.compile(r"/Users/[^/\s]+"), "<home>"),
    (re.compile(r"/home/[^/\s]+"), "<home>"),
    (re.compile(r"[A-Za-z]:\\Users\\[^\\\s]+"), "<home>"),
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "<ip>"),
]


def redact(t):
    # 실행 중인 사용자의 실제 홈은 OS 불문 정확히 치환(비표준 $HOME도 커버).
    if HOME and HOME in t:
        t = t.replace(HOME, "<home>")
    for rx, rep in REDACT_RULES:
        t = rx.sub(rep, t)
    return t


def decode_project(dirname):
    """Claude 프로젝트 폴더명(-Users-macbook9-Documents-foo) → 대략 경로."""
    return dirname.replace("-", "/", 0).lstrip("-").replace("-", "/")


def parse_ts(s):
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except Exception:
        return None


def list_sources():
    out = {"claude": {"exists": os.path.isdir(CLAUDE), "projects": []},
           "codex": {"exists": os.path.isdir(CODEX), "sessions": 0, "range": None}}
    if out["claude"]["exists"]:
        for d in sorted(os.listdir(CLAUDE)):
            p = os.path.join(CLAUDE, d)
            if not os.path.isdir(p):
                continue
            files = glob.glob(os.path.join(p, "*.jsonl"))
            if not files:
                continue
            mt = [os.path.getmtime(f) for f in files]
            out["claude"]["projects"].append({
                "folder": d,
                "path_hint": "/" + d.lstrip("-").replace("-", "/"),
                "sessions": len(files),
                "last": datetime.fromtimestamp(max(mt)).strftime("%Y-%m-%d"),
            })
    if out["codex"]["exists"]:
        files = glob.glob(os.path.join(CODEX, "**", "*.jsonl"), recursive=True)
        out["codex"]["sessions"] = len(files)
        if files:
            mt = [os.path.getmtime(f) for f in files]
            out["codex"]["range"] = [
                datetime.fromtimestamp(min(mt)).strftime("%Y-%m-%d"),
                datetime.fromtimestamp(max(mt)).strftime("%Y-%m-%d"),
            ]
    print(json.dumps(out, ensure_ascii=False, indent=2))


def match_project(text, filters):
    if not filters:
        return True
    return any(f.strip() and f.strip().lower() in text.lower() for f in filters)


def iter_user_utterances(sources, projects, since_dt):
    """Claude+Codex 세션에서 (src, cleaned_text)를 순회. redact/dedup은 호출측 책임.

    extract()와 capture.py --scan이 공유하는 단일 파싱 경로. since_dt로 과거 컷오프.
    """
    if "claude" in sources and os.path.isdir(CLAUDE):
        for d in os.listdir(CLAUDE):
            pdir = os.path.join(CLAUDE, d)
            if not os.path.isdir(pdir):
                continue
            if not match_project(d, projects):
                continue
            for f in glob.glob(os.path.join(pdir, "*.jsonl")):
                for l in open(f, encoding="utf-8", errors="ignore"):
                    try:
                        o = json.loads(l)
                    except Exception:
                        continue
                    if o.get("type") != "user":
                        continue
                    if since_dt:
                        ts = parse_ts(o.get("timestamp"))
                        if ts and ts < since_dt:
                            continue
                    m = o.get("message", {})
                    if m.get("role") != "user":
                        continue
                    c = m.get("content")
                    if isinstance(c, str):
                        t = clean(c)
                        if t:
                            yield ("claude", t)
                    elif isinstance(c, list):
                        for b in c:
                            if isinstance(b, dict) and b.get("type") == "text":
                                t = clean(b.get("text", ""))
                                if t:
                                    yield ("claude", t)

    if "codex" in sources and os.path.isdir(CODEX):
        for f in glob.glob(os.path.join(CODEX, "**", "*.jsonl"), recursive=True):
            cwd = ""
            rows = []
            for l in open(f, encoding="utf-8", errors="ignore"):
                try:
                    o = json.loads(l)
                except Exception:
                    continue
                if o.get("type") == "session_meta":
                    cwd = str(o.get("payload", {}).get("cwd", ""))
                rows.append(o)
            if not match_project(cwd or f, projects):
                continue
            for o in rows:
                p = o.get("payload", {})
                if not isinstance(p, dict):
                    continue
                if since_dt:
                    ts = parse_ts(o.get("timestamp"))
                    if ts and ts < since_dt:
                        continue
                if p.get("type") == "user_message":
                    t = clean(p.get("message") or p.get("text", ""))
                    if t:
                        yield ("codex", t)
                elif p.get("type") == "message" and p.get("role") == "user":
                    for b in p.get("content", []):
                        if isinstance(b, dict) and b.get("type") in ("input_text", "text"):
                            t = clean(b.get("text", ""))
                            if t:
                                yield ("codex", t)


def extract(sources, projects, since, out_path):
    since_dt = parse_ts(since + "T00:00:00+00:00") if since else None
    msgs = list(iter_user_utterances(sources, projects, since_dt))

    seen, uniq = set(), []
    for s, t in msgs:
        if (s, t) in seen:
            continue
        seen.add((s, t))
        uniq.append((s, t))

    with open(out_path, "w", encoding="utf-8") as w:
        for s, t in uniq:
            w.write(json.dumps({"src": s, "t": redact(t)}, ensure_ascii=False) + "\n")

    claude_n = sum(1 for s, _ in uniq if s == "claude")
    codex_n = sum(1 for s, _ in uniq if s == "codex")
    lens = [len(t) for _, t in uniq] or [0]
    print(json.dumps({
        "total": len(uniq), "claude": claude_n, "codex": codex_n,
        "median_len": sorted(lens)[len(lens) // 2],
        "short_ratio_pct": round(sum(1 for x in lens if x < 25) / len(lens) * 100),
        "out": out_path,
    }, ensure_ascii=False, indent=2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--sources", default="claude,codex")
    ap.add_argument("--projects", default="")
    ap.add_argument("--since", default="")
    ap.add_argument("--out", default=os.path.join(DATA_DIR, ".msgs.jsonl"))
    a = ap.parse_args()
    if a.list:
        list_sources()
        return
    os.makedirs(DATA_DIR, exist_ok=True)
    sources = [s.strip() for s in a.sources.split(",") if s.strip()]
    projects = [p for p in a.projects.split(",") if p.strip()] if a.projects else []
    extract(sources, projects, a.since or None, a.out)


if __name__ == "__main__":
    main()
