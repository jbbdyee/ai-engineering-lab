# 테스트 보고서 · IT 헬프데스크 (비용)

- 이름:
- 사용한 CLI 에이전트: codex / claude / agy
- 워크플로우 파일: `my-work/cost.json`, `my-work/cost-report.json`

## 1. 통과한 테스트

| 테스트 파일 | 결과 |
| --- | --- |
| `cases/lab01.json` (비용) | Passed  /3 |
| `cases/lab01-challenge.json` (기록) | Passed  /4 |
| `cases/lab01-challenge2.json` (기록이 멈춰도) | Passed  /4 |
| `cases/lab02.json` (줄이기 · 모델) | Passed  /5 |
| `cases/lab02-challenge.json` (LLM 한 번 · $0.0002) | Passed  /7 |
| `cases/lab02-challenge2.json` (긴 질문) | Passed  /4 |
| `cases/lab03.json` (하루 예산) | Passed  /3 |
| `cases/lab03-limit.json` (사용자별 한도) | Passed  /4 |
| `cases/lab03-challenge.json` (비용 보고서) | Passed  /5 |
| `cases/lab03-challenge2.json` (바꾸면 얼마) | Passed  /5 |

## 2. 실패와 고친 내용

| 실패한 케이스 | 처음 결과 | 내가 생각한 원인 | 에이전트가 고친 곳 | 고친 뒤 |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

## 3. 싸진 만큼 잃은 것

- 

## 4. 질문 하나의 비용 (처음 → 끝)

| | 처음 (`base-cost`) | 끝 (`my-cost`) |
| --- | --- | --- |
| VPN 질문 비용 ($) |  |  |
| LLM 호출 |  |  |
| 하루 1,000건 · 22일 |  |  |
