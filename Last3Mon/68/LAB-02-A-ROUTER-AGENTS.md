# Lab 02 · 여러 Agent에게 나눠 맡기는 라우터

> **정답본** · 수업이 끝난 뒤 공개합니다. 문제는 [LAB-02-Q-ROUTER-AGENTS.md](LAB-02-Q-ROUTER-AGENTS.md).
> 요청문은 예시이며 CLI 에이전트로 보내 재지는 않았습니다. 결과 숫자는 정답 워크플로우를 2026-10-18에 1회 실행한 값입니다 (gpt-4.1-mini).

- 관련 강의: [2단계 · Multi-Agent 워크플로우 설계](../../Lecture/68/02-STAGE2-MULTI-AGENT-DESIGN.md)
- 소요 시간: 약 70분 (예제 1 10분 · 예제 2 25분 · 과제 35분)

## 예제 1 · Agent 계약 (정답)

| Agent | 맡는 업무 | 웹훅 | 입력 | 결과 | 실패할 때 |
| --- | --- | --- | --- | --- | --- |
| IT 문의 (67일차) | it | `POST /webhook/it-agent` | `question`, `user` 필수 | `route`, `answer`, `tools_used`, `sources` | 입력 없음 400 · 근거 없음·남의 접수 건은 `route: 담당자 연결` |
| 회의록 (66일차) | meeting | `POST /webhook/meeting-agent` | `title`, `notes`(필수) | `route`, `title`, `count`, `summary`, `actions[{owner, task, due}]` | `notes` 없음 400 `{"error": "notes are required"}` |

수업 준비 때 직접 부른 결과: `it-agent` + `agent-it.json` 4.8초 (`Get_ticket`, "처리 중"), `meeting-agent` + `agent-meeting.json` 2.3초 (할 일 4개, 담당 미정 1개), `notes` 없이 400.

요청문 예:

```text
agents/ 폴더의 두 워크플로우를 읽고 my-work/DESIGN.md 2절 표를 채워 줘. 워크플로우는 만들지 마.
칸: Agent, 맡는 업무, 웹훅(메서드와 경로), 입력(필수 표시), 결과 필드 이름, 실패할 때 돌려주는 것(HTTP 코드와 본문).
근거가 된 노드 이름도 표 아래에 적어 줘.
```

## 예제 2 · 라우터 요청문 예

```text
my-work/split.json 을 바탕으로 my-work/assistant.json 을 새로 만들어 줘 (split.json 은 그대로).
- 웹훅 경로 my-assistant. 본문: message, user, (있으면) title, notes.
- 나누기 결과를 업무 하나당 항목 하나로 바꾸고 index(1부터)를 붙인다.
- Switch로 type별 갈래: it → HTTP POST http://localhost:5678/webhook/it-agent  본문 {question: 업무 text, user: 웹훅 body.user}
  meeting → HTTP POST http://localhost:5678/webhook/meeting-agent  본문 {title, notes: 웹훅 body 그대로}
  other → Agent를 부르지 않고 route "담당자 연결", answer "IT 문의와 회의록 정리 말고는 도와드릴 수 없어 담당자에게 전달했습니다."
- 갈래마다 결과를 같은 모양으로: index, type, text, agent, route, answer. 회의록은 answer에 summary와 "할 일: 담당 - 일 (기한)" 목록, actions도 남김.
- Merge로 모으고 Aggregate로 results 배열 하나로, Code에서 index 순으로 정렬해 {count, results, reply} 를 만든다. reply는 업무마다 한 줄씩.
- 기대 결과 cases/lab02.json. AGENTS.md 5절 노드를 써 줘.
```

정답: [reference/lab02-example2-router.json](reference/lab02-example2-router.json) — 일부러 `neverError`를 넣지 않았고 빠진 입력도 보지 않습니다 (Lab 03에서 드러남).

| 수업 준비 때 결과 (1회) | |
| --- | --- |
| `cases/lab02.json` | 6/6 |
| 시간 | 복합(업무 3개) 6.6초 · IT 하나 2.6초 · 회의록 3.5초 · IT+기타 2.8초 · 기타만 0.9초 (Agent를 부르지 않음) |
| 직접 `call` 복합 요청 | 4.8초, `results` 3개 (T-1002 "처리 중", 할 일 4개, 프린터 FAQ) |

풀이 포인트:

- 라우터 = **정해진 흐름**(Switch). 어떤 Agent를 부를지는 유형 표가 정하고, LLM은 나누기만 한다.
- 결과 모양 맞추기(Set 셋)가 계약을 지키는 곳. Agent가 바뀌어도 라우터 결과 모양은 그대로.
- 기타만 0.9초: LLM 한 번(나누기)뿐. 회의록·IT 시간은 각 Agent 시간 + 나누기.

## 과제 · Supervisor 요청문 예

```text
my-work/supervisor.json 을 새로 만들어 줘 (라우터와 별도). 웹훅 경로 my-supervisor, 입력은 라우터와 같음, message 비면 400.
- AI Agent 하나(Supervisor, gpt-4.1-mini, returnIntermediateSteps true)가 Tool 둘을 쓴다.
  Ask IT agent: HTTP Request Tool POST http://localhost:5678/webhook/it-agent, question은 $fromAI, user는 웹훅 body.user (LLM이 정하지 않음)
  Ask meeting agent: POST .../meeting-agent, title·notes는 웹훅 body 그대로, LLM은 request(무엇을 원하는지)만 채움
- 지시문: 직접 답하지 말 것. IT 질문마다 Ask_IT_agent 한 번, 회의록 요청이면 Ask_meeting_agent 한 번.
  그 밖의 요청은 Tool을 부르지 말고 정확히 "그 요청은 담당자에게 전달했습니다." Tool 결과의 이름·날짜·상태는 그대로.
- 다음 Code에서 intermediateSteps의 Tool 이름으로 agents_used(겹치지 않게)를 만들고 {reply, agents_used} 를 돌려준다.
- 기대 결과 cases/lab02-challenge.json.
```

정답: [answers/68-lab02-challenge-supervisor.json](answers/68-lab02-challenge-supervisor.json)

| 수업 준비 때 결과 | |
| --- | --- |
| 처음 (기타 요청 지시가 "직원이 도와준다고 말하라") | `lab02-challenge` 4/5 · 기타만: "회식 장소 추천은 **담당 직원**이 도와드릴 예정입니다" → `담당자` 없음 |
| 지시를 "정확히 '그 요청은 담당자에게 전달했습니다.'"로 바꾼 뒤 | 5/5 |
| 복합 요청 시간 (3번 측정) | Supervisor 10.5 · 9.6 · 10.8초 / 라우터 6.6 · 4.7 · 4.5초 |
| `test cases/lab02.json --webhook my-supervisor` | 1/6 (빈 요청만 통과: `count`, `results`가 없음 = 계약이 다름) |

비교 표 (풀이 때 함께 채움):

| | 라우터 | Supervisor |
| --- | --- | --- |
| 누가 Agent를 고르나 | 유형 표 (코드) | LLM |
| 복합 요청 시간 (수업 준비) | 4.5~6.6초 | 9.6~10.8초 (LLM이 Tool마다 판단하고 마지막에 답을 다시 씀) |
| 결과 모양 | 계약 그대로 (`results[]`) | 글자 답 하나, 업무별 결과는 없음 |
| 테스트하기 | 업무별 `results.N.*`로 정확히 | 답 글자에 낱말이 있는지 정도 |
| Agent 하나 더 | Switch 갈래 + 결과 Set 추가 | Tool 하나 + 지시문 한 줄 |
| 어울리는 곳 | 업무 종류가 정해져 있고 결과를 시스템이 다시 씀 | 요청이 열려 있고 사람에게 바로 답만 주면 됨 |

- 지시문의 낱말 하나로 4/5 ↔ 5/5가 갈렸다: **Supervisor는 지시문이 곧 분배 규칙**이라 흔들리는 곳이 많다.
