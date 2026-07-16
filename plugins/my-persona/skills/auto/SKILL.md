---
name: auto
description: >
  대화가 쌓이면 페르소나 업데이트를 제안받는 기능(자동 관찰)을 켜거나 끈다. 사용자가
  "페르소나 자동 제안 켜줘/꺼줘 / 자동 업데이트 켜기"라고 할 때 사용.
---

# my-persona: auto — 자동 업데이트 제안 켜기/끄기

`${SKILL_DIR}`는 이 SKILL.md 디렉터리, 공용 스크립트는 `${SKILL_DIR}/../../scripts/`.

현재 상태를 먼저 확인하고, 사용자에게 켤지/끌지 물어라(전문용어·수치 없이):
> "대화가 쌓이면 가끔 새로 반영할 내용을 제안해 드릴까요?"

```bash
python3 ${SKILL_DIR}/../../scripts/capture.py --hook-status     # 현재 상태(켜짐/꺼짐)
python3 ${SKILL_DIR}/../../scripts/capture.py --install-hook    # 켜기
python3 ${SKILL_DIR}/../../scripts/capture.py --uninstall-hook  # 끄기
```

- 켜면 대화가 끝날 때마다 새 신호를 조용히 모으고, 충분히 쌓이면 대시보드에 알림만 띄운다(방해 없음).
- `/my-persona:update`(Codex `$update`)로 언제든 검토할 수 있다. **자동으로 반영되는 것은 없다.**
- 스킬만 설치해도 자동으로 안 켜진다 — 사용자가 직접 동의해야 켜진다(남의 전역 설정을 몰래 바꾸지 않기 위함).

사용자에겐 "켰습니다 / 껐습니다" 정도로만 담백하게 안내한다.
