---
description: 대화가 쌓이면 페르소나 업데이트를 제안받는 기능을 켜거나 끕니다
---

현재 상태를 먼저 확인하고(`capture.py --hook-status`), 사용자에게 켤지/끌지 물어라.

- 켜기: `python3 "${CLAUDE_PLUGIN_ROOT}/skills/my-persona/capture.py" --install-hook`
- 끄기: `python3 "${CLAUDE_PLUGIN_ROOT}/skills/my-persona/capture.py" --uninstall-hook`

켜면 대화가 끝날 때마다 새 신호를 조용히 모으고, 충분히 쌓이면 대시보드에 알림만 띄운다(방해 없음).
`/my-persona:update` 로 언제든 검토할 수 있다. 자동으로 반영되는 것은 없다.
