---
name: create
description: >
  로컬 AI 세션 기록(Claude Code·Codex)에서 사용자의 판단 방식·가치관·소통 스타일을
  추출·귀납해 지시형 시스템 프롬프트를 만들고, 승인 후 전역 설정(~/.claude/CLAUDE.md·
  ~/.codex/AGENTS.md)에 설치한다. 완전 로컬·프라이버시 우선. 사용자가 "내 페르소나 만들어줘 /
  persona 만들어줘 / 내 작업 스타일 뽑아줘"라고 할 때 사용.
---

# my-persona: create — 데이터 기반 자기 페르소나 생성

## 실행 규약 (에이전트)
이 SKILL.md가 있는 디렉터리를 `${SKILL_DIR}`로 삼아라. 공용 스크립트는 **`${SKILL_DIR}/../../scripts/`**에
있다(예: `${SKILL_DIR}/../../scripts/extract.py`). 개인 데이터(rules.json·.pending·.msgs.jsonl)는 위치와
무관하게 항상 **`~/.my-persona/`**에 저장된다.

## 프라이버시 (먼저 고지)
- **완전 로컬.** 로그를 외부로 전송하지 않는다.
- 발화를 읽기 전에 `extract.py`가 **시크릿·이메일·토큰·해시를 자동 마스킹**한다.
- 개인 데이터(rules.json 등)는 `~/.my-persona/`에만 저장되고 repo/플러그인에 포함되지 않는다.

## 좋은 결과 조건
- 발화 수백 건 이상 + 일관된 이력이면 초안 품질이 좋다. 적으면 Step 3에서 경고한다.
- 세션 로그는 "교정 지문"이라 사용자가 반박·지시·교정한 것에 편향된다. 이 한계를 알리고 인터뷰로 보정한다.
  산출물은 "완성품"이 아니라 "좋은 초안 + 사용자 편집"이 목표.

---

## Step 0 — 소스 탐지 & 스코프 선택
```bash
python3 ${SKILL_DIR}/../../scripts/extract.py --list
```
출력(소스별 프로젝트·세션 수·기간)을 보여주고 물어본다: ① 소스(Claude/Codex/둘 다) ② 프로젝트(전체/특정)
③ 기간(전체/최근 N개월) ④ 업무/개인.

## Step 1 — 발화 추출 (레닥션 포함)
```bash
python3 ${SKILL_DIR}/../../scripts/extract.py --sources claude,codex --projects "<substr>" --since <YYYY-MM-DD>
```
총 건수/소스별/길이 중앙값을 보고한다.

## Step 2 — 정량 신호 + 대표 샘플
```bash
python3 ${SKILL_DIR}/../../scripts/analyze.py    # 패턴 빈도(보조 신호)
python3 ${SKILL_DIR}/../../scripts/sample.py     # LLM 귀납용 대표 샘플
```

## Step 3 — 표본 가드
추출 총 건수가 **< 100건**이면 "신뢰도 낮음"을 경고하고 계속할지 확인한다.

## Step 4 — 패턴 귀납 → rules.json 작성 (LLM = 너가 직접)
`sample.py` 출력을 읽고 규칙을 귀납한다. 정규식 빈도에 의존하지 말고 실제 발화에서 근거를 찾는다.
카테고리: `가치관 / 판단 / 소통 / 절대규칙 / 검증 / 라이브러리 / git / 상황별`.
각 규칙을 `rules.example.json` 스키마로 `~/.my-persona/rules.json`에 기록한다:
- `text`는 지시형("너는 ~하라 / 하지 마라"). `confidence`(상/중/하)·`evidence`(근거 발화 수·예시) 필수.
- `source: "induced"`. 근거 약하면 `confidence: "하"`로 정직하게.
- `meta.identity`(작업 스타일 한 문장), `meta.priority_order`(우선순위 배열)도 채운다.

## Step 5 — 상황별 드릴다운 인터뷰 (추측 최소화)
데이터로 못 정하거나 애매한 부분은 반드시 질문한다(추측 금지).
- **확신도 게이팅**: `confidence: 하/중` 규칙은 전부 확인 질문으로 돌린다.
- **상황별 드릴다운**: 버그/이상동작, 코드리뷰, 리팩터 범위, 새 라이브러리 도입, PR·커밋, 문서·글, 테스트,
  완료 검증, 우선순위 충돌 순서 — 각각 "이 상황에선 구체적으로 어떤 규칙?"을 물어 세밀한 트리거→행동
  규칙을 만든다(category `상황별`, source `interview`).
추가로 목적·출력 언어·설치 대상(Claude/Codex)을 확인해 rules.json에 반영한다.

## Step 6 — 컴파일 & 리뷰
```bash
python3 ${SKILL_DIR}/../../scripts/compile.py     # rules.json → 프롬프트 미리보기
```
결과를 섹션별로 보여주고 사용자가 수정/삭제하게 한다.

## Step 7 — 설치 (미리보기 → 승인 → 기록)
```bash
python3 ${SKILL_DIR}/../../scripts/install.py --from-rules --target ~/.claude/CLAUDE.md            # 미리보기
python3 ${SKILL_DIR}/../../scripts/install.py --from-rules --target ~/.claude/CLAUDE.md --apply    # 승인 후
```
Codex는 `--target ~/.codex/AGENTS.md`. 구분자 블록에만 기록(멱등), 최초 1회 `.bak` 백업.
**승인 없이 자동 기록하지 않는다.**

---

## 이후
- 규칙을 켜고 끄거나 즐겨찾기 → **dashboard 스킬**(`/my-persona:dashboard`, Codex `$dashboard`).
- 새로 쌓인 신호 반영 → **update 스킬**. 자동 제안 켜기/끄기 → **auto 스킬**.

## 원칙
- 사용자에게 하는 말은 담백한 존댓말로, 쉽게. 전문용어·내부 수치 노출 금지.
- 근거 없이 단정하지 마라. 개인화는 `~/.my-persona/`에만. 완전 로컬.
