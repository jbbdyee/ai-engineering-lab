# Lab 01 · 결과 먼저, 첫 요청문

> **강사용 정답본** · 학생 저장소에 올리지 않습니다. 학생용 문제는 [LAB-01-Q-RESULT-FIRST.md](LAB-01-Q-RESULT-FIRST.md).
> 요청문은 예시이며 CLI 에이전트로 보내 재지는 않았습니다. 결과 숫자는 정답 워크플로우를 2026-10-18에 1회씩 실행한 값입니다 (gpt-4.1-mini).

## 예제 1 · 정답

```json
{"title": "10월 16일 주간 회의", "summary": "…한 문장…", "count": 4,
 "actions": [
   {"owner": "이준호", "task": "신규 고객 문의 응답 템플릿 정리", "due": "금요일까지", "needs_check": false},
   {"owner": "박서연", "task": "VPN 장애 보고서 작성", "due": "다음 주 월요일까지", "needs_check": false},
   {"owner": "김민지", "task": "서버 점검 일정 공지", "due": "오늘 중", "needs_check": false},
   {"owner": "미정", "task": "회의실 예약 규칙 개선", "due": "미정", "needs_check": true}],
 "needs_check_count": 1}
```

| 단계 | 들어오는 항목 | 나가는 항목 |
| --- | --- | --- |
| 웹훅 | — | 1 |
| 할 일 뽑기 (LLM) | 1 | 1 (목록 하나) |
| 할 일 하나씩 | 1 | **4** |
| 다시 모으기 | 4 | **1** |

- 4번은 담당자도 기한도 **미정** (지어내지 않음). "다음 회의는 10월 23일"은 할 일이 아님.
- 수업 준비 때 LLM(Lab 03 정답)은 4번 기한을 **"다음 회의 10월 23일"**로 적었다 ("다음 회의에서 정한다" + "다음 회의는 10월 23일"을 이어 붙임). 담당자가 미정이라 `needs_check`로는 걸렸다 → 풀이 때 "이건 지어낸 걸까, 읽어 낸 걸까?" 토론.

## 예제 2 · 요청문 예

```text
my-work/meeting.json 에 n8n 워크플로우를 만들어 줘.
- POST 웹훅, 경로 my-meeting. 본문 title, notes.
- AI Agent(OpenAI gpt-4.1-mini, Tool 없음)가 회의록을 한국어 한 문장으로 요약한다. 회의록에 있는 것만. 할 일은 아직 뽑지 않는다.
- 결과는 {"title": 본문 title, "summary": "..."}.
- 기대 결과는 cases/lab01.json. check까지 하고 push·test 명령을 알려 줘.
```

정답: [reference/lab01-example2-summary.json](reference/lab01-example2-summary.json) (Webhook → Summarize(Agent) → Build result(Set) → Send result)

| 수업 준비 때 결과 | |
| --- | --- |
| `cases/lab01.json` | 3/3 (1.1~2.8초) |
| `cases/lab01-challenge.json` (예제 상태) | 1/4 |
| 예제 상태에서 빈 회의록 | **200** `{"title": "빈 회의록", "summary": "회의 내용이 없으므로 논의 사항이나 결정된 내용이 없습니다."}` — LLM을 불러 쓸모없는 답 |

## 과제 · 요청문 예

```text
my-work/meeting.json 을 고쳐 줘.
1. 웹훅 다음에 If "Has notes?": notes 의 앞뒤 공백을 지운 뒤 비었으면 400 {"error": "notes are required"} (LLM을 부르지 않는다).
2. title 이 없거나 비면 "회의".
3. 요약은 그대로. cases/lab01-challenge.json 과 cases/lab01.json 둘 다 통과.
```

정답: [answers/66-lab01-challenge-summary.json](answers/66-lab01-challenge-summary.json)

| 수업 준비 때 결과 | |
| --- | --- |
| `cases/lab01-challenge.json` | 4/4 (빈 회의록 0.1초) |
| `cases/lab01.json` | 3/3 |

풀이 포인트: 막는 곳은 **LLM 앞**. 공백만 보낸 경우는 "비었다"의 뜻을 요청문에 적어야 막힌다.
