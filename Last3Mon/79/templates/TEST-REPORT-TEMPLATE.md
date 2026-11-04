# 테스트 보고서 · Workflow Ops Assistant

- 이름:
- 사용한 CLI 에이전트: codex / claude / agy
- 워크플로우 파일: `my-work/ops-facts.json`, `my-work/ops-ask.json`, `my-work/ops-brief.json`, `my-work/ops-eval.json`

| 테스트 파일 | 결과 |
| --- | --- |
| `cases/lab01.json` (운영 사실) | Passed  /5 |
| `cases/lab01-period.json` (기간을 바꾸면, 에이전트 없이) | Passed  /5 |
| `cases/lab01-challenge.json` (영역별 상태) | Passed  /5 |
| `cases/lab01-challenge2.json` (출처가 멈추면) | Passed  /3 |
| `cases/lab02.json` (라우터 · 거절 · 숫자 확인) | Passed  /6 |
| `cases/lab02-phrasing.json` (질문을 바꾸면, 에이전트 없이) | Passed  /6 |
| `cases/lab02-challenge.json` (LLM 라우터) | Passed  /5 |
| `cases/lab02-challenge2.json` (감사 기록) | Passed  /5 |
| `cases/lab03.json` (브리핑) | Passed  /4 |
| `cases/lab03-llm.json` (요약) | Passed  /2 |
| `cases/lab03-after.json` (아침이 바뀌면, 에이전트 없이) | Passed  /5 |
| `cases/lab03-challenge.json` (골든 질문 평가) | Passed  /3 |
| `cases/lab03-challenge2.json` (평가 관문) | Passed  /4 |

## 실패와 고친 내용

| 실패한 케이스 | 처음 결과 | 내가 생각한 원인 | 에이전트가 고친 곳 | 고친 뒤 |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

## 도우미가 틀린 답 (숫자는 맞는데 뜻이 틀린 것 포함)

-
