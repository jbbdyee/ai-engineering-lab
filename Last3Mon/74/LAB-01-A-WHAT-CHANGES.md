# Lab 01 · 무엇이 바뀌었나, 답마다 버전, 지시문은 저장소로

> **강사용 정답본** · 학생 저장소에 올리지 않습니다. 학생용 문제는 [LAB-01-Q-WHAT-CHANGES.md](LAB-01-Q-WHAT-CHANGES.md).
> 요청문은 예시이며 CLI 에이전트로 보내 재지는 않았습니다. 결과 숫자는 실습을 5개로 늘린 뒤 정답 워크플로우를 학생 순서대로 2026-10-27에 1회씩 실행한 값입니다 (강사 Mac, `gpt-4.1-mini` · `gpt-5.4-nano`, bench는 n=5). 명령 · 출력 전부: [answers/LAB-TEST-RESULT.md](answers/LAB-TEST-RESULT.md).

## 예제 1 · 결과 (에이전트 없이)

| 바뀐 곳 (`diff`, 7개) | 전 | 후 | 셋 중 |
| --- | --- | --- | --- |
| `Answer` 지시문 | 307자 | 419자 (+ "FAQ에서 온 답이면 끝에 `[FAQ-003]`", "Keep answers short.") | 지시문 |
| `Answer model` | `gpt-4.1-mini` | `gpt-5.4-nano` | 모델 |
| 노드 `Review check` + 연결 셋 | 없음 | 답을 400자에서 자름 | 흐름 |
| 웹훅 경로 | `rel-v1` | `rel-v2` | 흐름 (답에는 영향 없음) |

| `call` (`answers/02`) | 시간 | 답 |
| --- | --- | --- |
| `rel-v1` | 2.8초 | "… 인증서 만료 여부를 확인한 뒤 다시 접속하시기 바랍니다. 현재 접수된 관련 문의는 없습니다 …" |
| `rel-v2` | 1.0초 | "… 인증서 만료 여부를 확인한 뒤 다시 접속해 보시기 바랍니다. **[FAQ-003]**" |

- 풀이 때: "출처 번호는 어디 때문?" → 지시문일 가능성이 높지만 **이 비교만으로는 확정 못 함** (모델도 바뀜). "빨라진 것은?" → 모델일 것 같지만 마찬가지.
- **수업 준비 중 실제로 본 것**: 10/18 판 v2는 `gpt-4.1-nano`였고 10/27에 OpenAI가 지원 종료해 HTTP 500이 났습니다. 워크플로우를 하나도 안 바꿨는데 멈춘 실제 예라 1단계 2절에 넣었습니다.

## 예제 2 · 요청문 예

```text
my-work/helpdesk.json (v1 을 복사한 것) 의 웹훅 경로를 my-helpdesk 로, 이름을 "74 IT helpdesk (my)" 로 바꿔 줘.
Has question? 뒤에 Release info(Set) 를 넣어 release 1.0.0, prompt_version p1, model gpt-4.1-mini.
Answer model 의 모델 값은 ={{ $('Release info').first().json.model }} 로 Release info 의 model 을 읽게.
Build result 결과에 version : {release, prompt_version, model} 을 Release info 에서 더해 줘. 지시문은 그대로 .
기대 결과 cases/lab01.json.
```

**빈칸 답** (Q 문서 ▶ 빈칸 채우기 `____①`~`____④`)

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `my-helpdesk` | `cases/lab01.json`의 `webhook` (AGENTS.md 3절) |
| ② | `={{ $('Release info').first().json.model }}` | 앞 노드 값을 읽는 n8n 표현식, 모델 이름을 한 곳에서 |
| ③ | `version` | AGENTS.md 3절 결과 모양의 버전 세 칸을 감싸는 이름 |
| ④ | 그대로 | 지시문까지 바꾸면 무엇 때문에 답이 바뀌었는지 또 모름 |

정답: [reference/lab01-example2-version.json](reference/lab01-example2-version.json)

| 10/27 결과 | |
| --- | --- |
| `cases/lab01.json` (`answers/03`) | **3/3** |

## 예제 3 · 결과 (에이전트 없이)

| 재기 | v1 (`rel-v1`) | v2 (`rel-v2`) |
| --- | --- | --- |
| `lab01-compare --repeat 3` (`answers/04` · `05`) | **9/15** — 출처 번호 두 케이스가 세 번 모두 ✘ | **15/15** |
| `bench -n 5` VPN (`answers/06`) | p50 1.23초 · p95 1.34초 | p50 0.98초 · p95 1.20초 |

- 출처 번호는 세 번 모두 같은 쪽 → **흔들림이 아니라 바뀐 것**. 해결 낱말 · 접수 현황은 둘 다 세 번 모두 ✔ (흔들림 없음).
- 시간 차이는 0.25초 정도. 모델 · 지시문 · 노드가 함께 바뀌어 원인을 말할 수 없습니다 → Lab 02의 한 가지씩 바꾼 릴리스로 이어 갑니다.

## 과제 1 · 요청문 예

```text
my-work/helpdesk.json 의 Release info 뒤에 Get prompt(HTTP GET) 를 넣어 줘.
주소는 http://data-api:8800/prompts/helpdesk/ prompt_version (Release info 의 값을 표현식으로).
Answer 의 systemMessage 는 지금 글자 대신 Get prompt 의 text 를 표현식으로 읽게.
Build result 의 version 에 prompt_source : ' registry ' 를 더해 줘. 다른 것은 그대로.
기대 결과 cases/lab01-challenge.json, cases/lab01.json.
```

**빈칸 답** (Q 문서 ▶ 빈칸 채우기 `____①`~`____④`)

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `prompt_version` | 릴리스 정보 세 값 중 지시문 버전 이름 (`{{ $('Release info').first().json.prompt_version }}`) |
| ② | `Get prompt` | 지시문 글자를 가져오는 노드 |
| ③ | `prompt_source` | 지시문을 어디서 가져왔는지 (AGENTS.md 3절) |
| ④ | `registry` | `cases/lab01-challenge.json`의 기대 |

정답: [answers/74-lab01-challenge-registry.json](answers/74-lab01-challenge-registry.json)

| 10/27 결과 | 고치기 전 (예제 2 정답) | 고친 뒤 |
| --- | --- | --- |
| `cases/lab01-challenge.json` (`answers/07` · `08`) | 2/3 (`prompt_source` 없음) | **3/3** |
| `cases/lab01.json` (`answers/09`) | | 3/3 |

## 과제 2 · 요청문 예

```text
my-work/helpdesk.json 의 Get prompt 에 options.timeout 2000 과 onError continueErrorOutput 를 넣어 줘.
성공 쪽은 Registry prompt(Set, text = $json.text), 실패 쪽은 Fallback prompt(Set, text = data-api/data/prompts/helpdesk- p1 .md 와 같은 글).
두 Set 모두 Search FAQ 로 이어 줘. Answer 의 systemMessage 는 Registry prompt 가 실행됐으면 그 text, 아니면 Fallback prompt 의 text.
version.prompt_source 는 Registry prompt 가 실행됐으면 'registry', 아니면 ' fallback '.
기대 결과 cases/lab01-challenge2.json, cases/lab01-challenge.json.
```

**빈칸 답** (Q 문서 ▶ 빈칸 채우기 `____①`~`____④`)

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `2000` | 2초를 ms로 |
| ② | `continueErrorOutput` | 실패해도 멈추지 않고 두 번째(오류) 출력으로 (72일차 Lab 03, 73일차 Lab 02 과제 2와 같음) |
| ③ | `p1` | 마지막으로 검증된 지시문 (운영 중인 1.0.0의 지시문) |
| ④ | `fallback` | `cases/lab01-challenge2.json`의 고장 케이스 기대 |

정답: [answers/74-lab01-challenge2-fallback.json](answers/74-lab01-challenge2-fallback.json) (과제 1 정답 + `Get prompt`의 `timeout` · `onError`, 노드 2개: `Registry prompt` · `Fallback prompt`)

| 10/27 결과 (`cases/lab01-challenge2.json`) | 고치기 전 (과제 1 정답, `answers/10`) | 고친 뒤 (`answers/11`) |
| --- | --- | --- |
| 평소 · 저장소에서 | ✔ | ✔ `registry` |
| 저장소 고장 (`prompts error`) | ✘ **HTTP 500** `Error in workflow` (0.1초) | ✔ 200 · `fallback` · "인증서" (1.3초) |
| 저장소 느림 (`prompts slow` 8초) | ✘ **9.1초** (8초를 다 기다림, `registry`) | ✔ `fallback` · 3.0초 |
| 되돌린 뒤 | ✔ | ✔ `registry` |
| 합계 | 2/4 | **4/4** |
| `lab01-challenge` (`answers/12`) | | 3/3 |

- 풀이 때 "73일차 판별 LLM은 막았는데 왜 여기는 계속 가나?"를 묻습니다: 판별 LLM은 보안 관문(멈추면 공격이 지나감), 지시문 저장소는 편의 의존(멈춰도 예전 지시문으로 답할 뿐).
- **다음 단계로 넘기는 질문**: "저장소가 404(그런 지시문 없음)를 주면 이 기본 지시문은 어떻게 할까?" → Lab 02 과제 2.
