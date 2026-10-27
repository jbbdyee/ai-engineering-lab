# Lab 02 · 규정으로만 답하기, 모르면 넘기기, 답 검사

> **강사용 정답본** · 학생 저장소에 올리지 않습니다. 학생용 문제는 [LAB-02-Q-ANSWER-FROM-POLICIES.md](LAB-02-Q-ANSWER-FROM-POLICIES.md).
> 요청문은 예시이며 CLI 에이전트로 보내 재지는 않았습니다. 결과 숫자는 정답 워크플로우를 2026-10-18에 1회씩 실행한 값입니다 (gpt-4.1-mini, text-embedding-3-large).
> 수업 전날(2026-10-22) 같은 정답으로 다시 돌린 명령 · `-v` 출력 전부와 codex 프롬프트: [answers/LAB-TEST-RESULT.md](answers/LAB-TEST-RESULT.md) (점수는 10/18과 같음).

## 예제 1 + 2 · 요청문 예

```text
my-work/policy-qa.json 을 만들어 줘. 계약은 AGENTS.md 3절 규정 Q&A. question 없으면 400.
1. 같은 메모리 저장소(my_policy_docs)에서 load, topK 3, 메타데이터 포함, Always Output Data.
2. Code "Build context": 청크를 [1] [2] [3] 번호 붙인 발췌로, hits(source, title, score), top_score.
   min_score = 본문 min_score 없으면 0.33, relevant = top_score >= min_score.
3. relevant 가 아니면 LLM을 부르지 않고 route "담당자 연결", answer "규정에서 답을 찾지 못했습니다. IT 문의 창구로 연결해 드릴게요.", cited [].
4. relevant 면 AI Agent(gpt-4.1-mini, Tool 없음): 발췌로만, 한국어 3문장 이내, 사실마다 [번호], 없으면 정확히 "규정에서 답을 찾지 못했습니다."
5. Code "Build answer": [번호] → [문서 제목], cited = 인용한 번호의 source, route "자동 답변".
기대 결과 cases/lab02.json.
```

정답: [reference/lab02-example2-qa.json](reference/lab02-example2-qa.json)

| 수업 준비 때 결과 | |
| --- | --- |
| `cases/lab02.json` | 6/6 (답 1.7~2.2초, 점심 메뉴 0.3초: LLM을 부르지 않음) |
| `cases/lab02-challenge.json` (예제 상태) | 2/8 — 점수는 높은데 규정에 없는 4개가 모두 `자동 답변`, 검사 기록 없음 |

예제 상태에서 실제로 나온 답 (`call`, 1회):

| 질문 | top_score | route | 답 |
| --- | --- | --- | --- |
| VPN 접속 속도가 느리면 어떻게 해요? | 0.463 | 자동 답변 | "…대처 방법에 대한 내용은 찾지 못했습니다." |
| 노트북 사양은 어떻게 되나요? | 0.379 | 자동 답변 | "규정에는 노트북 사양에 대한 내용이 **포함되어 있지 않습니다**." + 출처 3개 |
| 비밀번호를 잊어버리면 어디서 바꿔요? | 0.551 | 자동 답변 | "규정에서 답을 찾지 못했습니다." |
| 보안 교육은 1년에 몇 번 받아야 하나요? | 0.353 | 자동 답변 | "규정에서 답을 찾지 못했습니다." |
| 모니터를 하나 더 받을 수 있나요? | 0.311 | 담당자 연결 | (기준 아래) |

→ 기준값(0.33)만으로는 "비슷한 낱말은 있는데 답은 없는" 질문을 거르지 못한다. 기준을 올리면 0.46대인 진짜 규정 질문(퇴사 노트북 0.464)도 걸린다.

## 과제 · 요청문 예

```text
my-work/policy-qa.json 의 Build answer 에 검사를 더해 줘. 검사마다 {name, passed} 를 checks 에, 실패 이름을 failed 에.
- found_in_policies: "찾지 못했", "포함되어 있지 않", "명시되어 있지 않", "언급이 없", "나와 있지 않" 이 없어야
- cites_excerpt: 인용 번호가 하나 이상
- grounded: 답 글(번호 뺀)의 두 글자 묶음 중 30% 이상이 발췌에 있어야
- numbers_from_policies: 답에 나온 숫자가 모두 발췌에 있어야
failed 가 있으면 route "담당자 연결", answer "규정에서 확실한 답을 찾지 못해 IT 담당자에게 전달했습니다.", draft 에 원래 답.
cases/lab02-challenge.json, cases/lab02.json 둘 다 통과.
```

정답: [answers/71-lab02-challenge-qa.json](answers/71-lab02-challenge-qa.json)

| 수업 준비 때 결과 | |
| --- | --- |
| `cases/lab02-challenge.json` | 8/8 |
| `cases/lab02.json` | 6/6 |

풀이 포인트:

- 지시문에 정확한 문장("규정에서 답을 찾지 못했습니다.")을 주어도 LLM은 "포함되어 있지 않습니다"처럼 **다르게** 말했다 → 문장 하나만 찾는 검사는 새고, 모양 여러 개를 찾아야 했다.
- 틀린 전제("30일마다 바꾸면 되죠?")는 발췌로만 답하게 하자 예제 상태에서도 90일로 바로잡았다. 검사는 그 답을 막지 않는다 (숫자 90이 발췌에 있음).
- 검색 점수(앞)와 답 검사(뒤)는 **다른 실패**를 잡는다: 점수는 "엉뚱한 질문", 답 검사는 "비슷하지만 답이 없는 질문".

### 마무리 · 신뢰도 기준 충족 (`RAG-EVAL.md` 3-1절 답)

수업 준비 때 보고서(`answers/08-lab02-challenge.json` `--repeat 3`, `answers/09-lab02-after-challenge.json`, 2026-10-22)에서 센 값입니다. `lab02-challenge`는 세 번 모두 같은 갈래로 갔습니다 (24건 = 8 × 3: 자동 답변 9 · 관련도 기준 3 · 답 검사 12).

| 테스트 파일 | 질문 수 | 기준 충족 (자동 답변) | 미달 · 관련도 기준 | 미달 · 답 검사 | 충족률 |
| --- | --- | --- | --- | --- | --- |
| `cases/lab02.json` (빈 질문 400 빼고) | 5 | 4 | 1 (점심 메뉴 0.202) | 0 | 4/5 |
| `cases/lab02-challenge.json` (한 번) | 8 | 3 | 1 (연차 0.259) | 4 (VPN 속도 · 노트북 사양 · 비밀번호 찾기 · 보안 교육 횟수) | 3/8 |
| 합계 | 13 | 7 | 2 | 4 | 7/13 |

- 풀이 포인트: `lab02-challenge`의 충족률 3/8은 **낮아서 좋은 결과**입니다. 이 파일은 일부러 "점수는 높은데 답이 없는" 질문을 모은 것이라, 넘어간 4건이 모두 맞게 넘어간 것입니다. 충족률은 질문 묶음의 성격과 함께 읽습니다.
- 답 검사에서 넘어간 4건이 곧 "규정을 보완할 곳"입니다 (강의 6절 표의 담당자 연결 (검사)).
