# Routine Scout 개발 규칙

이 파일은 `vibe-flow`의 작업 규칙이다. 상위 [수업 저장소 AGENTS.md](../AGENTS.md)의 자료 동기화 지침도 계속 적용한다. 프로젝트 기준은 [SPEC.md](SPEC.md), 구현 계획은 [TODO.md](TODO.md)다.

## 목적과 MVP

- 테스트용 작업 이벤트 JSON에서 `source + action + target` 패턴을 n8n 내부에서 집계하고, 3회 이상 반복된 패턴을 추천한다.
- 이번 MVP는 로컬 n8n `http://localhost:5678/`의 Webhook 입력과 JSON 응답만 사용한다. 외부 서비스, AI API, Credential, 실제 macOS 사용 행동 수집, 자동화 실행, 캐릭터 기능을 추가하지 않는다.
- 실제 사용자 행동 수집과 앱 기능은 향후 확장으로만 다룬다.

## 파일 역할

| 경로 | 역할 |
| --- | --- |
| `SPEC.md` | 수업 공통 기준과 Routine Scout의 입력·출력 명세 |
| `TODO.md` | 구현 순서와 완료 기준 |
| `n8n/workflows/routine-scout.json` | Routine Scout 워크플로우 정의 |
| `n8n/cases/routine-scout.json` | 수업용 `flow.py test` 호환 구조화 입력·기대 결과 |
| `n8n/cases/malformed-json.http` | JSON 문법 오류를 실제 HTTP로 확인하는 별도 요청 |
| `n8n/cases/TEST-STATUS.md` | 실제 HTTP 관찰과 미검증 항목 기록 |

## 워크플로우와 응답 계약

- `POST /webhook/routine-scout/analyze`의 본문은 `events` 배열이 있는 JSON 객체다. 각 이벤트의 `source`, `action`, `target`은 공백 제거 후 비어 있지 않은 문자열이어야 한다.
- `Webhook → Code → IF(유효성) → IF(추천 여부) → 결과 생성 → Respond to Webhook` 흐름을 유지한다. n8n Code가 검증·집계를 직접 수행하고 IF가 분기한다.
- 모든 패턴을 횟수 내림차순으로 정렬한다. 동률이면 `source`, `action`, `target` 순서로 문자열 오름차순이다. 3회 이상인 패턴은 모두 추천한다.
- 정상 응답은 HTTP 200의 `recommend` 또는 `no_recommendation`이다. JSON 문법이 유효한 요청의 업무 입력 검증 오류는 Code 노드가 HTTP 400의 `error` JSON으로 반환한다. 이 워크플로우 응답에는 `recommendations`와 `patterns`가 있고, 오류에는 `error.code`, `error.field`, `error.message`가 있다.
- `Content-Type: application/json`의 JSON 문법 오류는 n8n의 선행 파서가 Webhook 실행 전에 HTTP 422 오류 JSON으로 반환한다. 관찰된 응답의 핵심 필드는 `code: 422`, `message: "Failed to parse request body"`다. 이 경우 Routine Scout의 `status: "error"` 또는 `error.field: "body"` 구조를 기대하지 않는다. 세부 계약은 `SPEC.md`를 따른다.
- 외부 시스템이나 AI API를 호출하는 노드와 인증 정보는 추가하지 않는다. 입력 원문·비밀값을 오류 메시지에 노출하지 않는다.

## 케이스 작성과 검증

- `n8n/cases/routine-scout.json`은 `{"webhook": "...", "cases": [...]}` 형식을 유지한다. 각 케이스는 `request`와 `expect.status`, `expect.equals`로 요청·HTTP 상태·JSON 결과를 명시한다.
- 3회/2회, 혼합 패턴, 여러 추천, 동률 정렬, 빈 배열, 필드 누락·공백, 잘못된 자료형을 검증한다. 문법 오류는 `flow.py`가 유효한 JSON만 직렬화하므로 별도 `.http` 요청으로 검증한다.
- `flow.py check`는 형식 확인에 사용한다. `flow.py test`는 `/webhook/` 게시 URL을 호출하므로, 미게시 워크플로우의 `/webhook-test/` 테스트에는 그대로 사용하지 않는다. UI에서 Listen for test event를 켜고 각 요청을 보내거나 별도 HTTP 클라이언트로 확인한다.
- HTTP 404와 Webhook 미등록 메시지는 입력 검증 실패가 아니라 **테스트 Webhook 등록/대기 상태 문제**로 기록한다. 실제 응답을 확인하지 않은 케이스는 통과로 표시하지 않는다.

## 기존 워크플로우와 게시 보호

- 기존 워크플로우의 ID·상태·내용 및 Webhook을 변경하거나 삭제하지 않는다. 게시 전 경로 중복을 읽기 전용으로 확인한다.
- `flow.py push`는 같은 경로의 기존 워크플로우를 비활성화하고 n8n 컨테이너를 재시작할 수 있다. **사용자의 명시적 승인 없이 실행하지 않는다.** 다른 게시 방식도 기존 워크플로우에 미치는 영향을 확인한 뒤 진행한다.
- Git 커밋과 Git push는 사용자의 명시적 요청이 있을 때만 수행한다.
