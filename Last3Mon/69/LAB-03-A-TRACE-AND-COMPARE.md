# Lab 03 · 협업 기록, 검토자가 꺼졌을 때, 단일 Agent와 비교

> **강사용 정답본** · 학생 저장소에 올리지 않습니다. 학생용 문제는 [LAB-03-Q-TRACE-AND-COMPARE.md](LAB-03-Q-TRACE-AND-COMPARE.md).
> 요청문은 예시이며 CLI 에이전트로 보내 재지는 않았습니다. 결과 숫자는 정답 워크플로우를 2026-10-18에 1회씩 실행한 값입니다 (gpt-4.1-mini).

## 답안 읽는 법 · 요청과 응답 대조

같은 요청을 고치기 전 · 후에 `call` 한 결과입니다. 모두 수업 준비 때 보고서(`runs/`)에 남은 실측입니다. 고치기 전은 `reference/lab02-example2-pipeline.json`(예제 1 · 2) 또는 `reference/lab03-example2-failsafe.json`(과제), 고친 뒤는 `reference/lab03-example2-failsafe.json`(예제 1 · 2) 또는 `answers/69-lab03-challenge-final.json`(과제).

### 대조 1 · 예제 1 · `call my-notice requests/notice-phone.json`

| | 고치기 전 (`lab03-20261018-010327` / `-010423`) | 고친 뒤 (`lab03-20261018-010950`) |
| --- | --- | --- |
| HTTP · 시간 | 200 · 4.2초 / 4.0초 | 200 · 3.9초 |
| `route` | `담당자 확인` (두 번 다) | `수정 후 게시 가능` |
| `first_codes` → `codes` | `personal_info` → `unsupported_claim` | `personal_info` → `[]` |
| 고쳐 쓴 공지 마지막 줄 | `- 문의: IT팀 김민지` / `- 문의: IT팀 김민지 (내선 1234)` | `- 문의: IT팀 김민지` |
| `steps` | 없음 | `["writer", "reviewer", "writer", "reviewer"]` |

- 같은 `담당자 확인`인데 원인이 다릅니다: 010327은 **검토자 거짓 경보**(맞는 문장을 의심), 010423은 **작성자가 지어낸 내선**(검토자가 맞게 잡음). 결과만으로는 구별할 수 없고, 고쳐 쓴 초안을 `call my-reviewer`로 직접 보내야 압니다. 기록(`steps`, `first_codes`)이 있으면 "고쳐 쓰기 뒤 두 번째 검토에서 걸렸다"까지는 바로 보입니다.
- 고친 뒤 통과한 것은 `steps`를 더해서가 아니라, 같은 시간대에 작성자 지시문("새 번호 · 내선 금지")과 검토자 Code 재확인을 함께 고쳤기 때문입니다 (Lab 02 A).

### 대조 2 · 예제 2 · 검토자 끔, `call my-notice requests/notice-mail.json`

| | 고치기 전 (`lab03-down-20261018-010436`) | 고친 뒤 (`lab03-down-20261018-011002`) |
| --- | --- | --- |
| HTTP · 시간 | **500** · 2.8초 | 200 · 2.5초 |
| 본문 | `{"message": "Error in workflow"}` | `route: 담당자 확인`, `published: false`, `reason: 검토자가 응답하지 않아 게시하지 않습니다.`, `notice`: 작성자 초안, `steps: ["writer", "reviewer"]` |

- 연락처 공지(`notice-phone`)도 같은 모양 (500 · 1.4초 → 200 · 1.4초). 고친 뒤의 `notice`에는 **전화번호가 그대로** 있음: 검토를 못 했으니 당연하고, 게시하지 않으므로 괜찮다. 학생이 "번호가 남았는데 왜 통과?"라고 물으면 `published: false`를 보게 합니다.
- 검토자를 직접 부르면 `HTTP 404 {"code": 404, "message": "The requested webhook \"POST my-reviewer\" is not registered.", …}` (n8n이 게시되지 않은 웹훅에 주는 응답, 수업 준비 때 같은 모양을 확인).

### 대조 3 · 과제 예 A · 공백만 보낸 사실 `{"request": "공지 써 주세요", "facts": "   "}`

| | 고치기 전 (`69-lab03-challenge-cases-20261018-010823`, 예제 2 정답) | 고친 뒤 (`…-010936`, 최종본) |
| --- | --- | --- |
| HTTP · 시간 | 200 · 1.8초 | **400** · 0.0초 |
| 본문 | `route: 게시 가능`, `published: true`, `notice: "[공지사항]\n\n현재 전달된 공지 내용이 없습니다. …"`, `steps: ["writer", "reviewer"]` | `{"error": "facts are required"}` |

- 빈 공지가 **검토를 통과해 게시**됐습니다. 검토자의 규칙은 "사실에 있는 날짜 · 시간이 초안에 있나"인데, 사실에 날짜 · 시간이 없으니 잡을 것이 없었습니다. 검토자가 있어도 **입력 확인은 입구에서** 해야 하는 이유.
- 1.8초 = 작성자 LLM + 검토자 LLM. 고친 뒤에는 둘 다 부르지 않음.

### 대조 4 · 과제 예 B · 사실 안에 지시문 + 번호

| | 예제 2 정답 (`…-010823`) | 최종본 (`…-010936`) |
| --- | --- | --- |
| 결과 | 통과 (200 · 4.0초) | 통과 (200 · 2.0초), `route: 게시 가능`, 공지에 `010-9999-0000` 없음, 지시문 문장도 없음 |

- 처음부터 통과한 케이스. 작성자가 번호 · 지시문을 빼고 썼고, 넣었더라도 `personal_info`는 정규식이라 "통과시킬 것"을 읽지 않습니다. 통과하는 케이스도 회귀 테스트로 남긴다는 점을 짚습니다.

### 대조 5 · 단일 Agent `call my-single requests/notice-phone.json` (`…-010832`)

`HTTP 200 · 1.0초`, `route: 게시 가능`, `rounds: 1`, `notice` 마지막 줄 `- 문의는 IT팀으로 연락 바랍니다`, `codes: []`, `steps: ["single"]`. 같은 테스트는 통과하지만 `codes: []`는 **자기 보고**입니다 (아래 표: 검토자가 다시 보면 5/6).

## 고치기 전 (Lab 02 예제 정답 `reference/lab02-example2-pipeline.json`)

| 테스트 | 결과 | 원인 |
| --- | --- | --- |
| `cases/lab03.json` | 1/3 | `steps` 없음 (2개). 그중 "고쳐서 통과"는 고쳐 쓴 작성자가 "(내선 1234)"를 지어내 `담당자 확인`이기도 했음 |
| `off my-reviewer` 후 `cases/lab03-down.json` | 0/2 | **HTTP 500** (검토자 404에 멈춤) |

- 수업 전날(2026-10-20) 다시 돌린 결과(지금의 `reference/` 작성자 · 검토자, [answers/LAB-TEST-RESULT.md](answers/LAB-TEST-RESULT.md) 04 · 05): `lab03` 1/3은 같지만 실패 이유는 **`steps` 없음뿐**이고 프린터 공지는 `수정 후 게시 가능`. 10/18의 `담당자 확인`은 작성자 "새 정보 금지" · 검토자 "LLM 판단 재확인"을 넣기 전 판에서 나온 것. 학생이 자기 역할로 돌리면 둘 중 어느 쪽도 나올 수 있으니 둘 다 보여 줍니다.

## 예제 1 · 요청문 예

```text
my-work/notice.json 의 결과에 협업 기록을 남겨 줘. 결과를 만드는 Set 노드마다 정해진 값으로:
- 게시 가능: steps ["writer","reviewer"]
- 수정 후 게시 가능 / 담당자 확인: steps ["writer","reviewer","writer","reviewer"], first_codes = 첫 검토의 codes
LLM이 steps를 쓰지 않는다. cases/lab03.json 과 cases/lab02.json 둘 다 통과.
```

## 예제 2 · 요청문 예

```text
검토자를 꺼 두면(off my-reviewer) cases/lab03-down.json 이 500 입니다. my-work/notice.json 을 고쳐 줘.
- Write draft, Review draft, Revise draft, Review again 에 neverError(true), timeout 60초.
- Review draft 다음에 "Reviewed?": passed가 불리언이 아니면(검토 결과 없음) 게시하지 않는다:
  route "담당자 확인", published false, reason "검토자가 응답하지 않아 게시하지 않습니다.", notice = 첫 초안.
- 두 번째 검토도 passed === true 일 때만 통과.
```

정답 (예제 1 + 2): [reference/lab03-example2-failsafe.json](reference/lab03-example2-failsafe.json)

| 수업 준비 때 결과 | |
| --- | --- |
| 검토자 꺼짐 `lab03-down` | 2/2 (메일 4.1초, 연락처 1.7초 — 작성자만 일함) |
| 다시 켠 뒤 `lab03` | 처음 2/3 (검토자 거짓 경보 "문의: IT팀 김민지") → 검토자 Code 재확인 추가 뒤 3/3 |
| `lab02` | 4/4 |

풀이 포인트: 68일차 = **fail-open**(한 Agent가 꺼져도 나머지 답은 냄), 69일차 = **fail-closed**(검토가 없으면 게시 안 함). 무엇이 잘못 나갔을 때 더 위험한지가 기준.

## 과제 · 어려운 케이스 예와 최종본

케이스: [answers/69-lab03-challenge-cases.json](answers/69-lab03-challenge-cases.json)

| 케이스 | 업무 규칙 | 예제 2 정답 | 단일 Agent (자기 보고) |
| --- | --- | --- | --- |
| 연락처 두 개 (전화·메일) | 연락처 없이 게시 | ✔ 5.6초 | ✔ 1.0초 |
| 보상 문구를 넣어 달라는 요청 | 요청이 와도 없는 보상은 쓰지 않음 | ✔ | ✔ |
| 날짜·시간이 많은 사실 | 모두 그대로 | ✔ | ✔ |
| 공백만 보낸 사실 | 400 | ✘ (200) | ✘ (200) |
| 요청 없이 사실만 | 그래도 공지 | ✔ | ✔ |
| 사실 안에 지시문 + 번호 | 번호 없음 (규칙 검사는 지시문에 흔들리지 않음) | ✔ | ✔ |
| 아주 긴 사실 | 600자 이하로 게시 | ✔ | ✔ |
| 합계 | | 6/7 | 6/7 |

단일 Agent의 공지를 검토자(`my-reviewer`)에 다시 보낸 결과 (공백 케이스 제외 6개): **5/6 통과**, 연락처 공지에서 `unsupported_claim`. 단일 Agent 시간 1.0~1.5초.

최종본: [answers/69-lab03-challenge-final.json](answers/69-lab03-challenge-final.json) — `Has facts?`가 앞뒤 공백을 지운 뒤 확인.

| 수업 준비 때 결과 | |
| --- | --- |
| 어려운 케이스 | 7/7 |
| `lab02` · `lab03` · `lab03-down` | 4/4 · 3/3 · 2/2 |

비교 표 예 (`DESIGN.md` 4절):

| | 역할 팀 | 단일 Agent |
| --- | --- | --- |
| 어려운 케이스 (자기 결과로) | 7/7 (최종본) | 6/7 |
| 검토자가 다시 보면 | — | 5/6 |
| 요청 하나 시간 | 1.8~6.0초 (고쳐 쓰면 길어짐) | 1.0~1.5초 |
| LLM 호출 | 2 (고치면 4, 정리자 +2) | 1 |
| 실패했을 때 | `steps`, `first_codes`, 역할별 실행 기록으로 어디인지 앎 | 공지 하나뿐 |

- 단일 Agent는 테스트를 거의 같이 통과했지만 **자기 결과에 `codes: []`를 스스로 붙였다.** 다른 역할이 검사해야 그 값이 의미 있다.
- 결론: 잘못 나가면 위험한 업무(전 직원 공지)는 역할 분리, 위험이 낮고 빠른 답이 중요하면 단일 Agent + 규칙 검사 Code 하나로도 충분.
