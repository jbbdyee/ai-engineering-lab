# Lab 02 · 규칙 검사를 모듈로, 두 곳에서 쓰기

> **강사용 정답본** · 학생 저장소에 올리지 않습니다. 학생용 문제는 [LAB-02-Q-MODULES.md](LAB-02-Q-MODULES.md).
> 요청문은 예시이며 CLI 에이전트로 보내 재지는 않았습니다. 결과 숫자는 정답 워크플로우를 2026-10-18에 1회씩 실행한 값입니다 (gpt-4.1-mini).
> 수업 전날(2026-10-21) 같은 정답으로 다시 돌린 명령 · `-v` 출력 전부와 codex 프롬프트: [answers/LAB-TEST-RESULT.md](answers/LAB-TEST-RESULT.md) (점수는 10/18과 같음).

## 예제 1 · 요청문 예

```text
두 파일을 만들어 줘. 계약은 AGENTS.md 3절, 노드는 5절.
1. my-work/rule-check.json: 모듈. "id": "modRuleCheck01" 를 파일에 쓴다.
   Execute Workflow Trigger(inputSource workflowInputs): facts(string), draft(string), max_length(number), required_phrases(array).
   Code "Rule checks": missing_fact(사실의 날짜·시간), personal_info(전화·메일), too_long(max_length), missing_phrase(required_phrases 중 없는 것).
   결과 {passed, codes, issues}. Respond 노드 없음.
2. my-work/rule-check-test.json: 웹훅 my-rule-check → Execute Workflow(id modRuleCheck01, 본문 값을 그대로 넘김,
   max_length 없으면 600, required_phrases 없으면 []) → Respond.
기대 결과 cases/lab02-module.json.
```

정답: [reference/lab02-example1-rule-check.json](reference/lab02-example1-rule-check.json) + [reference/lab02-example1-rule-check-test.json](reference/lab02-example1-rule-check-test.json)

| 수업 준비 때 결과 | |
| --- | --- |
| 모듈 게시 | 웹훅 없는(Execute Workflow Trigger만 있는) 워크플로우도 `push`로 게시되고 다른 워크플로우에서 불러짐 (n8n 2.42.6) |
| `cases/lab02-module.json` | 5/5 · 처음 호출 1.6초, 그다음 0.1초씩 (LLM 없음) |

## 예제 2 · 요청문 예

```text
my-work/notice-kit.json 의 Code "Rule checks" 를 지우고 그 자리에 Execute Workflow "Rule check module"(id modRuleCheck01)을 둔다.
입력: facts=웹훅 본문 facts, draft=Build draft 의 draft, max_length·required_phrases=Kind settings 표.
결과를 읽는 Build result 는 그대로. cases/lab01.json 을 고치지 않고 통과해야 한다.
```

정답: [reference/lab02-example2-kit-module.json](reference/lab02-example2-kit-module.json)

| 수업 준비 때 결과 | |
| --- | --- |
| 바꾸기 전 · 뒤 `cases/lab01.json` | 5/5 → 5/5 (테스트 수정 없음, 1.4~2.7초) |

## 과제 · 요청문 예

```text
my-work/sms.json 을 새로 만들어 줘. 계약은 AGENTS.md 3절 SMS. facts 없으면 400.
- AI Agent: 사실로 한국어 문자 하나, 80자 이내 한두 문장, 날짜·시간 그대로, 전화·메일·링크 없음.
- 같은 규칙 검사 모듈(id modRuleCheck01)을 부른다: max_length 80, required_phrases [].
  모듈 안은 고치지 않는다.
- 결과 {sms, published (passed), codes}. 기대 결과 cases/lab02-challenge.json.
```

정답: [answers/70-lab02-challenge-sms.json](answers/70-lab02-challenge-sms.json)

| 수업 준비 때 결과 | |
| --- | --- |
| `cases/lab02-challenge.json` | 4/4 (0.9~2.9초) |
| 키트 `cases/lab01.json` | 5/5 |

풀이 포인트:

- 모듈 안에 "SMS면 80" 같은 **쓰는 곳 이야기**가 들어가면, 쓰는 곳이 늘 때마다 모듈을 고치게 된다 → 다른 값은 **입력**으로.
- 웹훅으로 부르기(68·69일차)와 Execute Workflow의 차이: HTTP·웹훅 등록이 필요 없고 계약이 Trigger 입력으로 드러남. 대신 밖에서 바로 부를 수 없어 시험용 웹훅이 필요.
