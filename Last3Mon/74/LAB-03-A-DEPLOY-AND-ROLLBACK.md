# Lab 03 · 배포 · 되돌리기, 카나리, 릴리스 점검 워크플로우

> **강사용 정답본** · 학생 저장소에 올리지 않습니다. 학생용 문제는 [LAB-03-Q-DEPLOY-AND-ROLLBACK.md](LAB-03-Q-DEPLOY-AND-ROLLBACK.md).
> 요청문은 예시이며 CLI 에이전트로 보내 재지는 않았습니다. 결과 숫자는 정답 워크플로우를 학생 순서대로 2026-10-27에 1회씩 실행한 값입니다 (강사 Mac, `gpt-4.1-mini` · `gpt-5.4-nano`). 명령 · 출력 전부: [answers/LAB-TEST-RESULT.md](answers/LAB-TEST-RESULT.md).

## 예제 1 · 결과 (에이전트 없이)

| 재기 (`answers/22`) | 결과 |
| --- | --- |
| `release helpdesk 1.1.0` → `call` | `version.release` 1.1.0 · `stable`, 답 끝 `[FAQ-003]` |
| `release helpdesk 1.0.0` → `call` | 1.0.0, 출처 번호 없음 |
| `cases/lab03.json` | **2/2** |

- push · n8n 재시작 없음. `RELEASE.md` 3절 예: "1.1.0 배포 → 1.0.0 되돌림, 명령 한 줄, 다음 요청부터, `call -v`의 `version.release`로 확인".

## 예제 2 · 요청문 예

```text
my-work/helpdesk.json 의 Pick release 에 카나리를 더해 줘.
bucket = user 이름 글자의 codePointAt 합 % 100 . 본문 release 가 없고 canary 가 있고 bucket < canary.percent 이면
canary.release 를 쓰고 channel ' canary '. 순서는 고정 > 카나리 > active ( 고정(본문 release) 가 맨 먼저).
기대 결과 cases/lab03-canary.json, cases/lab02.json.
```

**빈칸 답** (Q 문서 ▶ 빈칸 채우기 `____①`~`____④`)

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `100` | AGENTS.md 3절 카나리 대상 규칙 (`% 100`) |
| ② | `<` | 작으면 카나리 (같으면 들어가지 않음) |
| ③ | `canary` | `channel` 세 값 중 하나 |
| ④ | 고정 (본문 `release`) | 테스트 · 점검이 카나리에 섞이지 않게 |

정답: [reference/lab03-example2-canary.json](reference/lab03-example2-canary.json) (Lab 01 · 02 과제 포함)

| 10/27 결과 | 고치기 전 (Lab 02 과제 2 정답, `answers/23`) | 고친 뒤 (`answers/24`) |
| --- | --- | --- |
| `cases/lab03-canary.json` | 3/6 (카나리 대상 둘 · "같은 사람" 이 `stable`) | **6/6** |
| `lab02` · `lab02-challenge2` | | 5/5 · 5/5 |

## 예제 3 · 결과 (에이전트 없이)

| 재기 | 결과 |
| --- | --- |
| `lab03-watch` (1.2.0 50% 카나리, `answers/25`) | **4/6** — 최유진 · 정우성 ✘ ("대기열" 없는 한 문장 답), 운영 넷 ✔ |
| `--no-canary` 뒤 `--no-before` (`answers/26`) | **6/6** |

- `RELEASE.md` 3절 예: "1.2.0 카나리 50% → 영향 2/6명, `--no-canary` 한 줄, 끈 뒤 6/6. 전원 배포였다면 6/6명이 영향."
- 풀이 때 "1.2.0 릴리스는 왜 지우지 않나?" → 기록 · 재현 (불변 버전), 원인 분석.

## 과제 1 · 요청문 예

```text
my-work/release-check.json 을 새로 만들어 줘. 웹훅 my-release-check , 본문 release 가 없으면 400.
Golden questions(Code): cases/my-golden.json 의 질문 6개(question · user · expect 낱말)를 항목 6개로, 각 항목에 release.
Ask helpdesk(HTTP POST http://localhost:5678/webhook/my-helpdesk): 항목마다 {question, user, release } 로 (neverError, timeout 30000).
Judge(Code): 답에 expect 낱말 중 하나가 있고 답의 version.release 가 점검한 release 와 같으면 이면 통과.
결과 {release, passed, total, failed, seconds, verdict}: 모두 통과면 ' promote ', 아니면 'rollback'.
기대 결과 cases/lab03-challenge.json.
```

**빈칸 답** (Q 문서 ▶ 빈칸 채우기 `____①`~`____④`)

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `my-release-check` | `cases/lab03-challenge.json`의 `webhook` |
| ② | `release` | 운영이 아니라 후보를 점검하려면 고정 |
| ③ | 같으면 | 고정이 먹었는지 확인 |
| ④ | `promote` | "내보내도 됨" |

정답: [answers/74-lab03-challenge-release-check.json](answers/74-lab03-challenge-release-check.json)

| 10/27 결과 (`answers/27`) | |
| --- | --- |
| 1.1.0 | `promote` 6/6 (3.1초) |
| 1.2.0 | `rollback` 0/6 (1.6초) |
| `release` 없음 | 400 |
| `cases/lab03-challenge.json` | **3/3** |
| `call my-release-check '{"release": "2.0.0"}'` | `promote` 6/6 (1.8초) |

## 과제 2 · 요청문 예

```text
my-work/release-check.json 의 Judge 와 Send verdict 사이에 Record gate(HTTP POST http://data-api:8800/ gates/helpdesk ) 를 넣어 줘.
본문: {release, verdict, passed, total, failed, seconds, source: 'my-release-check'} (Judge 의 결과에서).
Record gate 는 timeout 3000, neverError, onError continueRegularOutput (기록이 실패해도 판단은 보냄).
Send verdict 는 Judge 의 결과에 recorded: (기록 응답의 stored 가 true 인지) 를 더해 보낸다.
워크플로우에서 /releases 에는 POST 하지 않는다 . 기대 결과 cases/lab03-challenge2.json, cases/lab03-challenge.json.
```

**빈칸 답** (Q 문서 ▶ 빈칸 채우기 `____①`~`____④`)

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `gates/helpdesk` | AGENTS.md 2절 점검 기록 경로 |
| ② | `continueRegularOutput` | 실패해도 원래 출력으로 계속 (73일차 `Log event`와 같음) |
| ③ | `stored` | `POST /gates/helpdesk`의 응답 `{"stored": true, "count"}` |
| ④ | POST 하지 않는다 | 판단하는 쪽은 실행하지 않음 (AGENTS.md 9절, 최소 권한) |

정답: [answers/74-lab03-challenge2-gated.json](answers/74-lab03-challenge2-gated.json) (과제 1 정답 + 노드 `Record gate`, `Send verdict`에 `recorded`)

| 10/27 결과 (`cases/lab03-challenge2.json`) | 고치기 전 (과제 1 정답, `answers/28`) | 고친 뒤 (`answers/29`) |
| --- | --- | --- |
| 1.2.0 점검 · 기록 | ✘ `recorded` 없음 (24.2초, 이때 OpenAI가 느림) | ✔ `rollback` · `recorded` true (10.6초) |
| 1.1.0 점검 · 기록 | ✘ `recorded` 없음 | ✔ `promote` · `recorded` true |
| 1.2.0 배포 거부 (409 기대) | ✔ (기록이 **아예 없어서** 409) | ✔ (마지막 기록 rollback이라 409) |
| 1.1.0 배포 | **멈춤** — `before`가 409 `not gated` · `last_gate: null` | ✔ 200 → 1.1.0 · `stable` |
| 2.0.0 카나리 거부 (409 기대) | (돌지 않음) | ✔ 409, 최유진도 1.1.0 · `stable` |
| 합계 | 멈춤 (보고서 없음) | **5/5** |

`answers/30` (정책 켜고 손으로):

| 명령 | 결과 |
| --- | --- |
| `release helpdesk --require-gate on` → `release helpdesk 2.1.0` | `✘ refused: 2.1.0 has no passing gate record (never gated)` |
| `gate cases/golden.json --set release=2.0.0 --max-p95 3` | 6/6 PASS → `gate record → /gates/helpdesk: 2.0.0 promote` |
| `release helpdesk 2.0.0` | 됨 (`active 2.0.0 · deploy needs a passing gate`) |
| `release helpdesk --reset` · `doctor` | 1.0.0 · 정책 꺼짐 · `ready` |

- 풀이 때: 약한 golden으로 2.0.0을 게이트해도 기록이 남아 배포가 됩니다. **정책은 "기록이 있느냐"만 보고, 기록의 질은 게이트(테스트)의 질입니다.** 운영에서는 어느 테스트 파일로 · 누가 돌린 기록만 인정할지도 정합니다 (`source` · `cases` 칸).
