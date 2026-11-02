# 테스트 보고서 · 실행 로그 분석

- 이름:
- 사용한 CLI 에이전트: codex / claude / agy
- 워크플로우 파일: `my-work/log-report.json`, `my-work/log-summary.json`, `my-work/helpdesk.json`, `my-work/weekly.json`, `my-work/slo-alert.json`

## 1. 통과한 테스트

| 테스트 파일 | 결과 |
| --- | --- |
| `cases/lab01.json` (지표) | Passed  /5 |
| `cases/lab01-edges.json` (경계, 재기만) | Passed  /6 |
| `cases/lab01-challenge.json` (날짜별 · 릴리스별) | Passed  /6 |
| `cases/lab01-challenge2.json` (단계 · 비용) | Passed  /5 |
| `cases/lab02.json` (실패 묶음 · 답 못 한 주제 · 이상 시간대) | Passed  /6 |
| `cases/lab02-periods.json` (기간을 바꾸면, 재기만) | Passed  /5 |
| `cases/lab02-challenge.json` (다시 묻는 주제) | Passed  /5 |
| `cases/lab02-challenge2.json` (요약 · 숫자 확인) | Passed  /3 |
| `cases/replay-after.json` (고친 뒤 다시 돌리기) | Passed  /10 |
| `cases/lab03.json` (고치기 전 · 후) | Passed  /4 |
| `cases/lab03-slo.json` (SLO) | Passed  /4 |
| `cases/replay-normal.json` · `lab03-cost.json` (고친 것의 대가, 재기만) | Passed  /10 · /4 |
| `cases/lab03-challenge.json` (주간 보고) | Passed  /7 |
| `cases/lab03-challenge2.json` (SLO 알림) | Passed  /6 |

## 2. 실패와 고친 내용

| 실패한 케이스 | 처음 결과 | 내가 생각한 원인 (어느 정의?) | 에이전트가 고친 곳 | 고친 뒤 |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

## 3. 지표 정의에서 헷갈린 것

- 

## 4. 아직 숫자로 모르는 것

- 
