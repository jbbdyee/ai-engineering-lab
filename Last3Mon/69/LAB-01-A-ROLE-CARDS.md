# Lab 01 · 역할 카드, 작성자, 검토자

> **강사용 정답본** · 학생 저장소에 올리지 않습니다. 학생용 문제는 [LAB-01-Q-ROLE-CARDS.md](LAB-01-Q-ROLE-CARDS.md).
> 요청문은 예시이며 CLI 에이전트로 보내 재지는 않았습니다. 결과 숫자는 정답 워크플로우를 2026-10-18에 1회씩 실행한 값입니다 (gpt-4.1-mini).

## 예제 1 · 역할 카드 (정답 예)

| 칸 | 작성자 | 검토자 | 정리자 |
| --- | --- | --- | --- |
| 하는 일 | 사실로 공지 초안 쓰기 | 초안이 규칙을 지키는지 찾기 | 통과한 공지를 채널별로 다듬기 (메일 제목, 메신저 글) |
| 받는 것 | `request`, `facts` (고칠 때 `previous_draft`, `feedback`) | `facts`, `draft` | 통과한 `notice` |
| 내놓는 것 | `draft` | `passed`, `codes`, `issues` | `title`, `chat` |
| **하지 않는 일** | 스스로 검토·통과 판정 | 초안을 고쳐 쓰기 | 내용 바꾸기, 새 정보 |
| 테스트 | 날짜·시간이 그대로 있나 (`lab01`) | 일부러 틀린 초안 5종 (`lab01-challenge`) | 메신저 글에 날짜, 연락처 없음 (`lab02-challenge`) |
| LLM · 규칙 | LLM | 규칙 3 + LLM 1 | LLM (두 개 동시) |

사고 셋의 담당: 시간 빠짐 → 검토자 `missing_fact`, 개인 연락처 → 검토자 `personal_info`, 하지 않은 약속 → 작성자 지시문 + 검토자 `unsupported_claim` (두 번 막음).

## 예제 2 · 요청문 예

```text
my-work/writer.json 에 작성자 워크플로우를 만들어 줘. 계약은 AGENTS.md 3절 작성자.
- facts가 비면 400 {"error": "facts are required"}.
- AI Agent(gpt-4.1-mini, Tool 없음)가 한국어 공지 하나를 쓴다. 첫 줄은 [대괄호] 제목, 그다음 3~6줄.
  사실에 있는 것만. 날짜·시간은 사실에 쓴 그대로(10월 23일, 22:00~24:00). 사실에 없는 약속·보상·날짜·사람·연락처를 더하지 않는다.
- feedback이 오면 previous_draft를 검토 의견대로 모두 고치고 나머지는 그대로. 고칠 때 새 정보를 더하지 않는다
  (전화번호를 지울 때 다른 번호나 내선을 넣지 않는다).
- 다음 Code에서 앞뒤 ``` 를 지우고 {"draft": "..."} 로 돌려준다. 기대 결과 cases/lab01.json.
```

정답: [reference/lab01-example2-writer.json](reference/lab01-example2-writer.json)

| 수업 준비 때 결과 | |
| --- | --- |
| `cases/lab01.json` | 5/5 (1.3~5.2초) |
| `call my-writer requests/notice-phone.json` | 처음 요청("공지를 써 주세요")에서는 작성자가 연락처를 **스스로 뺐다** → 검토 단계를 시험할 수 없어 요청을 "문의처 연락처도 꼭 넣어 주세요"로 바꿈 → 전화번호·메일 주소를 넣음 |

풀이 포인트: 요청한 사람이 원하는 것(연락처 넣기)과 회사 규칙(개인 연락처 금지)이 부딪힙니다. 작성자는 요청을 따르고, **규칙은 검토자가 지킵니다.**

## 과제 · 요청문 예

```text
my-work/reviewer.json 에 검토자 워크플로우를 만들어 줘. 계약은 AGENTS.md 3절 검토자. facts나 draft가 비면 400.
1. Code "Rule checks": facts에서 날짜(10월 23일)·시간(22:00) 모양을 찾고, 초안에 없으면 missing_fact (빈칸은 무시하고 비교).
   전화번호(010-1234-5678)·메일 주소가 있으면 personal_info. 600자 넘으면 too_long.
2. AI Agent "Claim check agent": facts와 draft를 보고, 사실에 없는 약속·보상·날짜·연락처 문장을 JSON {"unsupported": [...]}로.
   사실을 바꿔 쓰거나 줄인 문장, 인사·양해 문구는 문제가 아니다.
3. Code "Build review": 둘을 합쳐 {passed, codes, issues}. 기대 결과 cases/lab01-challenge.json.
```

정답: [answers/69-lab01-challenge-reviewer.json](answers/69-lab01-challenge-reviewer.json) (학생용 [reference/lab02-start-reviewer.json](reference/lab02-start-reviewer.json)과 같은 것, Lab 02 시작용)

| 수업 준비 때 결과 | |
| --- | --- |
| 처음 | 5/6. "전화번호" 초안에 `personal_info`와 함께 `unsupported_claim`도 나옴. 그 초안의 연락처가 사실(메일 점검)에 **없었기** 때문 → LLM이 맞았고 테스트 자료가 틀림. 연락처가 사실에 있는 프린터 공지로 바꿈 |
| 바꾼 뒤 | 6/6 (0.9~1.1초, 초안 없음은 0.1초) |
| Lab 02에서 드러난 거짓 경보 뒤 | 지시문에 "바꿔 쓰거나 줄인 문장은 문제 아님", 그래도 남아 **Code가 LLM 판단을 다시 확인**(그 문장의 낱말이 모두 사실에 있으면 뺌) → 6/6 |

풀이 포인트: 테스트가 실패하면 **워크플로우·테스트 자료·기대 결과 중 무엇이 틀렸는지**부터 봅니다. 이번에는 테스트 자료였습니다.
