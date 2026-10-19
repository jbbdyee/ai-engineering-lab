# Lab 02 · LLM에게 JSON으로 받고, 코드로 읽기

> **강사용 정답본** · 학생 저장소에 올리지 않습니다. 학생용 문제는 [LAB-02-Q-JSON-AND-PARSE.md](LAB-02-Q-JSON-AND-PARSE.md).
> 요청문은 예시이며 CLI 에이전트로 보내 재지는 않았습니다. 결과 숫자는 정답 워크플로우를 2026-10-18에 1회씩 실행한 값입니다 (gpt-4.1-mini).

## 예제 1 + 2 · 요청문 예

```text
my-work/meeting.json 을 고쳐 줘. 요약(Summarize)과 입력 확인은 그대로.
- 요약 다음에 AI Agent "Extract actions"(gpt-4.1-mini, 자기 chat model 노드): 회의록의 할 일을 모두, 회의록 순서대로.
  JSON만, 코드 블록 없이: {"actions": [{"owner": "담당 또는 빈 글자", "task": "...", "due": "기한 그대로 또는 빈 글자"}]}.
  회의록에 없는 담당·기한은 지어내지 말고 비운다. 할 일이 없으면 {"actions": []}.
- Code "Parse actions": 앞뒤 ``` 를 지우고 JSON으로 읽는다. 실패하면 빈 목록. owner·due 가 비면 "미정", task 가 빈 항목은 뺀다.
- 결과 {title, summary, count, actions}. 기대 결과 cases/lab02.json.
```

정답: [reference/lab02-example2-actions.json](reference/lab02-example2-actions.json) (요약 → 할 일 뽑기를 **차례로**)

| 수업 준비 때 결과 | |
| --- | --- |
| `cases/lab02.json` | 6/6 (주간 회의 2.3~3.6초, 할 일 없는 회의 1.7초) |
| `cases/lab02-challenge.json` (예제 상태) | 1/4 (`attendees` 없음) |

## 과제 · 요청문 예와 실제로 있었던 일

```text
my-work/meeting.json 을 고쳐 줘.
- Extract actions 의 JSON 모양에 attendees 를 더한다: {"attendees": ["참석: 줄의 이름들, 없으면 []"], "actions": [...]}.
- Parse actions 에서 attendees 를 읽어 결과에 더한다 (없으면 []).
- 할 일은 그대로여야 한다: cases/lab02-challenge.json 과 cases/lab02.json 둘 다 통과.
```

정답: [answers/66-lab02-challenge-attendees.json](answers/66-lab02-challenge-attendees.json)

| 수업 준비 때 | 결과 |
| --- | --- |
| 지시문에 `attendees`만 더한 첫 판 | `lab02-challenge` 3/4 — 참석자는 모두 맞았지만 **할 일이 4개 → 3개**. "회의실 예약 규칙 개선은 담당자를 다음 회의에서 정한다"(담당자 미정)가 빠짐 |
| 지시문에 "담당자가 아직 정해지지 않은 할 일도 넣을 것" 추가 | 4/4, `lab02` 6/6 |

풀이 포인트 (실제로 일어난 일 그대로 보여 주기):

- 고친 곳(참석자)과 **상관없는 결과**(할 일 개수)가 바뀌었다. 지시문은 전체가 하나로 읽히기 때문.
- 그래서 과제 테스트에 "할 일은 그대로" 케이스를 넣었고, 원래 테스트(`lab02`)도 함께 돌린다. **고칠 때마다 전부 다시 재기**가 오늘의 습관.
- "미정"은 코드가 채운다 → LLM이 빈칸을 남겨도 결과는 매번 같다.
