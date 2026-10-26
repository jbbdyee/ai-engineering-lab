# Lab 02 · 규칙 먼저, 캐시, LLM 한 번

> **강사용 정답본** · 학생 저장소에 올리지 않습니다. 학생용 문제는 [LAB-02-Q-OPTIMIZE-FLOW.md](LAB-02-Q-OPTIMIZE-FLOW.md).
> 요청문은 예시이며 CLI 에이전트로 보내 재지는 않았습니다. 결과 숫자는 정답 워크플로우를 2026-10-18에 1회씩 실행한 값입니다 (강사 Mac, gpt-4.1-mini, bench는 n=5).
> 10/24에 실습을 5개로 늘리며 정답을 학생 순서대로 다시 돌렸습니다 (45단계). 명령 · `-v` 출력 전부와 codex 프롬프트: [answers/LAB-TEST-RESULT.md](answers/LAB-TEST-RESULT.md). 10/24 점수: 예제 1 `lab02` 7/9 (캐시 케이스 · 접수 답에서 검토 LLM이 "처리 중"을 바꿈), 나머지는 모두 기대대로.

## 예제 1 · 요청문 예

```text
my-work/helpdesk.json 의 순서를 바꿔 줘: Has question? → Start clock → Search FAQ → Get ticket → After data → Rule classify(Code) → Known?(If).
Rule classify: 질문에 T-1234 같은 번호(/T-?\d{4}/i)가 있으면 ticket, FAQ 결과가 1개 이상이면 faq, 아니면 unknown. {category, by:'rule'}.
Known? true → Answer, false → Classify → Parse category → After classify → Answer. Answer 는 $json.category 로 분류를 읽는다.
Build result: 분류는 Parse category 가 실행됐으면 그것, 아니면 Rule classify. steps 에 rule 또는 classify.
나머지(답, 검토, timings)는 그대로. 기대 결과 cases/lab02.json 앞 네 케이스.
```

**빈칸 답** (Q 문서 ▶ 빈칸 채우기 `____①`~`____④`)

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `/T-?\d{4}/i` | 하이픈 있어도 없어도, 대소문자 무시, 숫자 네 자리 (`T-1002` · `t1002`) |
| ② | 1개 이상 | `/faq`의 `results`가 비어 있지 않으면 FAQ로 답할 수 있음 |
| ③ | `Parse category` | LLM 분류 길에서 분류 결과를 만드는 마지막 노드 |
| ④ | `rule` | 규칙 길을 지났다는 `steps` 이름 (AGENTS.md 3절) |

정답: [reference/lab02-example1-rules.json](reference/lab02-example1-rules.json)

| 수업 준비 때 결과 | |
| --- | --- |
| `cases/lab02.json` | 7/9 (예제 2의 "같은 질문" 캐시 케이스와, 답 문장이 기대 표현과 달랐던 "없는 접수 번호" 실패. 10/23~24에는 "없는 접수 번호"가 통과해 8/9) |
| `cases/lab01.json` | 4/4 |
| 규칙 질문 시간 | 접수 1.9~2.3초 (예제 2 timings 상태에서 2.4~2.8초) |

- 처음 쓴 "없는 접수 번호" 기대(`찾지 못`)가 틀렸습니다: 검토 LLM이 "확인되지 않습니다"로 바꿔 말함. 기대를 "없다는 여러 표현 + 상태를 지어내지 않음(`not_contains` 처리 중 등)"으로 고쳤습니다 (71일차 "모른다의 여러 모양"과 같음).

## 예제 2 · 요청문 예

```text
my-work/helpdesk.json 에 캐시를 더해 줘 (AGENTS.md 2절 데이터 API, 3절 캐시 규칙).
Start clock 다음: Cache key(Code: question 을 trim·소문자·연속 공백 하나, use_cache = body.no_cache !== true)
→ Cache lookup(GET http://data-api:8800/cache/<encodeURIComponent(key)>, neverError) → Cached?(value 있고 use_cache)
  true → Cached result(route·category·answer·sources + llm_calls 0, cached true, steps ['cache'], timings.total_ms) → Send cached
  false → 지금 흐름(Search FAQ ...).
Build result 뒤: Cache it?(category faq 이고 use_cache) true → Store in cache(POST /cache/<key> {value:{route,category,answer,sources}, ttl 600}) → Send result.
접수(ticket)는 저장하지 않는다. 기대 결과 cases/lab02.json 전체, lab01 도 통과.
```

**빈칸 답** (Q 문서 ▶ 빈칸 채우기 `____①`~`____④`)

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | trim · 소문자 · 연속 공백 하나 | 띄어쓰기 · 대소문자만 다른 질문을 같은 키로 (AGENTS.md 3절) |
| ② | `body.no_cache !== true` | 본문 `no_cache`가 true가 아닐 때만 캐시 사용 |
| ③ | `neverError` | 캐시에 없을 때의 404에서 멈추지 않게 (AGENTS.md 5절) |
| ④ | 접수(ticket) | 상태가 바뀌는 답은 캐시하지 않음 (AGENTS.md 3절 굵은 줄) |

정답: [reference/lab02-example2-cache.json](reference/lab02-example2-cache.json)

| 수업 준비 때 결과 | |
| --- | --- |
| `cases/lab02.json` | 9/9 · 같은 질문(띄어쓰기·대소문자 다름) 0.1초, `llm_calls: 0` |
| `cases/lab01.json` · `lab03.json` | 4/4 · 2/4 (3단계 전) |
| 캐시 없이 (`faq-vpn-nocache`) bench | p50 2.01초 · p95 2.23초 |

- 처음에는 "규칙으로 모르는 질문"(회의실 화면 공유)이 LLM 분류로 `faq`가 되어 **캐시에 들어갔고**, 다음 테스트에서 0.1초로 나와 `llm_calls` 기대가 깨졌습니다. 그 케이스에 `no_cache: true`를 넣었습니다 → 수업 이야기 거리: "캐시는 테스트도 바꾼다".

## 예제 3 · 결과 (에이전트 없이, 10/24)

예제 2 정답(`reference/lab02-example2-cache.json`), 캐시를 비운 뒤.

| 재기 | 첫 호출 | p50 | max |
| --- | --- | --- | --- |
| 캐시 씀 (`faq-vpn` × 5) | 2.07초 (LLM 2번) | **0.05초** | 2.07초 |
| 캐시 안 씀 (`faq-vpn-nocache` × 5) | 1.99초 | 1.99초 | 2.24초 |

- `/cache-stats` 뒤: `entries 1 · hits 9 · misses 1`. `no_cache` 요청도 캐시를 **조회는** 하므로 hits로 셉니다 (쓰지는 않음). 학생이 "적중 9번?"이라고 하면 이 이야기를 합니다.
- 적중률 어림 (0.05초 · 2.0초): 10% → 1.81초, 30% → 1.42초, 60% → 0.83초.

## 과제 1 · 요청문 예

```text
my-work/helpdesk.json 에서 Review(검토 LLM)와 Review model 을 지우고, 그 자리에 Review check(Code)를 둬:
Answer 의 output 을 trim, 비었으면 empty, 한글이 없으면 not_korean, 400자 넘으면 자르고 too_long 을 review_problems 에.
Answer 지시문에 "합니다체, 3문장 이내"가 이미 있는지 확인. steps 에는 review 대신 check, llm_calls 는 검토를 세지 않는다.
나머지는 그대로. cases/lab02-challenge.json, lab02.json, lab01.json 모두 통과.
```

**빈칸 답** (Q 문서 ▶ 빈칸 채우기 `____①`~`____④`)

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `400` | 답 길이 상한 (교안 2단계 6절 검사 표) |
| ② | 합니다체, 3문장 이내 | 검토 LLM이 하던 말투 · 길이 다듬기를 지시문으로 |
| ③ | `check` | 검토 대신 코드 검사를 지났다는 단계 이름 (다른 짧은 이름도 됨) |
| ④ | 검토를 세지 않는다 | 지운 Review는 빼고 셈: 규칙 길 1, LLM 분류 길 2 |

정답: [answers/72-lab02-challenge-fast.json](answers/72-lab02-challenge-fast.json)

| 수업 준비 때 결과 | |
| --- | --- |
| `cases/lab02-challenge.json` | 5/5 (VPN 1.2초 · 비밀번호 1.1초 · 접수 1.3초) · 캐시 단계 상태 1/5 |
| `cases/lab02.json` · `lab01.json` | 9/9 · 4/4 |
| 캐시 없이 bench | p50 2.01 → **1.15초** · p95 2.23 → **1.16초** |

- 처음 쓴 `lab01` · `lab02` 기대에 `llm_calls: 3`, `steps`에 `review` 같은 **구조**가 들어 있어, 과제로 정당하게 빨라진 워크플로우가 실패했습니다. 품질 테스트는 **답의 내용**만 보게 고쳤습니다 (구조 기대는 그 단계의 테스트에만) → 이야기 거리: "최적화하면 깨지는 테스트는 무엇을 재고 있었나".

10/24 다시 돌린 결과: 고치기 전 `lab02-challenge` 1/5, bench p50 2.22 · p95 2.45초 → 고친 뒤 15/15 (`--repeat 3`, 0.9~1.6초), `lab02` 9/9, `lab01` 4/4, bench p50 **1.12** · p95 1.32초.

## 과제 2 · 요청문 예

```text
my-work/helpdesk.json 에 FAQ 번호 캐시를 더해 줘 (AGENTS.md 3절 캐시 키 표).
Rule classify 다음: FAQ cache key(Code: category 가 faq 이고 use_cache 이고 FAQ 결과가 있으면 faq_key = 'faq-' + 첫 FAQ id, 아니면 'none')
→ FAQ cache lookup(GET /cache/<faq_key>, neverError) → FAQ cached?(value 있고 faq_key 가 'none' 아님)
  true → FAQ cached result(llm_calls 0, cached true, cache_by 'faq', steps ['faq', 'rule', 'cache']) → Send
  false → Back to rule(Code: Rule classify 의 결과를 그대로) → Known?
Store in cache 뒤에 Store by FAQ(POST /cache/<faq_key>, 같은 value, ttl 600) → Result again.
질문 캐시의 Cached result 에는 cache_by 'question', Build result 에는 cache_by null.
기대 결과 cases/lab02-challenge2.json, lab02-challenge.json, lab02.json 도 통과.
```

**빈칸 답** (Q 문서 ▶ 빈칸 채우기 `____①`~`____④`)

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `faq-` | 캐시 키 표 둘째 줄: `faq-<FAQ id>` |
| ② | `faq` | FAQ 번호 키로 찾았을 때 (AGENTS.md 3절 Lab 02 과제 2) |
| ③ | `600` | 질문 캐시와 같은 ttl (초) |
| ④ | `question` | ②와 짝. 질문 키로 찾았을 때 |

정답: [answers/72-lab02-challenge2-faqcache.json](answers/72-lab02-challenge2-faqcache.json) (과제 1 정답에 노드 7개: FAQ cache key · FAQ cache lookup · FAQ cached? · FAQ cached result · Send FAQ cached · Back to rule · Store by FAQ)

| 10/24 결과 (`cases/lab02-challenge2.json`) | 고치기 전 (과제 1 정답) | 고친 뒤 |
| --- | --- | --- |
| 처음 묻는 VPN | ✔ 1.1초 | ✔ 2.5초 (push 직후) |
| 다른 말 VPN | ✘ `cached: false`, LLM 1번, 1.2초 | ✔ `cache_by: faq`, LLM 0번, **0.1초** |
| 같은 말 | ✘ `cache_by` 칸 없음 (캐시는 맞음, 0.1초) | ✔ `cache_by: question`, 0.0초 |
| `no_cache` | ✔ | ✔ 1.2초 |
| 프린터 처음 · 접수 현황 | ✔ | ✔ |
| 합 | 4/6 | 6/6, `lab02-challenge` 5/5, `lab02` 9/9 |

- `Back to rule`이 없으면 `Known?`이 캐시 응답을 읽어 분류가 사라집니다. 학생이 가장 많이 막힐 곳으로 예상합니다 (수업 준비 때 예상).
- 풀이 때 "잃는 것": FAQ-003에 묶인 질문은 모두 처음 질문에 맞춘 답을 받습니다.
