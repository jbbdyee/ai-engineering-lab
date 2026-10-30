# 테스트 보고서 · 문의 일괄 접수 (에러 처리)

- 이름:
- 사용한 CLI 에이전트: codex / claude / agy
- 워크플로우 파일: `my-work/intake.json`, `my-work/error-handler.json`, `my-work/replay.json`, `my-work/ops-status.json`

## 1. 통과한 테스트

| 테스트 파일 | 결과 |
| --- | --- |
| `cases/lab01.json` (항목 확인 · 재시도 · 중복 없음) | Passed  /6 |
| `cases/lab01-faults.json` (고장 종류마다, 재기만) | Passed  /5 |
| `cases/lab01-challenge.json` (LLM 멈춤) | Passed  /3 |
| `cases/lab01-challenge2.json` (같은 id · 10건 상한) | Passed  /4 |
| `cases/lab02.json` (DLQ · Error Workflow) | Passed  /4 |
| `cases/lab02-nets.json` (그물 지도) | Passed  /7 |
| `cases/lab02-challenge.json` (처리한 실패 알림 · DLQ가 멈추면) | Passed  /6 |
| `cases/lab02-challenge2.json` (알림 폭주 막기) | Passed  /6 |
| `cases/lab03.json` (재처리) | Passed  /5 |
| `cases/lab03-drill.json` (장애 연습) | Passed  /7 |
| `cases/lab03-half.json` (반쯤 처리된 요청, 재기만) | Passed  /6 |
| `cases/lab03-challenge.json` (세 번 실패하면 멈춤) | Passed  /7 |
| `cases/lab03-challenge2.json` (운영 상태) | Passed  /7 |

## 2. 실패와 고친 내용

| 실패한 케이스 | 처음 결과 | 내가 생각한 원인 | 에이전트가 고친 곳 | 고친 뒤 |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

## 3. 아직 잃을 수 있는 것

- 
