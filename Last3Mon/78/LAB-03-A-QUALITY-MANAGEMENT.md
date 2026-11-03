# Lab 03 · 품질 관리 · 스키마로 넓히고, 고쳐서 다시, 추세로 보기

> **강사용 정답본** · 학생 저장소에는 수업이 끝난 뒤 올립니다. 학생용 문제는 [LAB-03-Q-QUALITY-MANAGEMENT.md](LAB-03-Q-QUALITY-MANAGEMENT.md).
> 요청문은 예시이며 CLI 에이전트로 보내 재지는 않았습니다. 결과 숫자는 2026-11-01 정답 워크플로우 1회 실행 값입니다. 명령 · 출력 전부: [answers/LAB-TEST-RESULT.md](answers/LAB-TEST-RESULT.md).

## 예제 1 · 요청문 예

```text
my-work/check.json 을 새로 만들어 줘. 웹훅 POST my-check, 이름 "78 Schema check (my)".
Get schema: HTTP GET http://data-api:8800/schemas/<본문 schema> (neverError). 스키마가 없으면(fields 가 없음) HTTP 400 {error: "unknown schema", schema}.
Check rows(Code): 본문 csv 가 있으면 첫 줄을 열 이름으로 쉼표로 나눠 줄로 바꾸고, items 가 있으면 그대로.
필드 규칙은 코드에 쓰지 말고 스키마의 fields 를 읽어 AGENTS.md 3절 타입 표대로 (required · string · enum · email · phone · date · pattern · list), 키는 배치 안 중복.
결과 {schema, batch, total, valid, invalid, rows: [{row (1부터), key, ok, errors}], codes}. 기대 결과 cases/lab03.json.
```

**빈칸 답**

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `400` | 모르는 스키마는 검사할 수 없음 |
| ② | 열 이름 | `name,dept,email,phone,joined` |
| ③ | `fields` | 규칙을 데이터(스키마)로 두면 새 데이터셋에 워크플로우를 고치지 않음 (예제 3) |
| ④ | 1부터 | CSV의 열 이름 줄을 빼고 사람이 세는 번호 |

정답: [reference/lab03-example1-schema-check.json](reference/lab03-example1-schema-check.json)

| 11/01 결과 | |
| --- | --- |
| 고치기 전 (`answers/17`) | FAQ 검사에 직원 CSV → **400** (`items must be a list`), `lab03` **0/4** (404) |
| 고친 뒤 (`answers/18`) | **4/4** · 직원 9줄 중 4줄 (메일 · 팀 · 13월 · 이름 없음 · 중복), FAQ 스키마로 B-3 6줄 중 5줄, 모르는 스키마 400 |

**스키마로 하는 것 · 못 하는 것 (`QUALITY.md` 8절 예)**

| 규칙 | 스키마로 | 따로 |
| --- | --- | --- |
| 필수 · 길이 · 형식 · 목록 · 중복 | ✔ | |
| 개인정보 (답 안의 전화 · 메일) | | Code (Lab 01) |
| 이미 있는 데이터와 겹침 | | Code + 데이터 API (Lab 01 과제 1) |
| 답이 질문에 맞나 | | LLM (Lab 02 예제 2) |

## 예제 2 · 요청문 예

```text
my-work/faq-import.json 에서 고쳐서 다시 넣은 줄을 격리함에서 빼 줘.
Summarize 뒤에 Release fixed: POST http://data-api:8800/quarantine/remove {ids: imported_ids}.
넣은 줄만 뺀다 — 이번에도 걸린 줄은 격리함에 남는다. 품질 기록 · 알림은 그대로.
응답은 Summarize 의 결과를 다시 (Release fixed 의 응답이 아님). 기대 결과 cases/lab03-fix.json.
```

**빈칸 답**

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `imported_ids` | 이번에 넣은 id |
| ② | 남는다 | 고쳤는데 또 틀린 줄은 다시 사람에게 |
| ③ | 그대로 | Lab 02 과제 1의 기록 · 알림 |
| ④ | 다시 | HTTP 노드의 출력은 API 응답 — 결과는 Summarize에서 다시 꺼냄 |

정답: [reference/lab03-example2-import.json](reference/lab03-example2-import.json)

| 11/01 결과 | |
| --- | --- |
| 고치기 전 (`answers/19`) | **3/4** · 넣기는 됨(`score` 1 · FAQ 16), 격리함 **2** 그대로 |
| 고친 뒤 (`answers/20`) | **4/4** · 격리함 0, 기록 0.8 → 1 |

## 예제 3 · 결과 (에이전트 없이, `answers/21`)

| | FAQ 검사 | 스키마 검사 (고치지 않음) |
| --- | --- | --- |
| 접수 건 9줄 | 0줄 통과 (`id_format` · `keywords_missing` · `answer_missing` 9, 빈 id 중복 8) | **2줄 통과**, 줄마다 다른 이유 7가지 |
| 테스트 | — | **5/5** (직원 CSV 4/9 그대로) |

- 풀이 때: "스키마 파일 한 장으로 새 데이터셋" — 그래서 스키마 변경은 **규칙 변경**이라 리뷰가 필요 (74일차 관문).

## 과제 1 · 요청문 예

```text
my-work/quality-report.json 을 새로 만들어 줘. 웹훅 POST my-quality-report, 이름 "78 Quality report (my)".
Get log: HTTP GET http://data-api:8800/quality-log. 본문에 dataset 이 있으면 그 데이터셋만.
Make report(Code) 하나에서 AGENTS.md 3절 "품질 보고서" 정의대로 count · batches · avg_score (소수 4자리, 0건이면 0) · worst_batch (같으면 먼저 나온 것) · rejected_batches.
top_codes: 모든 기록의 codes 를 더해 많은 순, 같으면 코드 글자순. trend: 마지막 score − 첫 score 가 0.05 넘으면 좋아짐, −0.05 미만이면 나빠짐, 아니면 그대로.
LLM 은 쓰지 않는다. 기대 결과 cases/lab03-challenge.json.
```

**빈칸 답**

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `4` | 0.65833…을 0.6583으로 |
| ② | 먼저 나온 것 | 같은 점수면 순서로 하나를 정함 — 늘 같은 답 |
| ③ | 글자순 | 같은 수면 코드 이름으로 — 늘 같은 순서 |
| ④ | 그대로 | 1건뿐이거나 차이가 작으면 |

정답: [answers/78-lab03-challenge-report.json](answers/78-lab03-challenge-report.json)

| 11/01 결과 | |
| --- | --- |
| 고치기 전 (`answers/22`) | **0/4** · 404 (기록 4줄은 생김, B-1 `!` allow_fail) |
| 고친 뒤 (`answers/23`) | **4/4** · 4 · 0.6583 · B-1 · 거절 1, `pii` 2, `좋아짐` |

- 풀이 때: 거절을 빼면 0.8778. `trend`가 "13줄 거절 → 고친 2줄"을 비교한 것이라는 함정.

## 과제 2 · 요청문 예

```text
두 워크플로우를 고쳐 줘.
① my-work/check.json: 검사가 끝나면 POST http://data-api:8800/quality-log 한 줄 {batch, dataset: schema, total, valid, quarantined: invalid, rejected: false, score: valid / total (4자리), codes}. 응답은 검사 결과 그대로.
② my-work/quality-report.json: by_dataset — 모든 기록을 dataset 마다 {count, avg_score, worst_batch, top_code} (처음 나온 순서), worst_dataset — avg_score 가 가장 낮은 데이터셋.
본문의 dataset 거르기와 앞의 칸은 그대로. 기대 결과 cases/lab03-challenge2.json, lab03 · lab03-challenge 도.
```

**빈칸 답**

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `schema` | 직원 · 티켓 · FAQ가 데이터셋 이름 |
| ② | 처음 나온 | 보고서가 늘 같은 순서 |
| ③ | 낮은 | 가장 손볼 데이터셋 |
| ④ | 그대로 | `lab03-challenge` 4/4가 그대로여야 함 |

정답: [answers/78-lab03-challenge2-check-log.json](answers/78-lab03-challenge2-check-log.json) · [answers/78-lab03-challenge2-report.json](answers/78-lab03-challenge2-report.json)

| 11/01 결과 | |
| --- | --- |
| 고치기 전 (`answers/24`) | **0/4** · 기록 1줄 (FAQ만), `by_dataset` 없음 |
| 고친 뒤 (`answers/25`) | **4/4** · employee 0.4444 · ticket **0.2222** · faq 0.8333, `worst_dataset` ticket, 전체 0.5. `lab03` · `lab03-challenge` 4/4 |

- 풀이 때: 섞은 `trend`(좋아짐)는 직원 → FAQ를 비교한 것 — 추세는 데이터셋 안에서.
