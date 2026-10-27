# 테스트 보고서 · 보안 IT 문의 Agent

- 이름:
- 사용한 CLI 에이전트: codex / claude / agy
- 워크플로우 파일: `my-work/secure-agent.json`

## 1. 통과한 테스트

| 테스트 파일 | 결과 |
| --- | --- |
| `cases/lab01-attacks.json` (공격 9) | Passed  /9 (`open-it-agent`는  /9) |
| `cases/lab01.json` (입력 검증 · 규칙) | Passed  /8 |
| `cases/lab01-challenge.json` (알려진 공격 10 · 정상 10) | Passed  /20 |
| `cases/lab01-challenge2.json` (숨긴 공격 5 · 정상 4) | Passed  /9 |
| `cases/lab02.json` (본인 건 · 비밀) | Passed  /6 |
| `cases/lab02-challenge.json` (새 공격 8 · 정상 10) | Passed  /18 |
| `cases/lab02-challenge2.json` (판별 LLM 멈춤) | Passed  /4 |
| `cases/lab03.json` (출력 필터 · 기록) | Passed  /6 |
| `cases/lab03-layers.json` (관문별) | Passed  /5 |
| `cases/lab03-challenge2.json` (감사 로그 · 보안 요약) | Passed  /5 |
| `cases/my-cases.json` | Passed  / |

## 2. 실패와 고친 내용

| 실패한 케이스 | 처음 결과 | 내가 생각한 원인 | 에이전트가 고친 곳 | 고친 뒤 |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

## 3. 지나치게 막은 것 (정상인데 차단)

- 
