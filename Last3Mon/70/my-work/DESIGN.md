# 재사용 설계서 · 공지 키트와 규칙 검사 모듈

- 이름:
- 사용한 CLI 에이전트: codex

## 1. 복사본 비교 (Lab 01 예제 1)

| 노드 | 세 파일에서 같은가 | 다른 것 (점검 · 보안 · 교육) | 어디로 (모듈 · 설정 표 · 그대로) |
| --- | --- | --- | --- |
| Notice webhook | 경로만 다름 | `sample-maintenance` · `sample-security` · `sample-training` | 그대로 (공지 키트의 단일 웹훅으로 통합) |
| Has facts? | 같음 | 없음. 세 파일 모두 `body.facts`가 비었는지 검사 | 그대로 |
| Reject empty | 같음 | 없음. 모두 400과 `facts are required` 반환 | 그대로 |
| Writer agent | 작성 구조는 같고 지시가 다름 | `[점검 안내]`와 이용 불가·작업 후 조치 · `[보안 안내]`와 비밀번호 금지 문장·행동 지침 · `[교육 안내]`와 신청 문장·대상·일시·장소 | 설정 표 (머리말·필수 문장·주의를 한곳에 두고 작성 지시에 전달) |
| OpenAI chat model | 같음 | 없음. 모두 `gpt-4.1-mini`, temperature 0, 같은 Credential 사용 | 그대로 |
| Build draft | 같음 | 없음. 모두 작성 결과의 공백·코드 펜스를 제거 | 그대로 |
| Rule checks | 검사 코드는 같고 설정값이 다름 | 최대 600자·필수 문장 없음 · 최대 500자·`IT팀은 절대 비밀번호를 묻지 않습니다.` · 최대 800자·`신청은 IT 포털에서 할 수 있습니다.` | 모듈 (검사 코드) · 설정 표 (최대 길이·필수 문장) |
| Build result | `kind`만 다름 | `maintenance` · `security` · `training`; 나머지 결과 필드와 게시 판정은 같음 | 설정 표 (`kind`) · 나머지는 그대로 |
| Send result | 같음 | 없음. 모두 `{kind, route, published, notice, codes}`를 JSON으로 반환 | 그대로 |

- 보안 공지의 필수 문장을 고치려면 지금은 2곳(`Writer agent`의 지시와 `Rule checks`의 필수 문장)을 고쳐야 한다.

### 예제 1 · 1단계: 노드 단위 비교

위 표는 위치와 노드 식별자 대신 업무에 영향을 주는 웹훅 경로, 작성 지시, 검사 한도·필수 문장, 결과의 `kind`를 비교한다. 세 파일의 연결 순서와 입력·출력 계약은 같다.

### 예제 1 · 2단계: 차이 분류

| 분류 | 해당 값 | 처리 |
| --- | --- | --- |
| 종류별 설정 | 머리말, 최대 길이, 필수 문장, 작성 주의, `kind` | `Kind settings` 한 곳에 둔다 |
| 같아야 하는 값인데 우연히 다른 것 | 발견되지 않음 | 공통 노드의 동작을 유지한다 |
| 실제로 다른 흐름 | 웹훅 경로만 다르고 처리 흐름은 같음 | 하나의 `my-notice-kit` 웹훅으로 통합한다 |

## 2. 설정 표 (Lab 01 예제 2 · 과제)

| kind | 머리말 | 최대 길이 | 꼭 넣을 문장 | 주의 |
| --- | --- | --- | --- | --- |
| maintenance | `[점검 안내]` | 600 | 없음 | 점검 중 사용할 수 없는 서비스와 점검 후 할 일을 분명히 쓴다 |
| security | `[보안 안내]` | 500 | `IT팀은 절대 비밀번호를 묻지 않습니다.` | 할 일과 하지 말아야 할 일을 쓰고 비밀번호를 요구하지 않는다 |
| training | `[교육 안내]` | 800 | `신청은 IT 포털에서 할 수 있습니다.` | 참석 대상, 일시, 장소, 신청 방법을 쓴다 |
| survey | `[설문 안내]` | 500 | `응답은 익명으로 처리됩니다.` | 설문 목적, 기한, 소요 시간을 쓴다 |

- 새 종류를 더할 때 고친 노드: `Kind settings` 한 곳. 없는 종류를 거르는 분기는 `Known kind?`와 `Reject unknown kind`를 추가했다.

### 예제 2 · 1단계: 바탕 선택

세 복사본의 공통 흐름을 바탕으로 `my-work/notice-kit.json` 하나를 만들었다. 웹훅을 `my-notice-kit`로 바꾸고 `kind`와 `facts`를 필수로 확인한다. 종류별 값은 `Kind settings`로 옮겼다.

### 예제 2 · 2단계: 설정 표 사용

`Kind settings`의 한 행에는 `label`, `prefix`, `max_length`, `required_phrases`, `extra`를 둔다. `Writer agent`는 머리말·필수 문장·주의를 읽고, 규칙 검사 모듈에는 같은 행의 최대 길이·필수 문장을 넘긴다. `Build result`도 그 행의 `kind`를 사용한다.

### 예제 2 · 3단계: 점검표

- [x] `my-work/notice-kit.json`의 POST 웹훅과 필수 입력 `kind`, `facts`
- [x] 설정 표의 네 칸과 점검·보안·교육 세 종류
- [x] 작성 지시와 규칙 검사가 같은 설정 표를 읽음
- [x] 결과 필드 `kind`, `route`, `published`, `notice`, `codes`
- [ ] `cases/lab01.json` 실행: 지침에 따라 사람이 push·test 후 확인

### 과제 · 1단계: 새 종류를 표 한 줄로

`Kind settings`의 `KINDS`에 `survey` 한 행을 추가했다. 머리말 `[설문 안내]`, 최대 500자, 필수 문장 `응답은 익명으로 처리됩니다.`를 그 행에만 적었다. `Writer agent`, `Rule checks`, `Build result`는 표를 읽으므로 설문을 위해 수정하지 않았다.

### 과제 · 2단계: 없는 종류를 400으로 거절

기존 흐름에서 `kind: party`는 설정값이 없는 채로 작성 단계에 넘어갈 수 있었다. 이제 `Kind settings`가 표의 키로 `known`과 `kinds`를 만들고, 바로 다음 `Known kind?`가 확인한다. 없는 종류는 `Reject unknown kind`가 `{"error":"unknown kind","kinds":["maintenance","security","training","survey"]}`와 HTTP 400을 반환한다. 종류 목록은 표에서 자동 생성하므로 종류를 더할 때 따로 고치지 않는다.

### 과제 · 확인

- [x] 설문 종류의 설정값은 `Kind settings` 한 곳에만 추가
- [x] 없는 종류는 작성 전에 멈추고 표에서 만든 `kinds`를 400 응답에 포함
- [x] 점검·보안·교육 기존 경로와 결과 계약 유지
- [ ] `cases/lab01-challenge.json`과 `cases/lab01.json`: 지침에 따라 사람이 push·test 후 확인

## 3. 모듈 계약 (Lab 02)

| 모듈 | id | 입력 (이름 · 종류) | 결과 | 쓰는 곳 |
| --- | --- | --- | --- | --- |
| 규칙 검사 v1.1 | `modRuleCheck01` | `facts` · string, `draft` · string, `max_length` · number, `required_phrases` · array, `allowed_domains` · array(선택) | `passed` · boolean, `codes` · array, `issues` · array | `rule-check-test.json`, `sms.json` |
| 규칙 검사 v2 | `modRuleCheck02` | v1.1과 같음 | `passed` · boolean, `blocking` · array, `warnings` · array, `issues` · array, `version` · number | `rule-check-v2-test.json`, `notice-kit.json` |

### 예제 1 · 1단계: 모듈 입력

기존 키트의 `Rule checks`는 웹훅 본문의 `facts`, 앞 노드의 `draft`, 설정 표의 `max_length`와 `required_phrases`를 읽는다. 모듈은 호출자의 노드를 직접 참조하지 않으므로 이 네 값을 위 계약의 입력으로 받는다. 검사 코드는 날짜·시간 누락(`missing_fact`), 전화번호·메일 주소(`personal_info`), 길이 초과(`too_long`), 필수 문장 누락(`missing_phrase`)을 판정한다.

### 예제 1 · 2단계: 시험용 웹훅

`rule-check.json`은 웹훅이 없는 Sub-workflow라 `call`이나 `test`의 대상이 될 수 없다. `rule-check-test.json`은 `Test webhook` → `Rule check module` → `Send result`의 세 노드로 본문 네 값을 전달하고 모듈 결과를 그대로 반환한다. 두 파일을 함께 push한 뒤 `cases/lab02-module.json`으로 모듈을 따로 시험한다.

### 예제 1 · 3단계: 고정 id

모듈 파일에 `"id": "modRuleCheck01"`을 직접 넣었고 시험용 웹훅의 `workflowId.value`도 `modRuleCheck01`로 지정했다.

### 예제 1 · 확인

- [x] 모듈 입력 4개의 이름과 종류, 결과 3개 필드를 고정
- [x] 시험용 웹훅이 같은 id의 모듈을 호출
- [ ] 현재 v1.1 파일로 `cases/lab02-module.json` 재실행: 지침에 따라 사람이 push·test 후 확인

### 예제 2 · 공지 키트에서 모듈 사용

키트의 내부 `Rule checks`를 `Rule check module` 호출로 바꿨다. `facts`는 웹훅, `draft`는 `Build draft`, `max_length`와 `required_phrases`는 `Kind settings`에서 가져온다. 최종 키트는 v2의 `modRuleCheck02`를 호출하고, 기존 `codes` 필드도 유지한다.

### 과제 · SMS에서도 모듈 사용

`sms.json`은 같은 v1 계열 `modRuleCheck01`에 최대 길이 80, 필수 문장 빈 목록을 넘긴다. SMS 때문에 모듈 내부의 검사 기준을 고치지 않았다.

## 4. 바꿀 때 (Lab 03)

| 바꾼 것 | 하위 호환인가 | 같은 id · 새 id | 다시 돌린 테스트 | 결과 |
| --- | --- | --- | --- | --- |
| 바깥 링크 검사 (`allowed_domains`) | 예. 기존 네 입력과 `{passed,codes,issues}` 유지, 선택 입력 추가 | 같은 id `modRuleCheck01` (v1.1) | `cases/lab03.json`, `cases/lab02-module.json`, `cases/lab02-challenge.json` | 구현·정적 검사 완료, 현재 파일의 실행 테스트 대기 |
| 심각도 (`blocking` · `warnings`) | 아니요. 결과 필드와 `too_long`의 게시 판정이 달라짐 | 새 id `modRuleCheck02` (v2) | `cases/lab03-v2.json`, `cases/lab01.json`, `cases/lab01-challenge.json` | 구현·정적 검사 완료, 현재 파일의 실행 테스트 대기 |

## 5. 영향 표 (Lab 03 과제)

| 모듈 · 버전 | 쓰는 워크플로우 | 그 워크플로우의 테스트 |
| --- | --- | --- |
| `modRuleCheck01` · v1.1 | 시험용 웹훅, SMS | `cases/lab03.json`, `cases/lab02-module.json`, `cases/lab02-challenge.json` |
| `modRuleCheck02` · v2 | v2 시험용 웹훅, 공지 키트 | `cases/lab03-v2.json`, `cases/lab01.json`, `cases/lab01-challenge.json`, `my-work/cases/my-cases.json` |

### 최종 키트 · 어려운 케이스

`Has kind and facts?`는 공백만 있는 `facts`를 거절한다. `Kind settings`는 `kind`의 앞뒤 공백을 지우고 소문자로 바꾼 뒤 점검·보안·교육·설문의 한국어 별칭을 표의 키로 바꾼다. 없는 종류는 작성 전에 400과 표의 키 목록을 반환한다. `Build result`는 v2의 `blocking`과 `warnings`를 반환하면서 기존 `codes`를 유지한다. 실행 검증 대상은 `my-work/cases/my-cases.json`의 7개 케이스다.
