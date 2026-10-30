# Lab 02 · 실패를 모으고(DLQ), 알리기 (Error Workflow)

> **강사용 정답본** · 학생 저장소에 올리지 않습니다. 학생용 문제는 [LAB-02-Q-COLLECT-AND-ALERT.md](LAB-02-Q-COLLECT-AND-ALERT.md).
> 요청문은 예시이며 CLI 에이전트로 보내 재지는 않았습니다. 결과 숫자는 2026-10-29에 정답 워크플로우를 학생 순서대로 1회씩 실행한 값입니다. 명령 · 출력 전부: [answers/LAB-TEST-RESULT.md](answers/LAB-TEST-RESULT.md).

## 예제 1 · 요청문 예

```text
my-work/intake.json 의 Summarize 뒤에 Any failed?(If) 를 넣어 failed 가 1 이상일 때만 Send to DLQ(HTTP POST http://data-api:8800/ dlq ) 로.
본문은 {items: [...]}, 실패한 항목마다 { item: 원래 요청 {id, user, text}, reason, workflow: "intake" }. rejected 는 넣지 않는다 .
DLQ 저장이 실패해도 응답은 나가게 options.response 에 neverError: true , 두 갈래 모두 Public result 로 가서 같은 결과를 응답.
기대 결과 cases/lab02.json 앞 두 케이스.
```

**빈칸 답** (Q 문서 ▶ 빈칸 채우기 `____①`~`____④`)

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `dlq` | `POST /dlq` (AGENTS.md 2절) |
| ② | 원래 요청 | 재처리 때 그대로 `my-intake`로 보냄. 결과의 `request` |
| ③ | 넣지 않는다 | 다시 해도 같은 실패 |
| ④ | `neverError: true` | HTTP 500을 노드 오류로 만들지 않음 (예제 3에서 이것이 구멍이 됨) |

정답: [reference/lab02-example1-dlq.json](reference/lab02-example1-dlq.json) (Lab 01 과제 1 · 2 포함)

| 10/29 결과 | |
| --- | --- |
| 고치기 전 (`answers/09`) | **2/4** · `failed: 2`인데 DLQ 0 · 알림 0 |
| 고친 뒤 (`answers/10`) | **3/4** · DLQ D-1 · D-2 (R-301 · R-302, `attempts 1`, 이유 `500 - tickets service is failing`) · 남은 ✘는 예제 2 |

## 예제 2 · 요청문 예

```text
my-work/error-handler.json 을 새로 만들어 줘. 파일 맨 위에 "id": "errHandler76001", 첫 노드는 errorTrigger .
Make alert(Code) 가 workflow.name · workflow.id · execution.lastNodeExecuted · execution.error.message · execution.id 를
{workflow, workflow_id, node, message, execution_id, severity: "critical", reason: "unexpected"} 로 만들어 POST http://data-api:8800/alerts.
my-work/intake.json 의 settings 에 errorWorkflow: "errHandler76001" 을 넣어 줘.
기대 결과 cases/lab02.json 전체.
```

**빈칸 답**

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `errHandler76001` | `nightly-report`의 `settings.errorWorkflow`가 이미 이 id |
| ② | `errorTrigger` | `n8n-nodes-base.errorTrigger` (AGENTS.md 5절) |
| ③ | `critical` | 처리하지 못한 오류 (강의 2단계 등급 표) |
| ④ | `errorWorkflow` | `settings` 안 이름 (AGENTS.md 4절) |

정답: [reference/lab02-example2-error-handler.json](reference/lab02-example2-error-handler.json) · [reference/lab02-example2-intake.json](reference/lab02-example2-intake.json)

| 10/29 결과 | |
| --- | --- |
| 고친 뒤 (`answers/11`) | **4/4** · 알림 `[critical] 76 Nightly report (provided, has a bug) · unexpected · Count by category · rows is not iterable [line 4]`, `lab01` 6/6 |

- 수업 준비 때 확인: 처리기를 **게시 해제**하면 n8n이 부르지 않습니다 (알림 0). 학생이 "push했는데 알림이 없다"면 처리기의 게시 여부부터.
- 풀이 때: 오류 문장 `rows is not iterable [line 4]`만 보고 버그(`$json.items` → `tickets`)를 찾게 해 봅니다. 고치지는 않습니다.

## 예제 3 · 결과 (에이전트 없이, `answers/12`)

| 실패 | 그물 | 10/29 |
| --- | --- | --- |
| 빈 글 | 결과 `rejected` | ✔ `rejected: 1, created: 2` |
| API 오류 | `failed` → DLQ | ✔ DLQ 2 |
| 버그 | Error Workflow → critical | ✔ 3초 뒤 `unexpected` |
| **API 오류 + DLQ 오류** | **없음** | ✘ 200 · `failed: 3`, DLQ 2 그대로 (R-101~103 사라짐), 결과에 `dlq_saved` 없음, 알림 없음 |

- **5/7**이 맞는 답입니다. 6 · 7번 ✘는 과제 1에서 고칩니다. 풀이 때: "예제 1에서 둔 `neverError`가 무엇을 숨겼나?" → DLQ 저장 실패. "처리하는 장치가 실패할 때"를 생각하게 합니다.

## 과제 1 · 요청문 예

```text
my-work/intake.json 의 Send to DLQ 뒤에 Make alert(Code) 와 Send alert(HTTP POST http://data-api:8800/alerts) 를 넣어 줘.
DLQ 응답에 stored 가 있으면 {workflow: "intake", severity: "high", reason: "dlq", count: failed 수, message},
없으면(DLQ 저장 실패) severity "critical", reason " dlq_down ", message 에 잃을 뻔한 요청 id 들.
알림은 요청 하나에 하나 (항목마다가 아님). 실패가 없으면 알림을 보내지 않는다.
결과에 dlq_saved(실패가 있을 때 true/false) 와 alert("sent" / "none") 를 더해 줘.
기대 결과 cases/lab02-challenge.json, cases/lab02-nets.json, cases/lab02.json.
```

**빈칸 답**

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `stored` | DLQ 응답 `{"stored", "size"}`. 고장이면 `{"error"}`뿐 |
| ② | `high` | 처리한 실패 (critical 아래) |
| ③ | `dlq_down` | 조건 표 그대로 |
| ④ | `alert` | 조건 표의 결과 칸 |

정답: [answers/76-lab02-challenge-alert.json](answers/76-lab02-challenge-alert.json)

| 10/29 결과 | |
| --- | --- |
| 고치기 전 (`answers/13`) | **0/6** |
| 고친 뒤 (`answers/14`) | **6/6** · high `count 2` 하나 · 실패 없으면 `alert: none` · DLQ 고장 시 `dlq_saved: false` + critical `DLQ save failed: dlq service is failing (fault switch) · lost ids R-201, R-203` · `lab02-nets` **7/7** · `lab02` 4/4 |

## 과제 2 · 요청문 예

```text
my-work/intake.json 의 Make alert 뒤에 Recent alerts(HTTP POST http://data-api:8800/alerts/list) 를 넣어
본문 {workflow: "intake", reason: 이번 알림의 reason, within: 600 } 로 10분 안의 같은 알림 수를 받아 줘.
Decide alert(Code): severity 가 high 이고 그 수가 1 이상이면 suppressed true. critical 은 늘 보낸다 .
Send it?(If) 로 suppressed 가 아닐 때만 Send alert, 결과의 alert 는 "sent" / "suppressed" / "none".
기대 결과 cases/lab02-challenge2.json, cases/lab02-challenge.json.
```

**빈칸 답**

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `600` | 10분 = 600초 (`within`은 초) |
| ② | `high` | 줄이라고 한 등급 |
| ③ | 늘 보낸다 | "정말 급한 건 늘" |
| ④ | `suppressed` | 조건 표 그대로 |

정답: [answers/76-lab02-challenge2-throttle.json](answers/76-lab02-challenge2-throttle.json)

| 10/29 결과 | |
| --- | --- |
| 고치기 전 (`answers/15`) | **4/6** · 두 번째에도 `sent`, dlq 알림 2 |
| 고친 뒤 (`answers/16`) | **6/6** · 두 번째 `suppressed`, dlq 알림 1, **DLQ 5건 모두**, critical은 `sent` · `lab02-challenge` 6/6 · `lab01-challenge2` 4/4 |

## 4교시에 볼 것

| 볼 것 | 막혔을 때 한마디 |
| --- | --- |
| 처리기 파일에 `id`가 없음 | "`check`의 경고 — 다른 워크플로우가 id로 부름" |
| 처리기를 push하지 않음 | "게시를 내린 처리기는 불리지 않음" |
| 알림 확인을 `POST /alerts`로 함 | "그건 알림을 만든다. 읽기는 `/alerts/list`" |
| `dlq_saved`가 늘 true | "`neverError`라 상태 코드는 늘 성공. 본문의 `stored`" |
| 알림을 항목마다 보냄 | "요청 하나에 하나, `count`" |
| suppressed인데 DLQ에도 안 넣음 | "줄이는 것은 알림이지 기록이 아님" |
