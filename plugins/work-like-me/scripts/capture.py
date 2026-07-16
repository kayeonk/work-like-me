#!/usr/bin/env python3
"""work-like-me 지속 진화 — SessionEnd 훅 + 훅 설치/리뷰 관리.

모드:
  (인자 없음)        SessionEnd 훅. 끝난 세션 발화를 레닥션해 .pending/queue.jsonl 축적.
                     신규 신호 >= THRESHOLD  AND  마지막 리뷰 후 COOLDOWN_DAYS 경과 → .pending/flag 기록.
                     (flag = 대시보드 배지 = "업데이트 검토 권장". 방해하지 않음)
  --scan             훅과 무관하게 Claude+Codex 최신 발화를 즉석 스캔해 큐에 반영(도구 무관).
                     Codex는 SessionEnd 훅이 없으므로, update 스킬이 이 모드로 양쪽을 따라잡는다.
  --install-hook     ~/.claude/settings.json 의 SessionEnd 에 이 스크립트를 등록(백업, 중복 방지).
  --uninstall-hook   등록 해제.
  --hook-status      등록 여부 출력.
  --mark-reviewed    리뷰 완료 표시(쿨다운 리셋) + 큐/flag 정리.

훅으로 매 세션 실행되므로 기본 모드는 절대 크래시하지 않는다(항상 exit 0).
"""
import json, os, sys, glob
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))          # 코드 위치(플러그인/스킬 폴더)
sys.path.insert(0, HERE)
DATA_DIR = os.path.expanduser(os.environ.get("WORK_LIKE_ME_DATA", "~/.work-like-me"))  # 개인 데이터
PENDING_DIR = os.path.join(DATA_DIR, ".pending")
QUEUE = os.path.join(PENDING_DIR, "queue.jsonl")
FLAG = os.path.join(PENDING_DIR, "flag")
STATE = os.path.join(PENDING_DIR, "state.json")
SETTINGS = os.path.expanduser("~/.claude/settings.json")
HOOK_CMD = f"python3 {os.path.join(HERE, 'capture.py')}"

THRESHOLD = 30       # 신규 신호 이만큼 쌓여야
COOLDOWN_DAYS = 7    # 마지막 리뷰 후 이만큼 지나야 배지

try:
    import extract  # redact/clean/NOISE 재사용
except Exception:
    extract = None


def now():
    return datetime.now(timezone.utc)


def load_state():
    try:
        return json.load(open(STATE, encoding="utf-8"))
    except Exception:
        return {}


def save_state(s):
    os.makedirs(PENDING_DIR, exist_ok=True)
    json.dump(s, open(STATE, "w", encoding="utf-8"), ensure_ascii=False)


# ---------- SessionEnd 훅(기본 모드) ----------
def newest_transcript():
    files = glob.glob(os.path.expanduser("~/.claude/projects/**/*.jsonl"), recursive=True)
    return max(files, key=os.path.getmtime) if files else None


def read_transcript_path():
    try:
        data = json.loads(sys.stdin.read() or "{}")
        p = data.get("transcript_path") or data.get("transcriptPath")
        if p and os.path.exists(os.path.expanduser(p)):
            return os.path.expanduser(p)
    except Exception:
        pass
    return newest_transcript()


def parse_user_utterances(path):
    out = []
    for l in open(path, encoding="utf-8", errors="ignore"):
        try:
            o = json.loads(l)
        except Exception:
            continue
        if o.get("type") != "user":
            continue
        m = o.get("message", {})
        if m.get("role") != "user":
            continue
        c = m.get("content")
        texts = [c] if isinstance(c, str) else \
            [b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text"] if isinstance(c, list) else []
        for t in texts:
            t = extract.clean(t) if extract else (t.strip() or None)
            if t:
                out.append(extract.redact(t) if extract else t)
    return out


def do_capture():
    try:
        os.makedirs(PENDING_DIR, exist_ok=True)
        state = load_state()
        if "last_review" not in state:                 # 최초 사용 시점을 쿨다운 기준으로
            state["last_review"] = now().isoformat()
            save_state(state)
        path = read_transcript_path()
        if not path:
            return
        new = parse_user_utterances(path)
        seen = set()
        if os.path.exists(QUEUE):
            for l in open(QUEUE, encoding="utf-8"):
                try:
                    seen.add(json.loads(l)["t"])
                except Exception:
                    pass
        ts = now().isoformat()
        with open(QUEUE, "a", encoding="utf-8") as w:
            for t in new:
                if t in seen:
                    continue
                seen.add(t)
                w.write(json.dumps({"t": t, "ts": ts}, ensure_ascii=False) + "\n")
        # flag 판정: 신규 신호 수(=리뷰 이후 큐 전체) AND 쿨다운
        total = sum(1 for _ in open(QUEUE, encoding="utf-8")) if os.path.exists(QUEUE) else 0
        try:
            age_days = (now() - datetime.fromisoformat(state["last_review"])).days
        except Exception:
            age_days = 999
        if total >= THRESHOLD and age_days >= COOLDOWN_DAYS:
            open(FLAG, "w").write(str(total))
    except Exception:
        pass
    finally:
        sys.exit(0)


def do_scan():
    """훅과 무관하게 Claude+Codex 최신 발화를 큐에 반영(도구 무관 따라잡기).

    Codex는 SessionEnd 훅이 없으므로 update 스킬이 이 모드로 양쪽을 스캔해 검토 대상을 채운다.
    이미 큐에 있는 발화(레닥션 후 동일 텍스트)는 건너뛴다.
    """
    if extract is None:
        print("스캔 불가: extract 모듈을 불러오지 못했습니다.")
        return 0
    os.makedirs(PENDING_DIR, exist_ok=True)
    state = load_state()
    # 컷오프: 지난 스캔 → 지난 리뷰 → 둘 다 없으면 최근 90일(첫 스캔 폭주 방지)
    ref = state.get("last_scan") or state.get("last_review")
    try:
        since_dt = datetime.fromisoformat(ref) if ref else now() - timedelta(days=90)
    except Exception:
        since_dt = now() - timedelta(days=90)
    seen = set()
    if os.path.exists(QUEUE):
        for l in open(QUEUE, encoding="utf-8"):
            try:
                seen.add(json.loads(l)["t"])
            except Exception:
                pass
    ts = now().isoformat()
    added = 0
    with open(QUEUE, "a", encoding="utf-8") as w:
        for _src, t in extract.iter_user_utterances(["claude", "codex"], [], since_dt):
            rt = extract.redact(t)
            if rt in seen:
                continue
            seen.add(rt)
            w.write(json.dumps({"t": rt, "ts": ts}, ensure_ascii=False) + "\n")
            added += 1
    state["last_scan"] = ts
    save_state(state)
    # 배지 재판정(신규 신호 수 AND 쿨다운)
    total = sum(1 for _ in open(QUEUE, encoding="utf-8")) if os.path.exists(QUEUE) else 0
    lr = state.get("last_review")
    try:
        age_days = (now() - datetime.fromisoformat(lr)).days if lr else 999
    except Exception:
        age_days = 999
    if total >= THRESHOLD and age_days >= COOLDOWN_DAYS:
        open(FLAG, "w").write(str(total))
    print(f"스캔 완료: 신규 {added}건, 대기 총 {total}건")
    return added


def mark_reviewed():
    """리뷰 완료: 쿨다운 리셋 + 큐/flag 비우기."""
    save_state({"last_review": now().isoformat()})
    for f in (QUEUE, FLAG):
        try:
            os.remove(f)
        except OSError:
            pass
    print("반영했습니다.")


# ---------- 훅 설치/해제 ----------
def _load_settings():
    return json.load(open(SETTINGS, encoding="utf-8")) if os.path.exists(SETTINGS) else {}


def hook_registered(d):
    for g in d.get("hooks", {}).get("SessionEnd", []):
        for h in (g.get("hooks", []) if isinstance(g, dict) else []):
            if isinstance(h, dict) and h.get("command", "").rstrip().endswith("capture.py"):
                return True
    return False


def install_hook():
    d = _load_settings()
    if hook_registered(d):
        print("이미 켜져 있습니다.")
        return
    import shutil
    if os.path.exists(SETTINGS):
        shutil.copy2(SETTINGS, SETTINGS + ".bak-mypersona")
    se = d.setdefault("hooks", {}).setdefault("SessionEnd", [])
    grp = next((g for g in se if isinstance(g, dict) and g.get("matcher") == "*"), None)
    if grp is None:
        grp = {"matcher": "*", "hooks": []}
        se.append(grp)
    grp.setdefault("hooks", []).append({"type": "command", "command": HOOK_CMD})
    json.dump(d, open(SETTINGS, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("자동 업데이트 제안을 켰습니다. 기존 설정은 백업해 두었습니다.")


def uninstall_hook():
    d = _load_settings()
    if not hook_registered(d):
        print("켜져 있지 않습니다.")
        return
    for g in d.get("hooks", {}).get("SessionEnd", []):
        if isinstance(g, dict):
            g["hooks"] = [h for h in g.get("hooks", [])
                          if not (isinstance(h, dict) and h.get("command", "").rstrip().endswith("capture.py"))]
    json.dump(d, open(SETTINGS, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("자동 업데이트 제안을 껐습니다.")


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    if arg == "--install-hook":
        install_hook()
    elif arg == "--uninstall-hook":
        uninstall_hook()
    elif arg == "--hook-status":
        print("켜짐" if hook_registered(_load_settings()) else "꺼짐")
    elif arg == "--mark-reviewed":
        mark_reviewed()
    elif arg == "--scan":
        do_scan()
    else:
        do_capture()


if __name__ == "__main__":
    main()
