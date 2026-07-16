---
name: my-persona
description: >
  로컬 AI 세션 기록(Claude Code, Codex 등)에서 사용자의 판단 방식·가치관·소통
  스타일을 추출해, 규칙 레지스트리(rules.json)로 만들고 지시형 시스템 프롬프트로
  컴파일해 전역 설정에 설치한다. 규칙별 즐겨찾기/일시정지, 대시보드 관리, 훅 기반
  제안형 진화를 지원한다. 완전 로컬·프라이버시 우선·근거 기반. 사용자가
  "내 페르소나 만들어줘 / persona 만들어줘 / 내 작업 스타일 뽑아줘 / my-persona 업데이트"
  라고 할 때 사용.
---

# my-persona — 데이터 기반 자기 페르소나 생성기 (v2)

> 세션 로그 → **규칙 레지스트리(rules.json)** → 지시형 프롬프트 컴파일 → 전역 설치.
> 규칙을 원자 단위로 관리(즐겨찾기·일시정지)하고, 대화가 쌓이면 제안형으로 진화한다.

## 프라이버시 & 개인화 격리 (먼저 고지)

- **완전 로컬.** 로그를 외부로 전송하지 않는다.
- 발화를 읽기 전에 `extract.py`가 **시크릿·이메일·토큰·해시를 자동 마스킹**한다.
- **개인 데이터는 절대 스킬 repo에 커밋되지 않는다**: `rules.json`(사용자별 생성물),
  `.msgs.jsonl`, `.pending/`, 설치된 프롬프트는 모두 gitignore. 이 스킬 자체는 제네릭 도구다.
- 형식 참고는 `rules.example.json`(개인정보 없는 템플릿).

## 좋은 결과 조건 (미리 판단)

- 발화 수백 건 이상 + 일관된 이력이면 초안 품질이 좋다. 적으면 Step 3에서 경고한다.
- 세션 로그는 "교정 지문"이라 사용자가 **반박·지시·교정한 것에 편향**된다. 이 한계를 알리고
  인터뷰·편집으로 보정한다. 산출물은 "완성품"이 아니라 "좋은 초안 + 사용자 편집"이 목표.

---

## Step 0 — 소스 탐지 & 스코프 선택

```bash
python3 ~/.claude/skills/my-persona/extract.py --list
```
출력(소스별 프로젝트·세션 수·기간)을 보여주고 **물어본다**: ① 소스(Claude/Codex/둘 다)
② 프로젝트(전체/특정) ③ 기간(전체/최근 N개월) ④ 업무/개인.

## Step 1 — 발화 추출 (레닥션 포함)

```bash
python3 ~/.claude/skills/my-persona/extract.py --sources claude,codex --projects "<substr>" --since <YYYY-MM-DD>
```
총 건수/소스별/길이 중앙값을 보고한다.

## Step 2 — 정량 신호 + 대표 샘플

```bash
python3 ~/.claude/skills/my-persona/analyze.py    # 패턴 빈도(보조 신호, 언어의존적)
python3 ~/.claude/skills/my-persona/sample.py     # LLM 귀납용 대표 샘플
```

## Step 3 — 표본 가드

추출 총 건수가 **< 100건**이면 "신뢰도 낮음"을 경고하고 계속할지 확인한다.

## Step 4 — 패턴 귀납 → rules.json 작성 (LLM = 너가 직접)

`sample.py` 출력을 **읽고** 규칙을 귀납한다. 정규식 빈도에 의존하지 말고 실제 발화에서 근거를 찾는다.
카테고리: `가치관 / 판단 / 소통 / 절대규칙 / 검증 / 라이브러리 / git / 상황별`.

각 규칙을 `rules.example.json` 스키마로 `~/.claude/skills/my-persona/rules.json`에 기록한다:
- `text`는 **지시형**("너는 ~하라 / 하지 마라"). `confidence`(상/중/하)와 `evidence`(근거 발화 수·예시) 필수.
- `source: "induced"`. 근거 약하면 `confidence: "하"`로 정직하게.
- `meta.identity`(작업 스타일 한 문장), `meta.priority_order`(우선순위 배열)도 채운다.

## Step 5 — 상황별 드릴다운 인터뷰 (추측 최소화)

데이터로 **못 정하거나 애매한 부분은 반드시 질문**한다(추측 금지). 두 갈래로 판다:

**A. 확신도 게이팅** — `confidence: 하/중` 규칙은 전부 사용자에게 확인 질문으로 돌린다.

**B. 상황별 드릴다운** — 아래 상황 각각에 "이 상황에선 구체적으로 어떤 규칙?"을 물어
세밀한 트리거→행동 규칙을 만든다 (category `상황별`, source `interview`):
- 버그/이상 동작을 만났을 때
- 코드 리뷰할 때 / 리뷰받을 때
- 리팩터 범위를 정할 때
- 새 라이브러리 도입 검토
- PR·커밋·브랜치
- 문서·글 산출물
- 테스트 작성/전략
- 완료 보고 전 검증
- 우선순위 충돌(안전성·일관성·성능·단순성·속도) 순서

추가로 목적(주입용/자기이해/공유), 출력 언어, 설치 대상(Claude/Codex)을 확인한다.
답변을 rules.json에 반영한다.

## Step 6 — 컴파일 & 리뷰

```bash
python3 ~/.claude/skills/my-persona/compile.py     # rules.json → 프롬프트 미리보기(stdout)
```
결과를 섹션별로 보여주고 사용자가 수정/삭제하게 한다(rules.json 편집 또는 대시보드).

## Step 7 — 설치 (미리보기 → 승인 → 기록)

```bash
# 미리보기
python3 ~/.claude/skills/my-persona/install.py --from-rules --target ~/.claude/CLAUDE.md
# 승인 후 기록 (Codex는 --target ~/.codex/AGENTS.md)
python3 ~/.claude/skills/my-persona/install.py --from-rules --target ~/.claude/CLAUDE.md --apply
```
구분자 블록에만 기록(멱등), 최초 1회 `.bak` 백업. **승인 없이 자동 기록하지 않는다.**

## Step 8 — 관리 대시보드 (즐겨찾기 / 일시정지)

```bash
python3 ~/.claude/skills/my-persona/dashboard.py   # 브라우저로 규칙 관리 UI
```
규칙을 카테고리별로 보고, on/off(일시정지)·★즐겨찾기 토글, "적용"으로 재컴파일·설치.
CLI만으로도 가능: 규칙 `enabled`/`favorite`를 rules.json에서 바꾸고 Step 7 재실행.

## Step 9 — 훅 기반 제안형 진화 (선택)

세션이 끝날 때마다 새 신호를 모아, **기준을 넘으면 대시보드 배지로만 알린다**(방해·자동 반영 없음).

**켜기 — 사용자에게 Y/N로 물어본다.** 전문용어·수치 없이, 예:
> "대화가 쌓이면 가끔 새로 반영할 내용을 제안해 드릴까요?"

동의하면 실행(사용자에겐 "켰습니다" 정도로만 안내):
```bash
python3 ~/.claude/skills/my-persona/capture.py --install-hook
```
(SessionEnd에 등록, settings.json 백업. 끄기 `--uninstall-hook`, 상태 `--hook-status`.)
> 스킬만 복사해도 자동으로 안 켜진다 — 각 사용자가 이 단계에서 **직접 동의**해야 켜진다
> (남의 전역 설정을 몰래 바꾸지 않기 위함).

**알림 기준(내부용 — 사용자에게 말하지 마라):** 신규 신호 30건 이상 AND 마지막 리뷰 후 7일 경과일 때만
배지. 그 전까지는 조용히 쌓기만 한다(방해 0). 값은 capture.py 의 THRESHOLD/COOLDOWN_DAYS.
사용자에겐 "새로 반영할 내용이 쌓이면 대시보드에 알려드립니다" 정도로만.

**리뷰:** 사용자가 **"my-persona 업데이트"**라고 하면:
1. `.pending/queue.jsonl` 을 읽어 새 신호를 분석
2. **진짜 새롭거나 기존과 충돌하는 패턴이 있을 때만** 후보 규칙을 근거와 함께 제안(없으면 "변경 없음")
3. accept/reject → rules.json 병합(source `hook`)
4. compile + install (미리보기 → 승인)
5. `python3 ~/.claude/skills/my-persona/capture.py --mark-reviewed` (쿨다운 리셋·큐 정리)

**어떤 단계도 승인 없이 전역 설정을 자동 변경하지 않는다.**

---

## 원칙

- **사용자에게 하는 말은 담백한 존댓말(~합니다)로, 쉽게.** 전문용어(훅·레지스트리·컴파일·임계치·신호)와
  내부 수치(건수·기간 등)를 사용자에게 노출하지 마라. 내부 메커니즘은 이 문서(에이전트용)에만 두고,
  사용자에겐 이득 중심으로 말한다.
- **근거 없이 단정하지 마라.** 규칙은 실제 발화 근거에서 나온다. 근거 약하면 인터뷰로 확인.
- **개인화는 로컬에만.** rules.json 등 개인 생성물은 커밋 금지. 스킬은 제네릭 유지.
- **완전 로컬.** 로그를 외부로 보내지 않는다.
- 초안임을 알리고 사용자 편집으로 완성한다.
