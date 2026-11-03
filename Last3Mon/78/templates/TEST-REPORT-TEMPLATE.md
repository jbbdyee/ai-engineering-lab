# 테스트 보고서 · 데이터 품질 검사

- 이름:
- 사용한 CLI 에이전트: codex / claude / agy
- 워크플로우 파일: `my-work/faq-check.json`, `my-work/faq-import.json`, `my-work/check.json`, `my-work/quality-report.json`

| 테스트 파일 | 결과 |
| --- | --- |
| `cases/lab01.json` (규칙) | Passed  /5 |
| `cases/lab01-edges.json` (경계, 에이전트 없이) | Passed  /6 |
| `cases/lab01-challenge.json` (기존 데이터) | Passed  /4 |
| `cases/lab01-challenge2.json` (고침 목록) | Passed  /5 |
| `cases/lab02.json` (게이트 · 격리 · LLM) | Passed  /6 |
| `cases/lab02-gate.json` (기준을 바꾸면, 에이전트 없이) | Passed  /6 |
| `cases/lab02-challenge.json` (품질 기록 · 알림) | Passed  /5 |
| `cases/lab02-challenge2.json` (LLM 호출 수, 세 번) | Passed  /3 · /3 · /3 |
| `cases/lab03.json` (스키마) | Passed  /4 |
| `cases/lab03-fix.json` (고쳐서 다시) | Passed  /4 |
| `cases/lab03-schema.json` (새 스키마, 에이전트 없이) | Passed  /5 |
| `cases/lab03-challenge.json` (품질 보고서) | Passed  /4 |
| `cases/lab03-challenge2.json` (데이터셋별) | Passed  /4 |

## 실패와 고친 내용

| 실패한 케이스 | 처음 결과 | 내가 생각한 원인 | 에이전트가 고친 곳 | 고친 뒤 |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

## 규칙에서 헷갈린 것

-
