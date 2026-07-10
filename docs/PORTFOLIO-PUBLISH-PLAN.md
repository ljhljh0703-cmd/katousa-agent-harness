# 카투사 표준 포트폴리오 로드맵

Status: `GITHUB_PUBLICATION_IN_PROGRESS / USER_RESEARCH_PLANNED`

## 정본과 제외 범위

- 포트폴리오의 정본은 공개 GitHub 저장소다.
- 공개 서사는 `README.md`와 `docs/PORTFOLIO-CASE-STUDY.md`에서 시작한다.
- 해커톤 제출 ZIP, 원본 대화 로그, `_dev/`, `dist/`, `logs/`는 포트폴리오 자산과 공개 저장소에서 제외한다.
- 실제 사용자 검증 전에는 “이해도를 높였다”가 아니라 “이해도에 맞춰 설명을 바꾸는 구조를 구현했다”고 표현한다.

## Phase 1 — GitHub 공개 기반

목표: 기술 검토자가 clone과 테스트로 주장을 확인할 수 있게 한다.

- 저장소명: `katousa-agent-harness`
- 설명: `Beginner-friendly investment explanation agent with controlled memory, adaptation, and deterministic safety checks.`
- 토픽: `ai-agent`, `agent-harness`, `loop-engineering`, `financial-literacy`, `codex-plugin`, `ai-safety`
- 첫 공개 파일: 플러그인 소스, fixtures, tests, replay·포트폴리오 증거 생성기, 공개 문서
- 제외 파일: `_dev/`, `logs/`, `dist/`, `.calm-trade/`, cache, secret

완료 조건:

- [ ] 공개 저장소 URL 응답 확인
- [ ] 기본 브랜치 `main`
- [ ] README에서 케이스 스터디·증거·현수봇 링크 확인
- [ ] 새 clone에서 단위 테스트 29개 통과
- [ ] 새 clone에서 `scripts/export_portfolio_evidence.py` 재현
- [ ] 공개 후보 파일의 로컬 절대경로·이메일·비밀 문자열 0건

## Phase 2 — 읽히는 포트폴리오

목표: 기술을 모르는 채용 담당자는 30초 안에 차이를 이해하고, 기술 검토자는 5분 안에 증거까지 도달하게 한다.

핵심 메시지:

> 돈을 움직이는 AI는 행동을 통제하고, 사람에 맞춰 변하는 AI는 적응을 통제했습니다.

- 현수봇: 퀀트형 자동매매 에이전트의 행동 하네스
- 카투사: 초보 투자자에게 맞춰 성장하는 설명 에이전트의 헤르메스형 하네스

필요한 시각 자료:

1. 질문 → 출처 확인 → 설명 → 이해 확인 → 변경 후보 → 승인 흐름도
2. 같은 질문의 checklist·example·numbers 비교 화면
3. 출처 없는 급등 질문이 `BLOCKED_NEEDS_EVIDENCE`로 멈추는 화면
4. profile v1 → v2와 forget receipt를 함께 보여 주는 상태 변화 화면

권장 공개 묶음:

- GitHub README
- 상세 케이스 스터디
- 위 4장으로 만든 단일 HTML 또는 Notion 페이지
- 60~90초 무음 캡션 데모
- 이력서 bullet 2개와 30초 면접 답변

완료 조건:

- [ ] 모든 수치가 공개 증거 파일과 일치
- [ ] 모바일·인쇄 레이아웃 확인
- [ ] “공식 연동”, “투자 성과”, “실제 이해도 향상” 과장 표현 0건
- [ ] 헤르메스·하네스·replay를 첫 등장에 평어로 풀이
- [ ] 공개 URL과 GitHub commit SHA 고정

## Phase 3 — 초보 사용자 검증

목표: 카투사가 실제로 사용자의 판단을 대신하지 않으면서 위험과 부족한 정보를 이해시키는지 방향성 증거를 얻는다.

- 대상: 투자 경험이 적은 사용자 5~8명
- 방식: 1인 20~25분, 화면 공유 또는 대면
- 금지 수집: 계좌번호, 실제 보유 종목·금액, 주문 화면, 금융 신분 정보
- 핵심 과제: 비교 질문, 출처 없는 현재 정보, 설명 형식 변경
- 측정: 핵심 위험 재진술, 부족한 정보 식별, 판단 변경 조건 회상, 설명 선호, 과도한 확신 여부
- 결과 표현: 탐색적 사용자 테스트이며 통계적 효과나 투자 성과로 확대하지 않는다.

상세 절차와 모집 문구는 `docs/USER-RESEARCH-PLAN.md`를 따른다.

## 우선순위

1. 공개 저장소와 새 clone 재현
2. 시각 자료 4장
3. 사용자 5~8명 모집과 파일럿 1명
4. 본 테스트와 결과 요약
5. HTML·Notion 케이스 스터디 공개

기능 추가는 이 다섯 단계 뒤다. 지금 자산 가치를 높이는 병목은 새로운 모델이나 실시간 시세가 아니라 공개 재현성, 이해 가능한 시각화, 실제 사용자 증거다.
