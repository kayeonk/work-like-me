---
description: 내 페르소나 규칙을 브라우저에서 관리합니다 (켜기/끄기·즐겨찾기·변경 적용)
---

`${CLAUDE_PLUGIN_ROOT}/skills/my-persona/dashboard.py` 를 **백그라운드로** 실행하라
(서버가 계속 떠 있어야 하므로 블로킹하지 않게):

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/my-persona/dashboard.py"
```

실행되면 사용자에게 접속 주소(기본 http://127.0.0.1:8765)를 안내하고, 종료는 Ctrl+C라고 알려라.
대시보드에서 규칙을 켜고 끄거나 즐겨찾기한 뒤 **변경 적용**을 눌러야 실제 설정에 반영된다.
