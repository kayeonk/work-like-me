#!/usr/bin/env python3
"""생성된 페르소나 프롬프트를 전역 설정 파일에 안전하게 설치.

- 구분자 블록(<!-- my-persona:start --> … <!-- my-persona:end -->) 안에만 기록.
- 블록이 이미 있으면 그 부분만 교체(멱등). 파일의 나머지는 절대 안 건드림.
- 최초 1회 백업(.bak) 생성.
- 기본은 --dry-run(미리보기). 실제 기록은 --apply 필요.

사용:
  install.py --prompt-file <md> --target ~/.claude/CLAUDE.md            # 미리보기
  install.py --prompt-file <md> --target ~/.claude/CLAUDE.md --apply    # 기록
  install.py --from-rules --target ~/.claude/CLAUDE.md --apply          # rules.json 컴파일해 설치
"""
import argparse, os, shutil, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.expanduser(os.environ.get("MY_PERSONA_DATA", "~/.my-persona"))

START = "<!-- my-persona:start -->"
END = "<!-- my-persona:end -->"


def build_block(prompt):
    return f"{START}\n{prompt.strip()}\n{END}\n"


def splice(existing, block):
    if START in existing and END in existing:
        pre = existing.split(START)[0]
        post = existing.split(END, 1)[1]
        return pre.rstrip("\n") + ("\n\n" if pre.strip() else "") + block + post.lstrip("\n")
    if existing.strip():
        return existing.rstrip("\n") + "\n\n" + block
    return block


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt-file", default="")
    ap.add_argument("--from-rules", action="store_true",
                    help="rules.json을 compile.py로 컴파일해 설치")
    ap.add_argument("--rules", default=os.path.join(DATA_DIR, "rules.json"))
    ap.add_argument("--target", required=True)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    target = os.path.expanduser(a.target)
    if a.from_rules:
        import json, compile as compiler
        data = json.load(open(os.path.expanduser(a.rules), encoding="utf-8"))
        prompt = compiler.compile_md(data)
    elif a.prompt_file:
        prompt = open(os.path.expanduser(a.prompt_file), encoding="utf-8").read()
    else:
        ap.error("--prompt-file 또는 --from-rules 중 하나가 필요합니다")
    block = build_block(prompt)
    existing = open(target, encoding="utf-8").read() if os.path.exists(target) else ""
    new = splice(existing, block)

    if not a.apply:
        print("=== DRY-RUN (미기록) ===")
        print(f"대상: {target}")
        print(f"기존 파일: {'있음 (' + str(len(existing.splitlines())) + '줄)' if existing else '없음 → 새로 생성'}")
        print(f"my-persona 블록: {'교체' if START in existing else '신규 삽입'}")
        print(f"기록 후 총 줄 수: {len(new.splitlines())}")
        print("\n--- 삽입될 블록 미리보기(앞 20줄) ---")
        print("\n".join(block.splitlines()[:20]))
        print("\n실제 기록하려면 --apply 를 붙여 다시 실행.")
        return

    os.makedirs(os.path.dirname(target), exist_ok=True)
    if existing and not os.path.exists(target + ".bak"):
        shutil.copy2(target, target + ".bak")
        print(f"백업 생성: {target}.bak")
    with open(target, "w", encoding="utf-8") as w:
        w.write(new)
    print(f"설치 완료: {target}  (총 {len(new.splitlines())}줄)")


if __name__ == "__main__":
    main()
