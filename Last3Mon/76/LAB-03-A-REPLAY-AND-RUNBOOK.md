# Lab 03 · 다시 돌리기, 런북과 장애 연습, 끝없이 돌리지 않기

> **강사용 정답본** · 학생 저장소에 올리지 않습니다. 학생용 문제는 [LAB-03-Q-REPLAY-AND-RUNBOOK.md](LAB-03-Q-REPLAY-AND-RUNBOOK.md).
> 요청문은 예시이며 CLI 에이전트로 보내 재지는 않았습니다. 결과 숫자는 2026-10-29에 정답 워크플로우를 학생 순서대로 1회씩 실행한 값입니다. 명령 · 출력 전부: [answers/LAB-TEST-RESULT.md](answers/LAB-TEST-RESULT.md).

## 예제 1 · 요청문 예

```text
my-work/replay.json 을 새로 만들어 줘. 웹훅 POST my-replay .
Get DLQ(HTTP GET http://data-api:8800/dlq) → Pick items(Code): parked 가 아닌 것만, 비어도 다음으로 가게 alwaysOutputData true.
Has items? 가 없으면 바로 {replayed: 0, ok: 0, still_failed: 0, parked: 0}.
있으면 항목마다 Run intake again: POST http://localhost:5678/webhook/my-intake 본문 {requests: [ item ]} (DLQ 의 원래 요청).
my-intake 결과의 created 가 1 이면 성공 → POST /dlq/update {dlq_id, remove: true}. 실패면 지우지 않는다.
끝에 AGENTS.md 3절 {replayed, ok, still_failed, parked, duplicates}. 기대 결과 cases/lab03.json.
```

**빈칸 답** (Q 문서 ▶ 빈칸 채우기 `____①`~`____④`)

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `my-replay` | AGENTS.md 3절 재처리 |
| ② | `alwaysOutputData` | 빈 결과에서도 다음 노드로 (AGENTS.md 5절 그 밖) |
| ③ | `item` | DLQ 항목의 원래 요청 칸 |
| ④ | `created` | `my-intake`는 늘 200이라 결과 칸으로 판단 |

정답: [reference/lab03-example1-replay.json](reference/lab03-example1-replay.json)

| 10/29 결과 | |
| --- | --- |
| 고치기 전 (`answers/17`) | **1/5** · `my-replay` 404, DLQ 2 · 접수 건 0 |
| 고친 뒤 (`answers/18`) | **5/5** · `replayed: 2, ok: 2` (1.1초), DLQ 0, 접수 건 2, 한 번 더 `replayed: 0` |

## 예제 2 · 결과 (에이전트 없이, `answers/19`)

| 단계 | 본 것 |
| --- | --- |
| 장애 시작 | `my-intake` 200 · `failed: 2` (2.8초), `nightly-report` 500 |
| 알아챔 (`ops`) | DLQ 2 (R-301 · R-302) · 알림 2: `[high] intake · dlq · count 2`, `[critical] … unexpected · rows is not iterable` |
| 고침 · 재처리 | `fault tickets ok` → `call my-replay` 200 (1.4초) |
| 확인 | DLQ 0 · 접수 건 2. **critical 알림은 남음** (버그는 재처리로 안 고쳐짐) |
| `lab03-drill` | **7/7** · 접수 건 5 (평소 3 + 재처리 2) |

런북 2절 예 (짝 연습 뒤 비교용):

```markdown
1. `uv run tools/flow.py ops` — 고장 스위치 · DLQ · 알림을 본다. (또는 `curl -s -XPOST localhost:5678/webhook/my-ops-status -d '{}'`)
2. 알림을 나눈다: `high · dlq`는 데이터 API 쪽 → 3번. `critical · unexpected`는 코드 버그 → 알림의 workflow · node · message와
   execution_id로 n8n 화면 Executions에서 그 실행을 열고 코드 담당에게. `critical · dlq_down`은 알림의 lost ids를 먼저 적어 둔다.
3. 데이터 API가 되살아났는지: 데이터 API 담당에게 확인 (연습에서는 `uv run tools/flow.py fault tickets ok` 뒤 `ops`의 `fault switch: all ok`). `/health`는 고장 스위치와 관계없이 ok라 이것만으로는 모름.
4. 재처리: `curl -s -XPOST localhost:5678/webhook/my-replay -d '{}'` → `ok`가 DLQ 수와 같은지.
5. 확인: `ops`의 DLQ 0, 접수 건 수가 재처리한 만큼 늘었고 같은 key가 둘이 아닌지.
하지 말 것: DLQ를 비우지 말 것 (`/dlq-clear`, `ops --reset` — 재처리할 요청이 사라짐). parked를 자동으로 돌리지 말 것. nightly-report를 급히 고쳐 배포하지 말 것 (74일차 배포 절차).
```

- 짝 연습에서 흔히 빠지는 단계: ① 알림을 **원인별로 나누기** (critical이 재처리 뒤에도 남아 당황함) ② 재처리 **전에** 데이터 API가 살아났는지 확인 (아니면 재처리가 또 실패해 `attempts`만 오름) ③ 확인에서 **중복** 보기.

## 예제 3 · 결과 (에이전트 없이, `answers/20`)

| 케이스 | 10/29 |
| --- | --- |
| `slow` · `batch-two` | 11.6초 · `failed: 2`, DLQ 2 |
| 8초 뒤 접수 건 | **2** (이미 있음) |
| 재처리 | `replayed: 2, ok: 2, duplicates: 2` (1.1초) |
| 그 뒤 | 접수 건 2 그대로, DLQ 0 · **6/6** |

- 이 예제의 답: DLQ의 요청은 "반쯤 처리됐을" 수 있다. 재처리가 안전한 것은 멱등 키 덕분 (최소 한 번 + 멱등 = 결과는 한 번).

## 과제 1 · 요청문 예

```text
my-work/replay.json 의 Pick items 에서 body.max_attempts(없으면 3 ) 를 읽어,
attempts 가 그 수 이상 인 항목은 action "park", 나머지는 "replay" 로 나눠 줘.
Replay it?(If): replay 는 지금처럼 다시 보내고, park 는 POST /dlq/update {dlq_id, parked: true , reason} 뒤
POST /alerts {workflow: "replay", severity: "high", reason: "parked", dlq_id, message}.
두 갈래를 Merge 로 모아 요약의 parked 에 수를. parked 항목은 지우지 않는다.
기대 결과 cases/lab03-challenge.json, cases/lab03.json.
```

**빈칸 답**

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `3` | 조건 표 기본값 |
| ② | 이상 (`>=`) | 재처리 3에서 `attempts`가 3. 초과(`>`)면 4번째에야 멈춤 |
| ③ | `true` | DLQ 항목의 `parked` |
| ④ | `parked` | 조건 표 그대로 |

정답: [answers/76-lab03-challenge-park.json](answers/76-lab03-challenge-park.json)

| 10/29 결과 | |
| --- | --- |
| 고치기 전 (`answers/21`) | **3/7** · 재처리 3도 `replayed: 2, parked: 0`, 고친 뒤 자동으로 다시 보냄 |
| 고친 뒤 (`answers/22`) | **7/7** · 재처리 3 **0.1초** `parked: 2`, DLQ `size 2 · parked 2`, `[high] parked`, 고친 뒤 `replayed: 0` · `lab03` 5/5 |

## 과제 2 · 요청문 예

```text
my-work/ops-status.json 을 새로 만들어 줘. 웹훅 POST my-ops-status .
Get DLQ(GET /dlq) → Recent alerts(POST /alerts/list {within: 600}) → Get created(GET /tickets-created) → Decide status(Code).
parked 가 1 이상이거나 10분 안 critical 알림이 있으면 "critical", parked 가 아닌 DLQ 가 있거나 high 알림이 있으면 " warn ", 아니면 "ok".
결과 {status, dlq(parked 가 아닌 수), parked, created, alerts: {critical, high}, reasons: [한국어로 까닭]}.
읽기만 한다: 이 워크플로우에서 DLQ · 알림을 바꾸지 않는다 . 기대 결과 cases/lab03-challenge2.json.
```

**빈칸 답**

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `my-ops-status` | 조건 표 |
| ② | `600` | 10분 = 600초 |
| ③ | `warn` | 가운데 신호 |
| ④ | 바꾸지 않는다 | 확인이 상태를 바꾸면 안 됨 (`/alerts` POST 사고) |

정답: [answers/76-lab03-challenge2-ops-status.json](answers/76-lab03-challenge2-ops-status.json)

| 10/29 결과 | |
| --- | --- |
| 고치기 전 (`answers/23`) | **3/7** · 상태 케이스 넷 404 |
| 고친 뒤 (`answers/24`) | **7/7** · `ok` → `warn`(DLQ 2) → `critical`(critical 1) → `ok`, `lab03-challenge` 7/7 · `lab02-challenge2` 6/6 |
| `call my-ops-status` (비우기 전) | `critical` · DLQ 5 · critical 1 · high 1 · 까닭 셋 (`critical 알림 1건 (10분)`, `DLQ 5건: 원인을 고친 뒤 재처리`, `high 알림 1건 (10분)`) |

## 6교시에 볼 것

| 볼 것 | 막혔을 때 한마디 |
| --- | --- |
| 재처리가 접수 건을 직접 만듦 | "`my-intake`를 다시 불러 같은 규칙으로" |
| DLQ가 비면 응답이 안 옴 | "`alwaysOutputData` · 할 일 없음 갈래" |
| HTTP 상태로 성공 판단 | "`my-intake`는 늘 200 — `created`" |
| parked를 지움 | "사람이 볼 것. 지우지 않기" |
| 런북에 "확인한다"만 씀 | "무엇을 보면 되는지까지 (DLQ 0 · 같은 key 없음)" |
| 상태 웹훅이 알림을 만듦 | "읽기만" |
