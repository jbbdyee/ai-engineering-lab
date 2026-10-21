# Lab 03 · 빠진 입력, 꺼진 Agent, 어려운 테스트

> **정답본** · 수업이 끝난 뒤 공개합니다. 문제는 [LAB-03-Q-VERIFY-AND-ISOLATE.md](LAB-03-Q-VERIFY-AND-ISOLATE.md).
> 요청문은 예시이며 CLI 에이전트로 보내 재지는 않았습니다. 결과 숫자는 정답 워크플로우를 2026-10-18에 1회 실행한 값입니다 (gpt-4.1-mini).

- 관련 강의: [3단계 · 검증과 장애 격리, 확장 고려](../../Lecture/68/03-STAGE3-VERIFY-AND-SCALE.md)
- 소요 시간: 약 80분 (예제 1 20분 · 예제 2 20분 · 과제 40분)

## 고치기 전 (Lab 02 예제 정답 `reference/lab02-example2-router.json`)

| 테스트 | 결과 | 원인 |
| --- | --- | --- |
| `cases/lab03.json` | 4/5 | 회의록 없는 회의 요청 → **HTTP 500** (회의록 Agent가 400을 돌려주자 `Call meeting agent`가 멈추고 전체가 멈춤) |
| `off agents/meeting-agent.json` 후 `cases/lab03-down.json` | 1/3 | 복합 요청 → **HTTP 500**, T-1002 답까지 사라짐 (404에 멈춤). IT만 요청은 통과 |

## 답안 읽는 법 · 요청과 응답 대조 (수업 준비 실측)

Lab 03 답안은 새 워크플로우가 아니라 **Lab 02 라우터를 고친 판**입니다. 노드 구성은 같고 몇 곳만 바뀝니다. 아래 JSON은 2026-10-18 수업 준비 때 `flow.py test`가 남긴 보고서(`runs/*.json`, git 제외)에서 그대로 옮겼습니다 (회의록 `notes`만 `…`로 줄임).

| 판 | 파일 | 보고서 |
| --- | --- | --- |
| 고치기 전 | `reference/lab02-example2-router.json` | `lab03` 4/5 (`runs/lab03-20261018-003309.json`) · `lab03-down` 1/3 (`…-003325`) |
| 예제 1 + 2 | `reference/lab03-example2-isolated.json` | `lab03` 5/5 (`…-003414`) · `lab03-down` 3/3 (`…-003351`) · 과제 케이스 5/7 (`68-lab03-challenge-cases-…-003950`) |
| 과제 최종 | `answers/68-lab03-challenge-final.json` | 과제 케이스 7/7 (`…-003826`) |

```text
웹훅 → Has message? → Split tasks(LLM) → Parse tasks(Code) → One item per task
     → Route by type(Switch) ─it──────────→ Call IT agent ──────→ IT result ──────┐
                             ├meeting─────→ Call meeting agent ─→ Meeting result ─┤
                             ├other───────→ Other result ─────────────────────────┼→ Collect results → All results → Build reply → 응답
                             └needs input─→ Need input (예제 1에서 새로 생김) ───────┘
```

### 대조 1 · 예제 1 · 회의록 없는 회의 요청

보낸 요청 (`requests/meeting-no-notes.json`, 두 판 같음):

```json
{"message": "이번 회의록 할 일 정리 부탁해요", "user": "김민지"}
```

| 고치기 전 · HTTP 500 · 1.0초 | 예제 1 뒤 · HTTP 200 · 2.3초 |
| --- | --- |
| `{"message": "Error in workflow"}` | 아래 JSON |

```json
{
  "count": 1,
  "results": [
    {"index": 1, "type": "meeting", "text": "이번 회의록 할 일 정리 부탁해요",
     "agent": "meeting-agent", "route": "입력 필요",
     "answer": "회의록 정리를 하려면 회의록 내용(notes)을 함께 보내 주세요."}
  ],
  "reply": "1. 이번 회의록 할 일 정리 부탁해요\n   → [입력 필요] 회의록 정리를 하려면 회의록 내용(notes)을 함께 보내 주세요."
}
```

읽는 법:

- **고치기 전 500의 원인**: 라우터가 회의록 Agent를 그대로 불렀고, 회의록 Agent는 계약대로 `notes`가 없으면 HTTP 400 `{ "error": "notes are required" }`를 돌려줍니다 (`agents/meeting-agent.json`의 `Reject empty` 노드). `Call meeting agent`가 400에 멈추자 라우터 **전체**가 `Error in workflow`(500)가 됐습니다. 수업에서는 `call meeting-agent requests/meeting-no-notes.json`으로 이 400을 직접 보여 줍니다.
- **고친 곳 ① `Parse tasks`(Code)**: 업무마다 `agent`와 `missing`을 코드로 붙입니다 (LLM이 정하지 않음).
  ```js
  const AGENT = { it: 'it-agent', meeting: 'meeting-agent', other: '담당자 연결' };
  if (task.type === 'meeting' && !String(body.notes ?? '').trim()) missing.push('notes');
  if (task.type === 'it' && !String(body.user ?? '').trim()) missing.push('user');
  ```
- **고친 곳 ② `Route by type`(Switch)**: 위에서부터 **처음 맞는 갈래 하나**로만 갑니다 (옵션 비어 있음 = 기본값).

  | 출력 | 조건 |
  | --- | --- |
  | 0 it | `type = it` |
  | 1 meeting | `type = meeting` **그리고 missing 0개** |
  | 2 other | `type = other` |
  | 3 needs input | missing 1개 이상 |

  회의록 없는 회의 업무는 1번에 걸리지 않고 3번으로 → **Agent를 부르지 않음**.
- **고친 곳 ③ `Need input`(Set)**: `route: 입력 필요`와 답 문장을 바로 만들어 Merge 3번 입력으로. 응답 `results.0.route`가 테스트 기대 `입력 필요`와 같습니다.
- 응답 모양(`count`, `results[]`의 `index · type · text · agent · route · answer`, `reply`)은 Lab 02와 같습니다. 그래서 `lab02`도 계속 6/6 (`runs/lab02-20261018-003429.json`).

### 대조 2 · 예제 2 · 회의록 Agent 꺼짐 + 복합 요청

`off agents/meeting-agent.json` 뒤 보낸 요청 (`requests/composite.json`, 두 판 같음):

```json
{"message": "T-1002 처리 상태 알려주고, 첨부한 회의록에서 할 일도 정리해줘. 그리고 프린터 출력이 안 돼요.",
 "user": "박서연", "title": "10월 16일 주간 회의", "notes": "참석: 김민지, 이준호, 박서연. 1) …"}
```

| 고치기 전 · HTTP 500 · 4.3초 | 예제 2 뒤 · HTTP 200 · 4.6초 |
| --- | --- |
| `{"message": "Error in workflow"}` — **T-1002 답도 없음** | 아래 JSON |

```json
{
  "count": 3,
  "results": [
    {"index": 1, "type": "it", "text": "T-1002 처리 상태 알려줘", "agent": "it-agent", "route": "자동 답변",
     "answer": "T-1002 티켓은 현재 \"처리 중\" 상태이며, VPN 인증서 발급 승인 대기 중입니다. 10월 20일에 완료될 예정입니다."},
    {"index": 2, "type": "meeting", "text": "첨부한 회의록에서 할 일 정리", "agent": "meeting-agent", "route": "담당자 연결",
     "answer": "담당 Agent가 응답하지 않아 담당자에게 전달했습니다.", "actions": []},
    {"index": 3, "type": "it", "text": "프린터 출력이 안 돼요", "agent": "it-agent", "route": "자동 답변",
     "answer": "프린터 전원과 네트워크 연결을 확인하고, 인쇄 대기열을 비운 뒤 다시 출력해 보세요."}
  ],
  "reply": "1. T-1002 처리 상태 알려줘\n   → [자동 답변] …\n2. 첨부한 회의록에서 할 일 정리\n   → [담당자 연결] 담당 Agent가 응답하지 않아 담당자에게 전달했습니다.\n3. 프린터 출력이 안 돼요\n   → [자동 답변] …"
}
```

읽는 법:

- **고치기 전**: 4.3초 동안 IT 업무 둘은 이미 답을 받았지만, 꺼진 회의록 Agent의 **404**(게시 해제된 웹훅)에 `Call meeting agent`가 멈춰 전체가 500. 받아 둔 답까지 버려졌습니다. 같은 보고서에서 "회의록만"도 500, "IT만"은 회의록 Agent를 안 부르니 200.
- **고친 곳 ① `Call IT agent` · `Call meeting agent`**: `options.response.response.neverError: true` (timeout 60000은 원래 있음). 404 · 400 · 500도 멈추지 않고 응답을 다음 노드로 넘깁니다.
- **고친 곳 ② `IT result` · `Meeting result`(Set)**: 빈 칸을 대체 값으로.

  | 칸 | 고치기 전 | 고친 뒤 |
  | --- | --- | --- |
  | `route` | `{{ $json.route \|\| '오류' }}` | `{{ $json.route \|\| '담당자 연결' }}` |
  | `answer` (회의록) | 요약이 없으면 `$json.error` | 요약이 없으면 `'담당 Agent가 응답하지 않아 담당자에게 전달했습니다.'` |

  정상 응답에는 `route`가 있으니 그대로, 꺼진 Agent의 응답에는 없으니 대체 값. 그래서 `results.1`만 `담당자 연결`, `results.0` · `results.2`는 그대로 `자동 답변`.
- 시간 4.6초: 나누기 약 1초 + IT 둘(한 HTTP 노드가 **동시에**) + 회의록(404라 바로 끝남).

### 대조 3 · 과제 · user 없이 IT 질문 (예제 2 판에서 실패)

보낸 요청 (과제 케이스 `body`, 두 판 같음) · 기대 `results.0.route = 입력 필요`:

```json
{"message": "VPN이 계속 끊겨요"}
```

| 예제 2 판 · 200 · 2.3초 · ✘ | 최종 · 200 · 3.0초 · ✔ |
| --- | --- |
| `"route": "담당자 연결"`, `"answer": "담당 Agent가 응답하지 않아 담당자에게 전달했습니다."` | `"route": "입력 필요"`, `"answer": "누가 요청했는지(user)를 함께 보내 주세요."` |

```json
{"count": 1, "results": [{"index": 1, "type": "it", "text": "VPN이 계속 끊겨요", "agent": "it-agent",
  "route": "입력 필요", "answer": "누가 요청했는지(user)를 함께 보내 주세요."}],
 "reply": "1. VPN이 계속 끊겨요\n   → [입력 필요] 누가 요청했는지(user)를 함께 보내 주세요."}
```

읽는 법:

- 예제 2 판에서도 `Parse tasks`는 `missing: ["user"]`를 붙였습니다. 그런데 Switch의 **it 조건에 "missing 0개"가 없어** 첫 갈래(it)에 먼저 걸렸고, IT Agent가 계약대로 400(`user` 필수) → 예제 2의 대체 값 → `담당자 연결`. **장애가 아닌데 장애로 처리**한 것입니다. 응답만 보면 "Agent가 응답하지 않아"라고 거짓말을 합니다.
- **최종에서 고친 곳**: Switch 0번 it에 `missing 0개` 조건을 더함 → needs input으로. `Need input`의 `agent`는 원래 담당(`{{ $('Route by type').item.json.agent }}`), 답은 빠진 것에 따라: `missing.includes('notes') ? '회의록 정리를 하려면 …' : '누가 요청했는지(user)를 함께 보내 주세요.'`

### 대조 4 · 과제 · 공백만 보냄 (예제 2 판에서 실패)

보낸 요청 · 기대 HTTP 400:

```json
{"message": "   ", "user": "이준호"}
```

| 예제 2 판 · 200 · 0.7초 · ✘ | 최종 · 400 · 0.1초 · ✔ |
| --- | --- |
| 응답 본문이 **빈 글자** `""` | `{"error": "message is required"}` |

읽는 법:

- 예제 2 판의 `Has message?`는 `{{ $json.body.message }}`가 notEmpty인지 봅니다. 공백 세 칸은 "비어 있지 않음"이라 통과합니다. 보고서의 빈 응답과 0.7초(나누기 LLM 한 번)로 보아, LLM이 업무 0개를 돌려주고 `One item per task`가 항목 0개를 내보내 뒤 노드(Respond 포함)가 실행되지 않은 것입니다. Respond 노드가 실행되지 않으면 n8n은 **빈 200**을 돌려줍니다.
- **최종에서 고친 곳**: `Has message?`의 왼쪽 값을 `{{ String($json.body.message ?? '').trim() }}`으로 → 공백을 지우면 빈 글자 → `Reject empty` 400. LLM을 부르지도 않아 0.1초.

### 한 줄로

| 실패 | 막는 곳 | 대조에서 본 것 |
| --- | --- | --- |
| 고칠 수 있는 실패 (빠진 입력) | **부르기 전** (Parse tasks + Switch + Need input) | 500 → 200 `입력 필요`, 무엇이 빠졌는지 알려 줌 (대조 1 · 3) |
| 고칠 수 없는 실패 (Agent 꺼짐) | **부른 뒤** (`neverError` + 결과 Set 대체 값) | 500 → 200, 그 업무만 `담당자 연결` (대조 2) |
| 입력 검사의 구멍 | 웹훅 바로 뒤 (`Has message?`) | 빈 200 → 400, LLM 호출 없음 (대조 4) |

## 예제 1 · 요청문 예

- 시나리오는 새로 만들지 않습니다. `requests/meeting-no-notes.json`(회의록 없는 회의 요청) 하나, 고칠 파일은 `my-work/assistant.json`, 테스트는 이미 있는 `cases/lab03.json`.
- 시작: `call my-assistant requests/meeting-no-notes.json` → HTTP 500, `call meeting-agent requests/meeting-no-notes.json` → HTTP 400 `{"error": "notes are required"}`. 이 두 결과를 나란히 놓고 "Agent의 400이 라우터 전체를 500으로 만들었다"를 학생이 말하게 합니다.

```text
cases/lab03.json 의 "회의록 없는 회의 요청"이 status 500 입니다. 보고서: runs/lab03-<시각>.json
먼저 원인을 설명해 줘. 그다음 my-work/assistant.json 을 고쳐 줘:
- Parse tasks에서 업무마다 missing(빠진 입력)을 정한다 (Lab 01 과제와 같음).
- missing이 있는 업무는 Agent를 부르지 않고 route "입력 필요", answer "회의록 정리를 하려면 회의록 내용(notes)을 함께 보내 주세요."
- 결과 모양(index, type, text, agent, route, answer)은 그대로. cases/lab02.json 도 계속 통과.
```

## 예제 2 · 요청문 예

- 시나리오는 새로 만들지 않습니다. 회의록 Agent를 `off`로 끈 상태의 `requests/composite.json`.
- 시작: `call my-assistant requests/composite.json` → HTTP 500 (T-1002 답도 없음), `call meeting-agent requests/agent-meeting.json` → HTTP 404 (게시 해제). "404 하나에 라우터 전체가 멈춰 IT 답까지 사라졌다"를 학생이 말하게 합니다.

```text
회의록 Agent를 꺼 두고(off) cases/lab03-down.json 을 돌리면 복합 요청이 500 이고 IT 답도 사라집니다.
my-work/assistant.json 을 고쳐 줘:
- Call IT agent, Call meeting agent 에 neverError(true)와 timeout 60초.
- 결과 Set에서 route가 비어 있으면 "담당자 연결", answer가 비어 있으면 "담당 Agent가 응답하지 않아 담당자에게 전달했습니다."
- 다른 업무의 결과는 그대로 나와야 한다.
```

정답 (예제 1 + 2): [reference/lab03-example2-isolated.json](reference/lab03-example2-isolated.json) — Switch에 `needs input` 갈래와 `Need input` 결과, Merge 입력 4개.

| 수업 준비 때 결과 (1회) | |
| --- | --- |
| 회의록 Agent 꺼짐 `lab03-down` | 3/3 (복합 4.6초: IT 둘은 자동 답변, 회의록은 담당자 연결) |
| 다시 켠 뒤 `lab03` | 5/5 |
| `lab02` | 6/6 |

## 과제 · 어려운 케이스 예와 최종본

케이스: [answers/68-lab03-challenge-cases.json](answers/68-lab03-challenge-cases.json)

| 케이스 | 업무 규칙 | 예제 2 정답에서 |
| --- | --- | --- |
| user 없이 IT 질문 | 누가 물었는지 모르면 Agent를 부르지 않고 `입력 필요` | ✘ (`담당자 연결`: IT Agent가 400, 그걸 장애로 처리) |
| 남의 접수 건이 섞인 복합 요청 (이준호가 T-1002) | 라우터를 거쳐도 남의 접수 내용이 나오지 않음, 프린터는 답함 | ✔ (IT Agent가 `담당자 연결`, "정우성" 없음) |
| 회의록은 붙였지만 IT 질문만 | 회의록 Agent를 부르지 않음 | ✔ |
| 업무 4개 (VPN·프린터·회의록·회식) | `count: 4`, 순서대로 | ✔ (4.6초) |
| 소문자 접수 번호 `t1002` | "처리 중" | ✔ (IT Agent가 번호를 고침, 67일차 과제) |
| 공백만 보냄 | 400 | ✘ (200: 공백도 "비어 있지 않음"으로 봄) |
| 영어로 질문 | `it-agent`, 자동 답변 | ✔ |

예제 2 정답: 5/7 → 최종본: 7/7.

> 처음에 "남의 접수 건" 케이스의 기대를 `본인이 접수한`(답 문장)으로 썼다가 실패했습니다. 보고서를 보니 IT 문의 Agent는 남의 접수 건이면 `route: 담당자 연결`로 넘깁니다 (67일차 계약). 기대 결과를 Agent의 계약에 맞게 고쳤습니다. 수업에서 "테스트가 틀렸는지 워크플로우가 틀렸는지"는 **계약 표**로 판단한다는 예로 씁니다.

요청문 예:

```text
cases/my-cases.json 을 돌린 보고서입니다: runs/my-cases-<시각>.json. 실패: "user 없이 IT 질문", "공백만 보냄".
원인을 먼저 설명하고 my-work/assistant.json 을 고쳐 줘.
- Has message? 는 앞뒤 공백을 지운 뒤 비었는지 본다.
- it 업무도 missing(user)이 있으면 Agent를 부르지 않고 "입력 필요", 답은 "누가 요청했는지(user)를 함께 보내 주세요."
  (Need input 의 답은 무엇이 빠졌는지에 따라 다르게, agent 칸은 원래 담당 Agent)
- cases/lab02.json, cases/lab03.json 도 계속 통과.
```

최종본: [answers/68-lab03-challenge-final.json](answers/68-lab03-challenge-final.json)

| 수업 준비 때 결과 (1회) | |
| --- | --- |
| 어려운 케이스 | 7/7 |
| `lab02` · `lab03` | 6/6 · 5/5 |
| 회의록 Agent 꺼짐 `lab03-down` | 3/3 |

## 확장 계획 예 (DESIGN.md 6절, 수업 준비 측정값)

| 측정 | 값 |
| --- | --- |
| IT 하나 (`it-only`) | 2.3~2.6초 |
| 회의록 하나 (`meeting-only`) | 3.5초 |
| 복합 요청 (업무 3개) | 4.5~6.6초 |
| 업무 4개 | 4.6~4.8초 |
| 기타만 (나누기 LLM 한 번) | 0.9~1.0초 |

- 복합 요청(4.5~6.6초)은 단독 시간의 단순 합(2.6 + 3.5 + 2.6 ≈ 8.7초)보다 짧고, 가장 긴 것(3.5초)보다는 깁니다. 이유 두 가지:
  - 단독 시간에는 **나누기 LLM 약 1초**(기타만 0.9~1.0초)가 들어 있습니다. Agent만의 시간은 IT 약 1.3~1.6초, 회의록 약 2.5초. 단순 합은 나누기를 세 번 센 값입니다.
  - n8n HTTP Request 노드는 받은 항목들을 **동시에** 보냅니다 (n8n 2.42.6 `HttpRequestV3` 코드: 요청을 모아 `Promise.allSettled`, 배치 간격 기본 0). 그래서 IT 업무 둘은 `Call IT agent` 하나에서 함께 가고, IT 갈래와 회의록 갈래는 노드 순서대로 **차례로** 실행됩니다.
  - 어림: 나누기 1 + IT 둘 동시 약 1.5 + 회의록 약 2.5 ≈ 5초 → 측정 4.5~6.6초와 맞음. 업무 4개(4.6~4.8초)도 IT 둘 + 회의록 + 기타(Agent 없음)라 거의 같음.
- n8n이 부른 Agent도 각자 실행되므로, 부하가 몰리면 **Agent 실행 수 = 요청 수 × 업무 수**로 늘어난다.
- 21명이 동시에 복합 요청을 보내면 n8n 하나에서 라우터 21개 + Agent 실행 약 63개. 첫 조치는 측정 → 큐 모드(작업자 여러 개, 수평 확장)와 OpenAI 속도 제한 확인. 수직 확장은 LLM 대기 시간이 대부분이라 효과가 작다 (CPU가 아니라 API 응답을 기다림).
- Agent별로 분리해 두었기 때문에 회의록 Agent만 따로 늘리거나 꺼도 IT 답은 나온다 (예제 2에서 확인).
