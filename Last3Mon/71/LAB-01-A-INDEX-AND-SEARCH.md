# Lab 01 · 정답표, 색인, 검색

> **강사용 정답본** · 학생 저장소에 올리지 않습니다. 학생용 문제는 [LAB-01-Q-INDEX-AND-SEARCH.md](LAB-01-Q-INDEX-AND-SEARCH.md).
> 요청문은 예시이며 CLI 에이전트로 보내 재지는 않았습니다. 결과 숫자는 정답 워크플로우를 2026-10-18에 1회씩 실행한 값입니다 (text-embedding-3-large).
> 수업 전날(2026-10-22) 같은 정답으로 다시 돌린 명령 · `-v` 출력 전부와 codex 프롬프트: [answers/LAB-TEST-RESULT.md](answers/LAB-TEST-RESULT.md) (점수는 10/18과 같음).

## 예제 1 · 정답표

| 질문 | 문서 | 섹션 | 답 문구 |
| --- | --- | --- | --- |
| 비밀번호는 몇 자 이상이어야 하나요? | `password-policy` | 1. 비밀번호 만들기 | 12자 이상 |
| 암호를 얼마나 자주 바꿔야 해? | `password-policy` | 2. 변경 주기 | 90일마다 |
| 회사를 그만두면 노트북은 언제까지 돌려줘야 하나요? | `device-issue-return` | 3. 반납 | 5영업일 |
| 첨부 파일이 너무 커서 메일이 안 보내져요 | `email-and-documents` | 2. 첨부 파일 | 25MB, 사내 드라이브 |
| 생성형 AI에 고객 자료를 넣어도 되나요? | `software-usage` | 3. 생성형 AI 서비스 | 입력하지 않는다 |
| 연차 휴가는 며칠이에요? | **없음** | — | — |

- "암호"는 문서에 없는 낱말(문서는 "비밀번호")입니다. 임베딩 검색은 뜻이 가까우면 찾지만, Lab 03의 어려운 질문에서는 이런 차이가 실패를 만듭니다.

## 예제 2 · 요청문 예

```text
두 워크플로우를 만들어 줘. 계약은 AGENTS.md 3절, 노드는 5절.
1. my-work/index.json (웹훅 my-index): GET http://data-api:8800/docs → 문서마다 GET /docs/<name>
   → Code에서 본문을 "## " 섹션마다 청크로 (청크 글 앞에 문서 제목), source(name)·title·chunk 번호를 같이.
   본문 chunking 이 숫자면 그 글자 수로 자른다 (기본 section).
   → 메모리 Vector Store(insert, memoryKey my_policy_docs, clearStore true) + OpenAI Embeddings text-embedding-3-large + Default Data Loader(metadata source, title, chunk).
   → {indexed_chunks, chunking}.
2. my-work/search.json (웹훅 my-search): question 없으면 400. 같은 저장소에서 load, topK = 본문 top_k 없으면 3, 메타데이터 포함, Always Output Data.
   → Code: {question, hits:[{rank, source, title, score(소수 셋째 자리), text}], top_score, indexed}.
기대 결과 cases/lab01.json.
```

정답: [reference/lab01-example2-index.json](reference/lab01-example2-index.json), [reference/lab01-example2-search.json](reference/lab01-example2-search.json)

| 수업 준비 때 결과 | |
| --- | --- |
| 색인 (섹션) | 25개 청크 (문서의 `## ` 섹션 수와 같음), 1.2초 |
| `cases/lab01.json` | 6/6 (검색 0.2~0.4초) |
| `cases/lab01-challenge.json` (예제 상태) | 2/4 — `top_k`는 예제에 이미 있어 통과, `section` 없음 |

## 과제 · 요청문 예

```text
my-work/index.json 의 Make chunks 에서 청크마다 section(그 청크의 "## " 제목 글자)을 정하고, Loader 메타데이터에 section 을 더해 줘.
my-work/search.json 의 hits 에 section 을 더해 줘 (없으면 빈 글자). top_k 는 본문에서 받는다 (기본 3).
cases/lab01-challenge.json, cases/lab01.json 둘 다 통과.
```

정답: [answers/71-lab01-challenge-index.json](answers/71-lab01-challenge-index.json), [answers/71-lab01-challenge-search.json](answers/71-lab01-challenge-search.json)

| 수업 준비 때 결과 | |
| --- | --- |
| `cases/lab01-challenge.json` | 4/4 |
| `cases/lab01.json` | 6/6 |
