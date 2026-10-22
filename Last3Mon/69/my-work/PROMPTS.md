# Lab 01 예제 2 · 작성자 요청문과 확인 사항

## 만들 워크플로우

- 파일: `my-work/writer.json`
- 웹훅: `POST /webhook/my-writer`
- 입력: `request`, 필수 `facts`, 선택 `previous_draft`·`feedback`; `author`는 요청자 정보이며 공지 사실을 늘리는 근거가 아니다.
- 결과: `{"draft": "..."}`만 반환한다. `facts`가 비면 HTTP 400 `{"error": "facts are required"}`.
- 모델: OpenAI `gpt-4.1-mini`; 자격 증명은 `openAiCourse0001` 참조만 사용한다.

## ▶ 1단계 · 역할 카드를 요청문으로

작성자는 `facts`만 사용해 한국어 IT 공지 초안을 쓴다. 첫 줄은 `[제목]`, 다음은 짧은 3~6줄로 구성한다. 서비스 영향과 사용자가 할 일을 빠짐없이 담고, 날짜·요일·시간 범위는 사실의 표기를 그대로 옮긴다(`10월 23일(목)`, `22:00~24:00`). 검토 결과(`passed`, `codes`, `issues`)를 만들거나 스스로 합격 판정을 하지 않는다. 요청문에 있더라도 사실에 없는 쿠폰·보상·연락처·일정을 추가하지 않는다. `cases/lab01.json`은 메일 공지의 날짜·시간·보상 없음, VPN 공지의 마감일·제목 줄을 확인한다.

## ▶ 2단계 · 나중에 고쳐 쓰게 될 것

Lab 02에서 사용할 `previous_draft`와 `feedback`을 선택 입력으로 받는다. 검토 의견이 오면 이전 초안의 지적된 부분을 모두 고치되 `facts` 밖의 정보를 더하지 않는다. 개인 연락처를 빼라는 의견을 받았을 때 다른 번호·내선·메일 주소로 대체하지 않는다. 고친 결과도 `draft` 하나로 반환한다.

## ▶ 3단계 · 보내기 전 점검표

- [x] 파일·웹훅·입력·결과 계약을 정했다 (`my-work/writer.json`, `my-writer`, `{"draft": "..."}`).
- [x] 사실만 쓰고 날짜·시간을 원문 그대로 옮기도록 지시했다.
- [x] 검토하지 않으며 사실에 없는 약속을 더하지 않도록 지시했다.
- [x] `facts`가 비면 LLM 호출 전에 HTTP 400으로 응답한다.
- [x] 테스트 파일을 확인했다: `cases/lab01.json`.

`requests/notice-phone.json`에는 사실 자체에 개인 전화번호와 메일 주소가 있다. 작성자가 이를 초안에 옮기더라도 개인 연락처의 게시 차단은 별도 검토자의 `personal_info` 규칙이 맡는다.

---

# Lab 01 과제 · 검토자 요청문과 확인 사항

## 만들 워크플로우

- 파일: `my-work/reviewer.json`; 웹훅: `POST /webhook/my-reviewer`.
- 입력: `facts`, `draft` 모두 필수. 둘 중 하나가 비면 LLM 호출 없이 HTTP 400 `{"error": "facts and draft are required"}`.
- 결과: `{"passed": true/false, "codes": [...], "issues": [{"code": "...", "detail": "..."}]}`. 고친 초안은 반환하지 않는다.
- 검토 코드: `missing_fact`, `personal_info`, `too_long`, `unsupported_claim`.
- 테스트: `cases/lab01-challenge.json`의 좋은 초안, 시간 빠짐, 전화번호, 없는 쿠폰 약속, 600자 초과, 빈 초안 여섯 사례.

## ▶ 1단계 · 규칙과 LLM을 어디서 나누나

`Review webhook` → `Has facts and draft?` → `Rule checks` → `Claim check agent` → `Build review` → `Send result` 순서다. 입력이 비면 `Reject empty`로 보낸다. `Rule checks` Code 노드 하나에서 날짜·시간 누락, 전화번호·메일 주소, 600자 초과를 결정적으로 검사한다. `Claim check agent`는 `facts`와 `draft`를 함께 받고 사실에 없는 약속·보상·새로운 주장만 판단한다. `Build review` Code 노드가 두 결과를 합쳐 `passed`, `codes`, `issues`를 만든다. 검토자는 초안을 다시 쓰지 않는다. 초안이 있으면 LLM을 한 번 호출하고, 입력이 비면 호출하지 않는다.

## ▶ 2단계 · 날짜·시간을 어떻게 찾나

Code가 `facts`에서 `10월 23일` 같은 날짜와 `22:00`, `24:00` 같은 시간을 추출한다. 초안과 비교할 때 공백을 제거하므로 `10월23일`도 같은 날짜로 본다. 빠진 값은 `missing_fact`의 `issues[].detail`에 `22:00, 24:00`처럼 나열해 Lab 02 작성자가 무엇을 고칠지 알 수 있게 한다. 전화번호·메일 주소는 `personal_info`, 600자 초과는 `too_long`으로 별도 기록한다.

## ▶ 3단계 · LLM 검토자도 틀린다

LLM에는 사실에 있는 내용을 표현만 바꾸거나 줄여 쓴 문장, 사실에 적힌 담당자 이름·연락처, 단순한 사과·감사 표현을 `unsupported_claim`으로 보지 말라고 지시했다. LLM 응답은 JSON으로 파싱하고, 마지막 Code에서 보고된 문장의 단어가 모두 사실에 있는 경우 한 번 더 걸러 거짓 경보를 줄인다. 그래도 좋은 초안이나 전화번호 사례에 `unsupported_claim`이 붙으면 `issues[].detail`과 `facts`를 나란히 보고 판단을 수정한다. 기대 결과를 맞추려고 `cases/lab01-challenge.json`을 바꾸지 않는다.

## 확인할 요청과 기대 결과

| 요청 | 기대 결과 |
| --- | --- |
| `requests/review-good.json` | `passed: true`, `codes: []` |
| `requests/review-missing-time.json` | `codes: ["missing_fact"]`, `detail`에 빠진 시간 |
| `requests/review-personal-info.json` | `codes: ["personal_info"]`, `detail`에 개인 연락처 |
| `requests/review-added-promise.json` | `codes: ["unsupported_claim"]`, `detail`에 쿠폰 약속 |
| `requests/review-too-long.json` | `codes`에 `too_long` 포함 |
| `requests/review-empty.json` | HTTP 400 |

`uv run tools/flow.py call my-reviewer requests/review-personal-info.json`이 HTTP 404면 아직 웹훅이 게시되지 않은 것이다. 게시 후에는 위 결과 모양을 확인하고 `uv run tools/flow.py test cases/lab01-challenge.json -v --repeat 3`으로 반복 검사한다. 첫 네 정상·오류 사례의 `codes`는 표의 값과 정확히 같아야 한다.

---

# Lab 02 예제 1 · 계약 맞추기 (10분)

공지 팀은 작성자와 검토자를 HTTP로 부른다. 공지 팀을 만들기 전에 두 역할이 [AGENTS.md](../AGENTS.md) 3절의 계약대로 답하는지 각각 직접 확인한다. 이 단계에서 새 워크플로우 파일은 만들지 않는다.

## ① 보내는 요청

`requests/notice-phone.json`에는 다음 공지 요청이 있다.

```json
{"request": "프린터 드라이버 업데이트 공지를 써 주세요. 문의처 연락처도 꼭 넣어 주세요.",
 "facts": "10월 30일(목) 18:00~19:00 사내 프린터 드라이버 일괄 업데이트. 업데이트 중에는 출력이 안 됨. 문의는 IT팀 김민지(010-1234-5678, minji.kim@example.com).",
 "author": "김민지"}
```

`requests/review-personal-info.json`은 같은 `facts`와 마지막 줄이 `문의: IT팀 김민지(010-1234-5678)`인 초안을 검토자에게 보낸다. 이 초안은 Lab 01 과제의 개인 연락처 사례다.

## ② · ③ 두 역할을 직접 부르고 결과 확인

```bash
cd /Users/jbbdyee/Developer/ai-engineering-lab/Last3Mon/69
uv run tools/flow.py push my-work/writer.json my-work/reviewer.json
uv run tools/flow.py call my-writer requests/notice-phone.json
uv run tools/flow.py call my-reviewer requests/review-personal-info.json
```

검토자의 기대 응답 모양은 다음과 같다. `0.7s`는 수업 준비 당시의 예시 시간이며 실제 실행 시간은 달라질 수 있다.

```text
HTTP 200 · 0.7s
{"passed": false, "codes": ["personal_info"], "issues": [{"code": "personal_info", "detail": "010-1234-5678"}]}
```

| 확인 | 왜 확인하나 |
| --- | --- |
| 작성자 결과에 `draft` 하나가 있는가 | 공지 팀이 `$json.draft`로 초안을 읽는다. |
| 검토자 결과에 불리언 `passed`, 목록 `codes`, `issues[].detail`이 있는가 | 공지 팀이 `passed`로 갈림길을 정하고 `issues`로 고쳐 쓰기 의견을 만든다. |
| 작성자에게 `previous_draft`, `feedback`을 주면 고쳐 쓰는가 | 아래 ④에서 직접 확인한다. |

## ④ 고쳐 쓰기를 직접 시험하기

`call` 뒤에 JSON을 직접 쓴다. 위 검토 결과의 `issues`를 `feedback` 글자로 바꾸고, 처음 초안을 `previous_draft`로 넣는다.

```bash
uv run tools/flow.py call my-writer '{"request": "프린터 드라이버 업데이트 공지를 써 주세요. 문의처 연락처도 꼭 넣어 주세요.", "facts": "10월 30일(목) 18:00~19:00 사내 프린터 드라이버 일괄 업데이트. 업데이트 중에는 출력이 안 됨. 문의는 IT팀 김민지(010-1234-5678, minji.kim@example.com).", "previous_draft": "[프린터 드라이버 업데이트 안내]\n10월 30일(목) 18:00~19:00에 사내 프린터 드라이버를 일괄 업데이트합니다.\n업데이트 중에는 출력이 안 됩니다.\n문의: IT팀 김민지(010-1234-5678)", "feedback": "personal_info: 010-1234-5678"}'
```

수업 준비 때 공지 팀 안에서 고쳐 쓴 결과의 마지막 줄은 다음 모양이었다. LLM의 실제 문장은 달라질 수 있다.

```json
{"draft": "[프린터 드라이버 업데이트 안내]\n…\n문의는 IT팀 김민지에게 연락 바랍니다."}
```

번호와 메일 주소는 빠지고 날짜와 시간은 그대로 남아야 한다. 새로운 정보도 생기면 안 된다. 수업 준비 때 한 번은 작성자가 지운 번호 대신 `(내선 1234)`를 지어냈으므로, 이런 대체 연락처가 없는지도 확인한다. 처음과 같은 초안이 돌아오면 작성자가 `previous_draft`와 `feedback`을 읽지 않는 것이므로 공지 팀을 만들기 전에 작성자부터 고친다.

## ▶ 1단계 · 계약이 안 맞으면

결과 필드가 `text`나 `ok`처럼 다르게 오면 공지 팀에서 임시로 바꾸지 말고 해당 역할의 결과를 계약에 맞춘다. 작성자는 `draft`, 검토자는 `passed`·`codes`·`issues`를 반환해야 한다. 그러면 다른 사람의 역할인 `reference/lab02-start-reviewer.json`도 같은 계약으로 바꿔 끼울 수 있다.

---

# Lab 02 예제 2 · 공지 팀 (25분)

## 만들 워크플로우와 계약

- 파일: `my-work/notice.json`; 웹훅: `POST /webhook/my-notice`.
- 입력: `request`, 필수 `facts`, `author`. `facts`가 비면 HTTP 400 `{"error": "facts are required"}`.
- 순서: 작성자(`my-writer`) → 검토자(`my-reviewer`) → 첫 검토가 실패하면 작성자에게 의견을 주고 **한 번만** 고쳐 쓰기 → 검토자 재호출. 두 역할은 HTTP로 호출하고 공지 팀 안에서 작성·검토를 재구현하지 않는다.
- 결과: `route`, 불리언 `published`, 숫자 `rounds`, `notice`, 목록 `codes`. 고쳐 쓴 경로에는 첫 검토의 `first_codes`도 포함한다.
- 경로: 첫 검토 통과 `게시 가능`; 수정 후 통과 `수정 후 게시 가능`; 두 번째도 실패 `담당자 확인`(게시하지 않음). 이때 `codes`는 두 번째 검토 결과다.
- 테스트: `cases/lab02.json`.

## ① 보내는 요청

Lab 01에서 쓴 `requests/notice-mail.json`, `requests/notice-vpn.json`, `requests/notice-phone.json`, `requests/notice-empty.json`을 공지 팀에 그대로 보낸다. 공지 팀의 입력은 작성자와 같은 요청이다.

## ② 지금 결과와 ③ 나와야 할 결과

아직 공지 팀을 게시하지 않았다면 `uv run tools/flow.py call my-notice requests/notice-phone.json`은 `HTTP 404`(`POST my-notice` 웹훅 미등록)가 될 수 있다. 아래 내용은 수업 준비 당시 기대 모양이며 실행 시간과 공지 문장은 달라질 수 있다.

| 요청 | 기대 경로와 필드 |
| --- | --- |
| `notice-mail` | HTTP 200, `route: 게시 가능`, `published: true`, `rounds: 1`, `codes: []`, `notice`에 `10월 23일(목) 22:00~24:00` 및 메일 점검 안내 |
| `notice-phone` | HTTP 200, `route: 수정 후 게시 가능`, `published: true`, `rounds: 2`, `codes: []`, `first_codes: ["personal_info"]`, `notice`에서 전화번호·메일 주소 제거 |
| `notice-empty` | HTTP 400, `{"error": "facts are required"}` |

프린터 공지는 첫 검토에서 개인 연락처가 걸리며, 수정 후 두 번째 검토가 통과해야 한다. 따라서 두 역할을 각각 두 번씩 부를 수 있어 한 번에 통과한 경우보다 시간이 길다. 고쳐도 실패하면 `route: 담당자 확인`, `published: false`, 두 번째 검토의 `codes`를 반환한다.

## ④ 테스트가 보는 곳 · `cases/lab02.json`

| 케이스 | 확인할 결과 |
| --- | --- |
| 메일 점검 · 게시 | `published: true`, `codes: []`, `route`에 `게시 가능`, `notice`에 `22:00` |
| VPN · 게시 | `published: true`, `codes: []`, `notice`에 `10월 24일` |
| 연락처가 든 사실 · 고쳐서 게시 | `published: true`, `codes: []`, `route`에 `게시 가능`, `notice`에 `010-1234-5678`과 `minji.kim@example.com` 없음 |
| 사실 없음 | HTTP 400 |

## ⑤ 만들고 확인

```bash
cd /Users/jbbdyee/Developer/ai-engineering-lab/Last3Mon/69
uv run tools/flow.py push my-work/notice.json
uv run tools/flow.py call my-notice requests/notice-phone.json
uv run tools/flow.py test cases/lab02.json -v
```

수업 준비 때 테스트는 4/4였고, 처음에는 검토자의 거짓 경보로 3/4가 나온 적이 있다. `notice-phone`의 수정 전후 공지를 비교해 번호 외에 무엇이 바뀌었는지 살펴보고, n8n **Executions**에서 `my-notice` 한 번에 `my-writer`·`my-reviewer` 실행이 몇 개 생겼는지도 확인한다.

## ▶ 1단계 · 흐름을 먼저 그리기

`my-work/DESIGN.md` 3절의 Mermaid에 작성 → 검토 → 통과 여부 → 게시 또는 고쳐 쓰기 → 재검토 → 게시 또는 담당자 확인을 그렸다. 화살표에 `draft`, `issues`에서 만든 `feedback`, 원래 `facts`의 출처를 표시했고, ③의 세 결과가 각각 어느 끝인지 구분했다.

## ▶ 2단계 · 왜 한 번만 고쳐 쓰나

통과할 때까지 반복하면 두 역할이 끝없이 주고받거나 수정할수록 공지가 나빠질 수 있다. 따라서 `Revise draft`와 `Review again`을 각각 한 노드씩 별도로 두고, 두 번째 검토가 실패하면 `담당자 확인`으로 끝낸다. 반복 고리로 앞 노드에 되돌리지 않는다.

## ▶ 3단계 · 넘기는 값의 출처

두 번의 검토에서 `facts`는 항상 `Notice webhook`의 원래 요청에서 가져온다. 작성자의 응답에 사실이 섞이거나 바뀌어도 검토 기준이 흔들리지 않게 한다. 첫 검토의 `issues`를 `code: detail` 줄로 합쳐 수정 요청의 `feedback`에 넣고, 첫 초안은 `previous_draft`로 보낸다.

## ▶ 4단계 · 보내기 전 점검표

- [x] 새 파일 `my-work/notice.json`, 웹훅 `my-notice`, 호출 주소 `my-writer`·`my-reviewer`를 정했다.
- [x] 고쳐 쓰기 1회와 세 경로의 `route` 값을 정했다.
- [x] `published`, `rounds`, `notice`, `codes`, 수정 경로의 `first_codes`를 정했다.
- [x] 원래 `facts`를 검토자에게 보내고 첫 `issues`로 `feedback`을 만든다.
- [x] 테스트 파일은 `cases/lab02.json`이다.

---

# Lab 02 과제 · 정리자 둘을 나눠 돌리고 모으기 (35분)

팀장의 요청: 통과한 공지를 메일과 메신저에도 보내기 위해 메일 제목 한 줄과 메신저용 짧은 글을 함께 만든다. 두 정리자는 서로의 결과를 기다릴 필요가 없으므로 한 갈래에서 둘로 나누고 다시 모은다.

## 조건과 ① 보내는 요청

- 고칠 파일은 기존 `my-work/notice.json` 하나다. 승인된 결과에 `title`(메일 제목, 괄호 없는 한 줄·40자 이내), `chat`(메신저 글, 2줄·120자 이내, 날짜·시간 그대로)을 추가한다.
- `게시 가능`, `수정 후 게시 가능`에서만 정리자를 실행한다. `담당자 확인`에서는 만들지 않는다.
- 입력은 예제 2와 같은 `requests/notice-mail.json`, `requests/notice-vpn.json`, `requests/notice-phone.json`, `requests/notice-empty.json`이다.
- `cases/lab02-challenge.json`과 기존 `cases/lab02.json` 모두 통과해야 한다.

## ② 지금 결과와 ③ 나와야 할 결과

예제 2 결과에는 `title`·`chat`이 없다. 과제 후 승인된 응답은 기존 `route`, `published`, `rounds`, `notice`, `codes`와 수정 시 `first_codes`를 유지하고 두 필드만 더한다. 수업 준비 당시 예시는 아래와 같다. 실제 문장과 시간은 달라질 수 있다.

| 요청 | 추가될 내용과 지켜야 할 것 |
| --- | --- |
| `notice-mail` | `title`에 메일 서버 **점검** 안내, `chat`에 `10월 23일(목) 22:00~24:00` 점검·송수신 불가·재실행 안내. `쿠폰`은 없음. |
| `notice-phone` | `route: 수정 후 게시 가능`, `first_codes: ["personal_info"]`; `title`에 프린터 드라이버 업데이트 안내, `chat`에 `10월 30일(목) 18:00~19:00`과 출력 불가·IT팀 문의. `notice`와 `chat`에 전화번호·메일 주소 없음. |
| `notice-empty` | 기존대로 HTTP 400. 정리자를 호출하지 않음. |
| `담당자 확인` | `published: false`; 정리자를 호출하거나 `title`·`chat`을 만들지 않음. |

메신저 글도 검토 중 지운 개인 연락처를 되살리면 안 된다. 예제 2의 기존 필드는 그대로 남아야 기존 `lab02` 검사도 계속 통과한다.

## ④ 테스트가 보는 곳 · `cases/lab02-challenge.json`

| 케이스 | 확인할 결과 |
| --- | --- |
| 메일 점검 · 제목과 메신저 | `published: true`, `title`에 `점검`, `chat`에 `10월 23일`, `chat`에 `쿠폰` 없음 |
| VPN · 메신저에 마감일 | `chat`에 `10월 24일`, `title`에 `VPN` 또는 `인증서` |
| 고쳐서 게시 · 메신저에도 연락처 없음 | `published: true`, `chat`·`notice`에 `010-1234-5678`·`minji.kim@example.com` 없음 |
| 사실 없음 | HTTP 400 |

## ⑤ 만들고 확인

```bash
cd /Users/jbbdyee/Developer/ai-engineering-lab/Last3Mon/69
uv run tools/flow.py push my-work/notice.json
uv run tools/flow.py call my-notice requests/notice-mail.json
uv run tools/flow.py test cases/lab02-challenge.json -v --repeat 3
uv run tools/flow.py test cases/lab02.json -v
```

수업 준비 때는 과제 테스트 4/4, 기존 테스트 4/4였다. 현재 워크플로우를 게시한 뒤 실제 결과를 따로 확인해야 한다.

## ▶ 1단계 · Fork-Join

`Approved`와 `Approved after revision`을 `Final notice` 하나에 연결해 승인된 길을 모은다. 거기서 `Make title`, `Make chat message` 두 Agent로 Fork하고, 각 결과를 `Join editors`의 입력 0·1로 보내 Join한다. 마지막 Code `Combine`이 두 결과를 기존 응답에 붙인다. `Needs person` 경로는 Join에 들어가지 않는다. 두 Agent는 각각 전용 Chat model을 쓴다.

## ▶ 2단계 · 정리자의 하지 않는 일

정리자는 공지의 날짜·시간을 바꾸거나, 검토가 지운 연락처를 되살리거나, 공지에 없는 약속·쿠폰·보상을 만들어 넣지 않는다. `cases/lab02-challenge.json`의 `not_contains`가 쿠폰과 연락처 재등장을 확인한다. 마지막 Code도 연락처 제거, 날짜·시간 포함, 길이 제한을 검사한다. 의미상 새 주장은 이 규칙만으로 완전히 잡을 수 없으므로 실제 게시 때는 사람 확인 또는 추가 의미 검토가 필요하다.

## ▶ 3단계 · 시간 재기 · 정말 동시에 돌았나

정리자 추가 전 `lab02` 보고서의 `seconds`(수업 준비 당시 2.0~4.1초)와 추가 후 `lab02-challenge` 보고서의 값을 비교한다. n8n **Executions**에서 같은 `my-notice` 실행의 `Make title`과 `Make chat message`를 눌러 각각의 시작 시각과 걸린 시간을 `DESIGN.md`에 적는다. 두 시작 시각이 겹쳤는지, 하나가 끝난 뒤 다른 하나가 시작했는지 확인한다. 증가한 시간도 두 정리자의 합에 가까운지 긴 쪽에 가까운지 비교한다. 68일차 교안의 “같은 HTTP 노드의 항목은 함께, 갈래는 차례로” 설명과 실제 기록을 대조한다. 아직 실행 기록이 없어 동시 실행 여부는 단정하지 않는다.
