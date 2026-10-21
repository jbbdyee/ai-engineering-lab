# Lab 01 · 복합 요청을 업무로 나누기

> **정답본** · 수업이 끝난 뒤 공개합니다. 문제는 [LAB-01-Q-SCENARIO-AND-SPLIT.md](LAB-01-Q-SCENARIO-AND-SPLIT.md).
> 68일차부터 수업 준비는 **정답 워크플로우만 한 번 실행해 확인**합니다. 아래 요청문은 예시이며, 수업 준비 때 CLI 에이전트로 보내 결과를 재지는 않았습니다. 결과 숫자는 정답 워크플로우(`reference/`, `answers/`)를 2026-10-18에 1회 실행한 값입니다 (gpt-4.1-mini).

- 관련 강의: [1단계 · 복합 업무 시나리오 분석](../../Lecture/68/01-STAGE1-COMPOSITE-SCENARIO.md)
- 소요 시간: 약 40분 (예제 1 10분 · 예제 2 15분 · 과제 15분)

## 예제 1 · 업무 분석표 (정답 예)

| 요청 | 업무 | 유형 | 필요한 입력 | 요청에 있나 | 관계 |
| --- | --- | --- | --- | --- | --- |
| `composite` | ① T-1002 처리 상태 ② 회의록 할 일 정리 ③ 프린터 출력 안 됨 | it · meeting · it | ① 접수 번호, 요청한 사람 ② 회의록 원문 ③ 증상 | 모두 있음 (`user`, `notes`) | 셋 다 독립 |
| `two-it` | ① 비밀번호 분실 ② 메일함 용량 | it · it | 증상, 요청한 사람 | 있음 | 독립 (같은 Agent에 두 번) |
| `it-and-other` | ① 프린터 ② 회식 장소 추천 | it · other | ① 증상 ② (맡을 Agent 없음) | ① 있음 | 독립 |
| `meeting-no-notes` | ① 회의록 할 일 정리 | meeting | 회의록 원문 | **없음** | — |

강조할 점:

- 업무 개수는 "접속사 수"가 아니라 **처리 단위**. `two-it`은 같은 Agent지만 업무 둘.
- 필요한 입력이 **문장 밖(요청 본문의 다른 칸)** 에 있다: `user`, `notes`. 업무 나누기 LLM에게는 문장만 줘도 되지만, 빠진 입력 판단은 본문 전체를 봐야 한다.
- 오늘 업무는 모두 **독립** → 라우터(분배)로 충분. "보고서를 쓰고 그걸 검토"처럼 순서가 있으면 파이프라인 (69일차).

## 예제 2 · 요청문 예

```text
my-work/split.json 에 n8n 워크플로우를 만들어 줘.
- POST 웹훅, 경로 my-split. 직원 요청 문장은 본문의 message.
- message가 비어 있으면 400 {"error": "message is required"}.
- AI Agent(OpenAI gpt-4.1-mini, Tool 없음)가 문장을 업무 목록으로 나눈다. 업무 하나 = 한 번에 처리할 수 있는 요청 하나.
  유형: it(비밀번호·계정·VPN·프린터·메일·소프트웨어, T-1002 같은 접수 현황), meeting(회의록 정리·할 일), other(그 밖).
  업무 텍스트는 직원이 쓴 한국어 그대로, 접수 번호를 지우지 않는다. JSON만 돌려 달라고 한다.
- 다음 Code 노드에서 그 글자를 JSON으로 읽는다. 앞뒤 ``` 는 지우고, 읽지 못하면 빈 목록. 정해지지 않은 유형은 other.
- 결과는 {"count": 업무 수, "tasks": [{"type": "it", "text": "..."}]} (요청에 나온 순서대로).
- 기대 결과는 cases/lab01.json. check까지 하고 push·test 명령을 알려 줘.
```

정답: [reference/lab01-example2-split.json](reference/lab01-example2-split.json) (Webhook → Has message? → Split tasks(Agent) → Parse tasks(Code) → Send result).

| 수업 준비 때 결과 | |
| --- | --- |
| `cases/lab01.json` | 7/7 (케이스당 0.9~3.2초, 복합 요청이 가장 김) |
| `cases/lab01-challenge.json` (예제 상태) | 0/4 (`agent`, `missing` 필드 없음) |

## 과제 · 요청문 예

```text
my-work/split.json 을 고쳐 줘. LLM 지시문(Split tasks)은 그대로 두고 Parse tasks 코드에서만 정한다.
1. 업무마다 agent: it → "it-agent", meeting → "meeting-agent", other → "담당자 연결".
2. 업무마다 missing: 빠진 입력 목록. meeting인데 본문 notes가 비었으면 ["notes"], it인데 본문 user가 비었으면 ["user"], 아니면 [].
   본문은 $('Assistant webhook').first().json.body 로 읽는다.
3. cases/lab01-challenge.json 과 cases/lab01.json 이 둘 다 통과해야 한다.
```

정답: [answers/68-lab01-challenge-split.json](answers/68-lab01-challenge-split.json)

| 수업 준비 때 결과 | |
| --- | --- |
| `cases/lab01-challenge.json` | 4/4 |
| `cases/lab01.json` | 7/7 |

풀이 포인트:

- **LLM이 할 일(문장 이해)** 과 **규칙이 할 일(담당 표, 빈 칸 확인)** 을 나눴다. 규칙 쪽은 매번 같은 답 → 테스트가 흔들리지 않는다 (67일차 "LLM이 정하면 안 되는 값"과 같은 생각).
- `user` 빠짐은 테스트에 없지만 넣어 두면 Lab 03 과제의 "user 없이 IT 질문"에서 바로 쓴다.
