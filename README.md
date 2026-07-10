# 카투사

[![CI](https://github.com/ljhljh0703-cmd/katousa-agent-harness/actions/workflows/ci.yml/badge.svg)](https://github.com/ljhljh0703-cmd/katousa-agent-harness/actions/workflows/ci.yml)

**카카오 투자하는 사람. 수익률은 못 올려도, 이해도는 올려드립니다.**

투자는 내가, 설명은 카투사가. 초보 투자자의 반복 질문과 이해 결과를 기억해 설명 방식은 조절하고, 안전 기준은 고정하는 Codex 플러그인 프로젝트입니다.

> 상태: `IMPLEMENTED / LOCALLY_VERIFIED / USER_RESEARCH_PLANNED`
> 검증 기준:
> `python3 -m unittest discover -s tests -v` `29 passed`
> `python3 scripts/run_replay_eval.py --out dist` `30 runs / invariant stable`
> `python3 scripts/export_portfolio_evidence.py` `public-safe evidence snapshot`
> `python3 "$CODEX_HOME/skills/.system/plugin-creator/scripts/validate_plugin.py" plugins/calm-trade-growth-harness` `PASS`
> `python3 "$CODEX_HOME/skills/.system/skill-creator/scripts/quick_validate.py" plugins/calm-trade-growth-harness/skills/calm-trade-growth-harness` `PASS`

## 포트폴리오에서 보는 법

카투사는 현수봇의 축소판이 아닙니다. 두 프로젝트는 서로 다른 위험을 통제합니다.

| | 현수봇 | 카투사 |
|---|---|---|
| 한 줄 정의 | 퀀트형 자동매매 에이전트의 행동 하네스 | 초보 투자자에게 맞춰 성장하는 설명 에이전트의 헤르메스형 하네스 |
| 통제 대상 | 주문으로 이어지는 외부 행동 | 기억과 개인화로 이어지는 내부 적응 |
| 사람에게 남긴 권한 | 실거래 전환과 규칙 채택 | 투자 결정과 중요한 프로필 변경 |

> 돈을 움직이는 AI는 행동을 통제하고, 사람에 맞춰 변하는 AI는 적응을 통제했습니다.

- [공개용 케이스 스터디](docs/PORTFOLIO-CASE-STUDY.md)
- [이력서·면접 카피 키트](docs/PORTFOLIO-COPY-KIT.md)
- [포트폴리오 발행 계획](docs/PORTFOLIO-PUBLISH-PLAN.md)
- [초보 사용자 검증 계획](docs/USER-RESEARCH-PLAN.md)
- [재생성 가능한 공개 증거](docs/portfolio-evidence.json)
- [주장과 증거 경계](docs/EVIDENCE-MAP.md)

여기서 `헤르메스형`은 관찰한 내용을 곧바로 학습시키지 않고, 변경 후보·검증·사용자 승인·버전 적용을 거치는 통제된 성장 루프를 뜻합니다. 자동 자기개조나 온라인 학습을 의미하지 않습니다.

## 문제

초보 투자자는 매수·매도 앞에서 같은 질문을 반복합니다. 기존 설명 도구는 매번 좋은 답을 만들 수 있어도, 사용자가 숫자·사례·체크리스트 중 어떤 방식을 이해하기 쉬워하는지와 어떤 개념에서 계속 막히는지를 다음 대화에 안전하게 반영하기 어렵습니다.

이 프로젝트는 수익률을 예측하거나 주문을 실행하지 않습니다. 다음 두 가지를 함께 검증합니다.

1. 설명 방식이 사용자의 명시적 선호와 확인된 이해 수준에 맞게 달라지는가.
2. 개인화 이후에도 출처·위험 고지·비권유·비실행 원칙이 그대로 유지되는가.

## 설계 원칙

- 모델이 설명을 만들고, 결정론 코드가 안전 조건을 검사합니다.
- 기억은 사건 단위로 추가합니다. 과거 기록을 조용히 고쳐 쓰지 않습니다.
- 설명 형식은 변경 후보가 될 수 있지만 위험성향·목표 변경은 사용자 확인이 필요합니다.
- 손익 결과만으로 사용자 성향이나 안전 규칙을 바꾸지 않습니다.
- 한 루프에서 한 항목만 바꾸며 같은 실패가 세 번 반복되면 중단합니다.
- 출처와 관찰 시각이 없으면 `BLOCKED_NEEDS_EVIDENCE`, 핵심 출처가 충돌하면 `BLOCKED_HUMAN_REVIEW`로 결론을 보류합니다.
- 평가는 수익률이 아니라 프로세스·안전·이해·추적 가능성을 봅니다.

## 저장소 구조

```text
plugins/calm-trade-growth-harness/   Codex 플러그인 원본
.agents/plugins/marketplace.json     repo-local 테스트용 marketplace
docs/IMPLEMENTATION-SPEC.md          공개 구현 명세
docs/PORTFOLIO-BRIEF.md              현수봇과 연결한 포트폴리오 구조
docs/PORTFOLIO-CASE-STUDY.md         공개용 표준 케이스 스터디
docs/PORTFOLIO-COPY-KIT.md           이력서·면접 재사용 문구
docs/PORTFOLIO-PUBLISH-PLAN.md       공개 발행과 사용자 검증 계획
docs/USER-RESEARCH-PLAN.md           초보 사용자 모집·테스트 절차
docs/portfolio-evidence.json         공개 가능한 replay 증거 스냅샷
docs/EVIDENCE-MAP.md                 주장과 검증 증거 매핑
docs/HACKATHON-ANSWERS.md            제출 문항 1~5 답변 초안과 글자 수
docs/DEMO-SCENARIO.md                정상·차단·성향 변경 재현 절차
docs/WRITING-POLICY.md               공개 글·제품 문구 편집 규칙
_dev/                                Codex 내부 작업 지시와 RETURN, git 제외
logs/privacy-safe/                   개인정보 제거 재구성 개발 맥락, git 제외
dist/                                submission.zip, git 제외
```

## Codex 플러그인

플러그인 원본은 `plugins/calm-trade-growth-harness/`에 둡니다. 사용 문서와 스크립트 경로는 `plugins/calm-trade-growth-harness/README.md`에 정리했습니다. 출력 초안 검증은 `plugins/calm-trade-growth-harness/scripts/validate_output.py`를 통해 수행합니다.

## 검증 요약

- 단위 테스트: `29`개 통과. 선호 변경 단일 필드 규칙, 확인 없는 material 변경 차단, 삭제 뒤 감사 이벤트 ID 고유성, forget 영수증, 패키징 금지 경로와 비밀 탐지, JSONL 명령의 편집 표식 오탐 방지, 공개 증거 export의 주장 경계까지 포함합니다.
- replay 평가: `dist/replay-report.md`, `dist/replay-metrics.json`, `dist/replay-trace.jsonl` 생성. `30`회 실행은 `15 PASS / 15 expected FAIL`이며, 설명 프로필이 달라도 안전 verdict와 blocked 이유가 일치했습니다.
- 플러그인·스킬 검증: 로컬 plugin validator와 skill validator가 모두 통과했습니다.

## 해커톤 기원

카투사는 카카오페이증권 문제를 대상으로 한 해커톤 프로토타입에서 시작했습니다. 제출용 ZIP과 개발 대화 기록은 포트폴리오 공개 범위에서 제외합니다. 현재 저장소의 정본은 플러그인 구현, 재현 가능한 테스트, 케이스 스터디와 사용자 검증 계획입니다.

## 포트폴리오 연결

이 프로젝트는 [현수봇](https://github.com/ljhljh0703-cmd/binance-trading-bot)과 같은 코드베이스로 합치지 않습니다. 두 프로젝트는 다음 질문에 대한 연속 사례로 묶습니다.

> 도메인의 실패 조건이 달라지면 AI 에이전트를 감싸는 하네스는 어떻게 달라져야 하는가?

- 현수봇: 퀀트형 자동매매 시스템에서 AI 판단이 주문으로 이어지기 전 행동을 제한했습니다.
- 카투사: 초보자 친화형 헤르메스 하네스로, 기억·개인화가 안전 기준을 침범하지 않게 제한합니다.
- 공통점: 모델보다 하네스, 결과보다 과정 증거, 자동 변경보다 제안·검증·승인 루프를 우선합니다.

## 공개 근거

- [카카오페이증권 인터뷰](https://www.youtube.com/watch?v=aBuoojGjyf4)
- [금융위원회 금융소비자보호 안내](https://www.fsc.go.kr/po020201/75646)
- [Codex 플러그인 작성 문서](https://learn.chatgpt.com/docs/build-plugins)
- [현수봇 공개 저장소](https://github.com/ljhljh0703-cmd/binance-trading-bot)

## 주장 경계

- 해커톤 프로토타입이며 카카오페이증권의 공식 제품이 아닙니다.
- 투자 자문, 종목 추천, 주문 실행, 수익 보장을 제공하지 않습니다.
- 구현과 테스트는 위 검증 명령으로 확인한 범위에서만 완료로 표현합니다.
- 현수봇 평가 수치는 dry-run 프로세스 지표이며 실거래 수익률이 아닙니다.

## 개발 시작

Codex는 `_dev/AGENTS.md`와 최신 `_dev/DISPATCH-*.md`를 읽고 구현합니다. `_dev/`는 공개 저장소와 해커톤 ZIP에서 제외합니다.
