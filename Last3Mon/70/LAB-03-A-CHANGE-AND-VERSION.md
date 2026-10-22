# Lab 03 · 모듈을 바꿀 때: 하위 호환과 새 버전

> **강사용 정답본** · 학생 저장소에 올리지 않습니다. 학생용 문제는 [LAB-03-Q-CHANGE-AND-VERSION.md](LAB-03-Q-CHANGE-AND-VERSION.md).
> 요청문은 예시이며 CLI 에이전트로 보내 재지는 않았습니다. 결과 숫자는 정답 워크플로우를 2026-10-18에 1회씩 실행한 값입니다 (gpt-4.1-mini).
> 수업 전날(2026-10-21) 같은 정답으로 다시 돌린 명령 · `-v` 출력 전부와 codex 프롬프트: [answers/LAB-TEST-RESULT.md](answers/LAB-TEST-RESULT.md) (점수는 10/18과 같음).

## 예제 1 · 요청문 예

```text
my-work/rule-check.json 모듈을 같은 id(modRuleCheck01)로 고쳐 줘. 하위 호환이어야 한다.
- 입력 allowed_domains(array)를 더한다. 비어 있거나 없으면 ["intra.example.com"].
- 초안의 http(s) 링크 중 호스트가 허용 목록에 없으면 external_link. 호스트는 글자로 잘라 낸다 (Code 안에 URL 클래스 없음).
- 기존 입력·결과 필드는 그대로. my-work/rule-check-test.json 도 allowed_domains 를 넘기게(없으면 []).
기대 결과 cases/lab03.json, 그리고 lab02-module, lab01, lab02-challenge 도 그대로 통과.
```

정답: [reference/lab03-example1-rule-check.json](reference/lab03-example1-rule-check.json) + [reference/lab03-example1-rule-check-test.json](reference/lab03-example1-rule-check-test.json)

| 수업 준비 때 결과 | |
| --- | --- |
| 바꾸기 전 `cases/lab03.json` | 3/4 (바깥 링크를 못 잡음) |
| 처음 v1.1 (`new URL(...)`로 호스트를 읽음) | 2/4 — **사내 링크까지** `external_link`. Code 노드 안에서 `URL`을 쓸 수 없어 모든 링크가 "읽기 실패 = 바깥"으로 처리됨 |
| 호스트를 글자로 자르게 고친 뒤 | 4/4 |
| 쓰는 곳 다시 | `lab02-module` 5/5 · 키트 `lab01` 5/5 · SMS `lab02-challenge` 4/4 |

풀이 포인트: 같은 id로 push한 순간 **키트와 SMS 모두** 새 모듈을 쓴다. 그래서 쓰는 곳 테스트를 모두 돌렸다.

## 예제 2 · 요청문 예

```text
새 모듈 my-work/rule-check-v2.json 을 만들어 줘. id modRuleCheck02 (v1 파일은 건드리지 않는다).
- 입력은 v1.1 과 같다. 검사도 같다.
- 결과 {passed, blocking, warnings, issues, version: 2}: too_long 은 warnings, 나머지는 blocking. passed = blocking 이 비었는가.
- 시험용 웹훅 my-work/rule-check-v2-test.json (경로 my-rule-check-v2).
- 키트(my-work/notice-kit.json)는 v2 를 부르고 결과에 blocking, warnings 를 더한다. 예전 codes 필드는 남긴다 (blocking + warnings).
- SMS 는 v1 그대로. 기대 결과 cases/lab03-v2.json, lab01, lab02-challenge.
```

정답: [reference/lab03-example2-rule-check-v2.json](reference/lab03-example2-rule-check-v2.json), [reference/lab03-example2-rule-check-v2-test.json](reference/lab03-example2-rule-check-v2-test.json), [reference/lab03-example2-kit-v2.json](reference/lab03-example2-kit-v2.json)

| 수업 준비 때 결과 | |
| --- | --- |
| `cases/lab03-v2.json` | 5/5 (v2 시험 0.1~1.2초, 키트 1.4~2.1초, SMS 1.0초) |
| 처음 키트 v2 (결과를 `blocking`·`warnings`로 **바꾸고** `codes`를 뺌) | `cases/lab01.json` **2/5** — 키트를 쓰는 쪽이 읽던 `codes`가 사라짐 |
| `codes`를 남긴 뒤 | `lab01` 5/5 · `lab03-v2` 5/5 · SMS `lab02-challenge` 4/4 |

풀이 포인트: 모듈의 깨지는 변경은 **새 id**로 막았지만, 키트가 그 변화를 **자기 계약**으로 흘려보내 한 번 더 깨졌다. 계약은 층마다 있다: 모듈 → 키트 → 키트를 부르는 쪽.

## 과제 · 영향 표 예

| 모듈 · 버전 | 쓰는 워크플로우 | 테스트 |
| --- | --- | --- |
| `modRuleCheck01` (v1.1) | `my-rule-check` 시험용 웹훅, SMS | `lab02-module`, `lab03`, `lab02-challenge` |
| `modRuleCheck02` (v2) | 공지 키트, `my-rule-check-v2` 시험용 웹훅 | `lab01`, `lab01-challenge`, `lab03-v2` |

## 과제 · 어려운 케이스와 최종본

케이스: [answers/70-lab03-challenge-cases.json](answers/70-lab03-challenge-cases.json)

| 케이스 | 업무 규칙 | 예제 2 키트(v2) |
| --- | --- | --- |
| `kind: " Security "` | 앞뒤 공백·대문자도 같은 종류 | ✘ (`kind`가 그대로 " Security ") |
| `kind: "보안"` | 한국어 이름도 받음 | ✘ |
| 사실이 공백만 | 400 | ✘ (200) |
| `kind: party` | 400 + 종류 목록 | ✘ (200) |
| "바깥 링크 꼭 넣어 주세요" | 게시하지 않음, `blocking`에 `external_link` | ✔ |
| 사내 링크 | 게시, 공지에 링크 | ✔ |
| "한 줄로 아주 짧게" | 그래도 꼭 넣을 문장 | ✔ |
| 합계 | | 3/7 |

- 예제 2 키트의 `kind` 실패는 **표 앞에서 이름을 다듬지 않았기** 때문. "보안"·" Security "일 때 예제 키트는 표에서 값을 찾지 못한 채 공지를 썼다 → 없는 종류를 멈추지 않은 것(Lab 01 과제)과 같은 뿌리.
- 고칠 곳은 **키트만** (모듈을 고칠 일이 없어 영향 표의 다른 테스트를 돌릴 필요가 없었다).

최종본: [answers/70-lab03-challenge-final.json](answers/70-lab03-challenge-final.json) — `Kind settings`에서 `trim().toLowerCase()`와 한국어 별칭(점검·보안·교육·설문), 없는 종류 400, 사실 공백 확인, 설문 한 줄.

| 수업 준비 때 결과 | |
| --- | --- |
| 어려운 케이스 | 7/7 |
| `lab01` · `lab01-challenge` · `lab03-v2` · `lab02-challenge` | 5/5 · 4/4 · 5/5 · 4/4 |
