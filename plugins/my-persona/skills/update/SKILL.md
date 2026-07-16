---
name: update
description: >
  대화가 쌓이며 모인 새 신호를 검토해 페르소나 규칙 업데이트를 제안·반영한다. 사용자가
  "페르소나 업데이트 / 새로 반영할 내용 검토 / my-persona 업데이트"라고 할 때 사용.
---

# my-persona: update — 제안형 업데이트 검토

`${SKILL_DIR}`는 이 SKILL.md 디렉터리, 공용 스크립트는 `${SKILL_DIR}/../../scripts/`.

1. `~/.my-persona/.pending/queue.jsonl` 을 읽어 새 신호를 분석한다.
2. **진짜 새롭거나 기존 규칙과 충돌하는 패턴이 있을 때만** 후보 규칙(신규/수정)을 근거와 함께 제안한다.
   없으면 "반영할 변경이 없습니다"라고 알린다.
3. 사용자가 고른 것만 `~/.my-persona/rules.json`에 반영한다(source `hook`).
4. 설치 — 미리보기 → 승인 후 기록:
   ```bash
   python3 ${SKILL_DIR}/../../scripts/install.py --from-rules --target ~/.claude/CLAUDE.md          # 미리보기
   python3 ${SKILL_DIR}/../../scripts/install.py --from-rules --target ~/.claude/CLAUDE.md --apply  # 승인 후
   ```
   Codex는 `--target ~/.codex/AGENTS.md`.
5. 마무리:
   ```bash
   python3 ${SKILL_DIR}/../../scripts/capture.py --mark-reviewed
   ```

**승인 없이 전역 설정을 자동 변경하지 않는다.** 사용자에겐 담백한 존댓말로, 내부 수치는 노출하지 않는다.
