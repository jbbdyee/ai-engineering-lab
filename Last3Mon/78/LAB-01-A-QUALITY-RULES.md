# Lab 01 · 품질 규칙 · 눈으로 검사하고, 규칙으로 바꾸기

> **강사용 정답본** · 학생 저장소에는 수업이 끝난 뒤 올립니다. 학생용 문제는 [LAB-01-Q-QUALITY-RULES.md](LAB-01-Q-QUALITY-RULES.md).
> 요청문은 예시이며 CLI 에이전트로 보내 재지는 않았습니다. 결과 숫자는 실습을 5개로 늘린 뒤 정답 워크플로우를 학생 순서대로 2026-11-01에 1회씩 실행한 값입니다 (강사 Mac). 판정은 규칙대로라 누가 돌려도 같습니다. 명령 · 출력 전부: [answers/LAB-TEST-RESULT.md](answers/LAB-TEST-RESULT.md).

## 예제 1 · 결과 (에이전트 없이, `answers/01`)

| 줄 | id | 내 눈 | 기준 검사 | 규칙 |
| --- | --- | --- | --- | --- |
| 3 · 5 · 8 | FAQ-103 · 105 · 108 | 나쁨 | ✔ 잡음 | `title_missing` · `answer_missing` · `keywords_missing` |
| 4 | FAQ-10 | 나쁨 | **놓침** | `id_format` |
| 6 | FAQ-106 | 나쁨 | **놓침** | `answer_too_long` |
| 7 | FAQ-102 (둘째) | 나쁨 | **놓침** | `duplicate_in_batch` |
| 9 | FAQ-109 | 나쁨 | **놓침** | `pii` (`010-1234-5678`) |
| 10 | FAQ-110 | 나쁨 | **놓침** | `external_link` (`bit.ly`) |
| 11 · 12 | FAQ-003 · 112 | 이미 있는 FAQ를 봐야 | 통과 | 과제 1 |
| 13 | FAQ-113 | 뜻이 다름 | 통과 | Lab 02 예제 2 (LLM) |

- 기준: 13줄 중 **10줄 통과**(빈 값 셋만). 눈: 분명히 나쁜 8줄 + 판단 보류 3줄 → 좋은 줄 2줄.
- 풀이 때: "기준이 틀렸나?" → 아니오, **규칙이 셋뿐**. 가장 위험한 놓침은 FAQ-109(개인 전화번호)와 FAQ-110(단축 링크) — 73일차 보안과 이어서.

## 예제 2 · 요청문 예

```text
my-work/faq-check.json 을 새로 만들어 줘. 웹훅 POST my-faq-check, 이름 "78 FAQ check (my)".
Is a list?(IF): 본문 items 가 목록이 아니면 Reject body 로 HTTP 400 {"error": "items must be a list"}.
Check rows(Code) 하나에서 줄마다 AGENTS.md 3절 FAQ 품질 규칙대로 errors 를 붙인다. 공백만 있는 값은 빈 값, 글자 수는 앞뒤 공백을 뺀 뒤 센다.
pii 는 하이픈 없는 휴대전화도, external_link 는 호스트가 정확히 intra.example.com 이 아니면.
결과 {batch, total, valid, invalid, rows: [{id, ok, errors, warnings}], codes}, rows 는 들어온 순서 그대로. LLM 은 쓰지 않는다. 기대 결과 cases/lab01.json.
```

**빈칸 답** (Q 문서 ▶ 빈칸 채우기 `____①`~`____④`)

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `my-faq-check` | AGENTS.md 3절 계약 · 테스트 파일의 `webhook` |
| ② | `400` | 목록이 아닌 본문은 줄을 셀 수 없음 — 기준 검사는 여기서 500으로 멈춤 |
| ③ | 앞뒤 공백을 뺀 뒤 | 공백 세 칸짜리 제목이 '있는 제목'으로 통과하지 않게 (예제 3의 경계) |
| ④ | 정확히 intra.example.com | `intra.example.com.evil.io`처럼 앞만 같은 바깥 주소를 막음 |

정답: [reference/lab01-example2-check.json](reference/lab01-example2-check.json)

| 11/01 결과 | |
| --- | --- |
| 고치기 전 (`answers/02`, 기준에 같은 테스트) | **1/5** · 빈 값만 ✔, 형식 · 중복 · 개인정보 · 링크 없음, B-2 `valid` 10, 목록이 아닌 본문 **500** |
| 고친 뒤 (`answers/03`) | **5/5** · B-1 13줄 중 5줄 통과 · 8줄 나쁨 (눈과 같은 8줄), 목록이 아닌 본문 400, 0.1초 |

## 예제 3 · 결과 (에이전트 없이, `answers/04`)

| 경계 | 내 검사 | 기준 | 기준이 틀린 까닭 |
| --- | --- | --- | --- |
| 40자 · 41자 | ✔ 통과 · `title_too_long` | ✘ 둘 다 통과 | 길이 규칙 없음 |
| 공백만 | ✔ `title_missing` | ✘ 통과 | `!r.title` — 공백은 "있음" |
| 10자 · 9자 | ✔ 통과 · `answer_too_short` | ✘ 둘 다 통과 | 길이 규칙 없음 |
| `01012345678` · `02-123-4567` | ✔ `pii` · 통과 | ✘ 둘 다 통과 | 전화 규칙 없음 |
| `intra.example.com/help` · `intra.example.com.evil.io` | ✔ 통과 · `external_link` | ✘ 둘 다 통과 | 링크 규칙 없음 |
| `faq-410` | ✔ `id_format` | ✘ 통과 | 형식 규칙 없음 |

- 내 검사 **6/6**, 기준 **0/6**. 강사의 첫 판(10/18 판 reference)은 `evil.io`를 통과시켰음 — `(?!intra\.example\.com)`만 보고 호스트가 끝나는지는 안 봄. 지금 판은 `(?!intra\.example\.com(?![\w.-]))`. 학생 판이 FAQ-409에서 ✘라면 좋은 토론거리.

## 과제 1 · 요청문 예

```text
my-work/faq-check.json 에 이미 있는 데이터와 맞춰 보기를 더해 줘.
Is a list? 와 Check rows 사이에 Get FAQ(HTTP GET http://data-api:8800/faq-all) 를 둔다.
이미 있는 id 면 errors 에 exists_id, 이미 있는 제목이면 same_title.
이미 있는 FAQ 가 쓰는 키워드는 errors 가 아니라 warnings 에 keyword_used:<낱말> (대소문자 무시) — 통과는 시킨다.
앞의 규칙은 그대로. 기대 결과 cases/lab01-challenge.json, cases/lab01.json 도.
```

**빈칸 답**

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `faq-all` | 처음 6개 + 오늘 더한 FAQ 전체 |
| ② | `same_title` | 제목이 같으면 검색에서 두 답이 겹침 |
| ③ | `warnings` | 키워드가 겹치는 것은 흔하고 나쁘지 않음 — 알려만 줌 |
| ④ | 그대로 | 같은 Code에 더함. `lab01` 5/5가 그대로여야 함 |

정답: [answers/78-lab01-challenge-existing.json](answers/78-lab01-challenge-existing.json)

| 11/01 결과 | |
| --- | --- |
| 고치기 전 (`answers/05`) | **0/4** · `exists_id` · `same_title` 없음, 통과 5 |
| 고친 뒤 (`answers/06`) | **4/4** · FAQ-003 `exists_id`, FAQ-112 `same_title` + 경고 `keyword_used:vpn`, 통과 3, 막 더한 FAQ-201도 `exists_id`. `lab01` 5/5 |

## 과제 2 · 요청문 예

```text
my-work/faq-check.json 의 결과에 보낸 사람에게 돌려줄 고침 목록을 더해 줘.
fix_list: 통과하지 못한 줄만 줄 순서대로 {row (1부터), id, codes (그 줄의 errors), fix}.
fix 는 코드마다 AGENTS.md 3절 "고침 목록" 표의 말을 그대로 쓴다 (LLM 으로 만들지 않는다).
message: "<batch>: <total>줄 중 <valid>줄 통과, <invalid>줄 고칠 것".
나쁜 줄을 고쳐 주지는 않는다 — 고치는 것은 사람. 앞의 칸은 그대로. 기대 결과 cases/lab01-challenge2.json, lab01 · lab01-challenge 도.
```

**빈칸 답**

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | 줄 순서대로 | 보낸 사람이 자기 파일의 몇째 줄인지 바로 찾게 (`row`는 1부터) |
| ② | 그대로 | 같은 코드에 늘 같은 말. LLM으로 만들면 매번 말이 달라짐 |
| ③ | 고칠 것 | 테스트가 `message`를 글자 그대로 봄 |
| ④ | 사람 | 워크플로우가 고쳐 넣으면 무엇이 틀렸는지 아무도 모름 (README 원칙) |

정답: [answers/78-lab01-challenge2-fix-list.json](answers/78-lab01-challenge2-fix-list.json)

| 11/01 결과 | |
| --- | --- |
| 고치기 전 (`answers/07`) | **1/5** · `fix_list` · `message` 없음 ("앞의 칸은 그대로"만 ✔) |
| 고친 뒤 (`answers/08`) | **5/5** · B-1 고칠 줄 10 (3째 FAQ-103 ~ 12째 FAQ-112), `B-1: 13줄 중 3줄 통과, 10줄 고칠 것`, B-2 FAQ-209 하나. `lab01` 5/5 · `lab01-challenge` 4/4 · `lab01-edges` 6/6 |

- 풀이 때: "고침 말을 LLM으로 만들면?" — 같은 코드에 날마다 다른 말, 돈, 그리고 지어낸 조언. 표 하나면 충분.
