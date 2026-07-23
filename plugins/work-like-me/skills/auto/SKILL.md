---
name: auto
description: >
  대화가 쌓이면 페르소나 업데이트를 제안받는 기능(자동 관찰)을 켜거나 끈다. 사용자가
  "페르소나 자동 제안 켜줘/꺼줘 / 자동 업데이트 켜기"라고 할 때 사용.
---

# wlm: auto — 자동 업데이트 제안 켜기/끄기

`${SKILL_DIR}`는 이 SKILL.md 디렉터리, 공용 스크립트는 `${SKILL_DIR}/../../scripts/`.

자동 제안은 **기본 켜짐**이다(플러그인의 네이티브 SessionEnd 훅). 현재 상태를 확인하고, 사용자가 원하면 끈다:

```bash
python3 ${SKILL_DIR}/../../scripts/capture.py --hook-status     # 현재 상태(켜짐/꺼짐)
python3 ${SKILL_DIR}/../../scripts/capture.py --uninstall-hook  # 끄기(.auto-off 플래그)
python3 ${SKILL_DIR}/../../scripts/capture.py --install-hook    # 다시 켜기
```

- 켜져 있으면(기본) 대화가 끝날 때마다 새 신호를 조용히 로컬에 모으고, 충분히 쌓이면 대시보드에 알림만 띄운다(방해 없음).
- 모으는 건 **전부 로컬**이고 네트워크 전송 없음. `/wlm:update`로 검토하기 전까진 **자동으로 반영되는 것은 없다.**
- 끄기는 **사용자 settings.json을 건드리지 않는다** — `~/.work-like-me/.auto-off` 플래그만 만든다(훅은 그대로 있되 즉시 빠져나감).
- **자동 훅은 Claude 전용이다**(Codex는 세션 종료 훅이 없음). 다만 `update`가 실행 시 Claude+Codex 양쪽을 직접 스캔하므로, **Codex만 써도 검토는 정상 동작한다.** 이 훅은 배지 알림 편의일 뿐 검토의 전제조건이 아니다.

사용자에겐 "켰습니다 / 껐습니다" 정도로만 담백하게 안내한다.
