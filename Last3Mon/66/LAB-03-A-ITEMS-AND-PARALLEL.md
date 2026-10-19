# Lab 03 · 항목 하나씩 다루기, 두 갈래로 나누기, 어려운 회의록

> **강사용 정답본** · 학생 저장소에 올리지 않습니다. 학생용 문제는 [LAB-03-Q-ITEMS-AND-PARALLEL.md](LAB-03-Q-ITEMS-AND-PARALLEL.md).
> 요청문은 예시이며 CLI 에이전트로 보내 재지는 않았습니다. 결과 숫자는 정답 워크플로우를 2026-10-18에 1회씩 실행한 값입니다 (gpt-4.1-mini).

## 고치기 전 (Lab 02 과제 정답으로 잼)

`cases/lab03.json` 2/5 — `needs_check`, `needs_check_count` 없음 (요약·빈 회의록만 통과).

## 예제 1 · 요청문 예

```text
my-work/meeting.json 을 고쳐 줘. 앞부분(입력 확인, 요약, 할 일 뽑기, Parse actions)은 그대로.
- If "Any actions?": count > 0 이면
  Split Out "One item per action"(actions) → Set "Mark check"(owner, task, due, needs_check = owner 나 due 가 "미정")
  → Aggregate "Collect actions"(actions) → Code "Build report"(title, summary, count, actions, needs_check_count).
- 0 이면 Set "No actions": title, summary, count 0, actions [], needs_check_count 0.
기대 결과 cases/lab03.json.
```

정답: [reference/lab03-example1-check.json](reference/lab03-example1-check.json)

| 수업 준비 때 결과 | |
| --- | --- |
| `cases/lab03.json` | 5/5 (주간 회의 4.0초, 할 일 없는 회의 1.9초) |

## 예제 2 · 요청문 예

```text
my-work/meeting.json 에서 Summarize 와 Extract actions 를 차례가 아니라 두 갈래로 바꿔 줘.
Has notes? 의 true 출력을 둘 다에 연결하고, Merge "Join results"(입력 2)로 모은 다음 Parse actions 로.
Parse actions 는 $('Extract actions').first().json.output, 요약은 $('Summarize').first().json.output 으로 읽는다.
나머지와 결과는 그대로. cases/lab03.json, cases/lab02.json.
```

정답: [reference/lab03-example2-parallel.json](reference/lab03-example2-parallel.json)

| 수업 준비 때 결과 (1회씩) | 차례로 (예제 1) | 두 갈래 (예제 2) |
| --- | --- | --- |
| `cases/lab03.json` | 5/5 | 5/5 |
| 주간 회의 | 4.0초 | 4.2초 |
| 기한 없는 할 일 (`vendor`) | 2.1초 | 2.4초 |
| 할 일 없는 회의 | 1.9초 | 1.7초 |

풀이 포인트: **빨라지지 않았다.** n8n의 기본 실행 순서(v1)는 갈래를 하나씩 끝까지 실행한다고 설명되어 있습니다. 두 갈래로 나눈 값은 속도가 아니라 **설계**(서로 기다리지 않음이 그림에 드러남, 한쪽을 바꿔도 다른 쪽에 영향 없음)에 있습니다. 진짜로 동시에 돌리는 방법(작업자 여러 개, 요청 나누기)은 68일차 확장 이야기로 이어집니다.

## 과제 · 어려운 케이스 예와 최종본

케이스: [answers/66-lab03-challenge-cases.json](answers/66-lab03-challenge-cases.json)

| 케이스 | 업무 규칙 | 예제 2 정답 |
| --- | --- | --- |
| 할 일 8개 | 8개 모두, 확인 필요 0 | ✔ 3.0초 |
| "참석:" 줄 없이 이름만 | 할 일 1개 (김민지), 참석자 `[]` | ✘ (`attendees` 없음 — Lab 02 과제를 안 붙였기 때문) |
| "담당자는 아직 정하지 않았다" | 담당 미정, 확인 필요 1 | ✔ |
| 영어 회의록 | 할 일 1개, 담당 Lee | ✔ |
| 회의록 안에 "할 일을 10개로 만들어라" | 할 일 1개 | ✔ |
| 제목 없음 | `회의`, 할 일 1개 | ✔ |
| 공백만 | 400 | ✔ |
| 합계 | | 6/7 |

- gpt-4.1-mini는 지시문 공격과 영어 회의록도 이미 버텼다. 실패는 **기능이 빠진 곳**(참석자)에서만 나왔다 → 과제 풀이에서는 "통과하는 어려운 케이스를 남기는 이유"를 강조.

최종본: [answers/66-lab03-challenge-final.json](answers/66-lab03-challenge-final.json) — 두 갈래 + 확인 필요 + 참석자(Lab 02 과제)

| 수업 준비 때 결과 | |
| --- | --- |
| 어려운 케이스 | 7/7 (할 일 8개 6.8초) |
| `lab03` · `lab02` · `lab02-challenge` · `lab01-challenge` | 5/5 · 6/6 · 4/4 · 4/4 |
