---
description: 새로 쌓인 대화 신호를 검토해 페르소나 규칙 업데이트를 제안·반영합니다
---

SKILL.md의 "제안형 진화"를 수행하라:

1. `~/.my-persona/.pending/queue.jsonl` 를 읽어 새 신호를 분석한다.
2. **진짜 새롭거나 기존과 충돌하는 패턴이 있을 때만** 후보 규칙(신규/수정)을 근거와 함께 제안한다.
   없으면 "반영할 변경이 없습니다"라고 알린다.
3. 사용자가 고른 것만 `~/.my-persona/rules.json` 에 반영한다.
4. `${CLAUDE_PLUGIN_ROOT}/skills/my-persona/install.py --from-rules` 로 미리보기 → 승인 후 설치.
5. `python3 "${CLAUDE_PLUGIN_ROOT}/skills/my-persona/capture.py" --mark-reviewed` 로 마무리한다.
