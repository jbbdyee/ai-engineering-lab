# Routine Scout HTTP 테스트 상태

기록 기준: 사용자가 터미널에서 직접 확인한 HTTP 결과와 `http-results.jsonl`의 HTTP 통합 테스트 기록. 이번 문서 수정에서는 n8n에 새 요청을 보내지 않았다. [routine-scout.json](routine-scout.json)의 `expect`는 **기대 결과**이며 실제 관찰 결과와 구분한다. 구조화 케이스 14개 중 **5개 통과, 9개 미검증**이다. JSON 문법 오류 1개는 관찰됐으며 아래에 최초 계약과 변경 후 재평가를 구분한다.

| 케이스 | 관찰된 HTTP 상태 | 관찰된 응답 | 판정 |
| --- | --- | --- | --- |
| 동일 작업 3회 | 200 | `status: recommend`, `repeat_count: 3`, 추천 1개 | 통과 |
| 동일 작업 2회 | 200 | `status: no_recommendation`, `recommendations: []`, `repeat_count: 2` | 통과 |
| 서로 다른 작업 혼합 | 200 | `status: recommend`, 추천 1개; 패턴 횟수 3·1·1 (`http-results.jsonl`) | 통과 |
| 여러 추천과 동률 정렬 | 200 | `status: recommend`, 추천 3개; 패턴 순서 browser 4회 → alpha 3회 → beta 3회 (`http-results.jsonl`) | 통과 |
| events 필드 누락 | 400 | `status: error`, `error.code: INVALID_INPUT`, `error.field: events`, `error.message: 이벤트 배열이 필요합니다.` | 통과 |
| 그 밖의 구조화 케이스 9개 (5~12, 14번) | 미실행 | 없음 | 미검증 |
| JSON 문법 오류 (`{"events": [}`) | 422 | `code: 422`, `message: Failed to parse request body`; n8n이 Webhook 실행 전에 반환(사용자 보고) | 변경 후 계약에 부합(기존 관찰값 재평가, 새 요청 없음) |

이전에 동일 작업 2회와 `events` 누락에서 관찰된 HTTP 404는 **테스트 Webhook 미등록** 때문에 발생했다. 이후 두 요청을 재실행해 위의 HTTP 200 및 400 응답을 확인했다. 과거의 404는 입력 검증 실패가 아니다. 남은 케이스는 n8n UI에서 **Listen for test event**를 켠 뒤 표시된 `/webhook-test/routine-scout/analyze` 주소로 보내고, HTTP 상태와 JSON 전체를 기대값과 비교한다. 테스트 리스너는 한 요청을 받은 뒤 다시 대기시켜야 할 수 있다.

수업용 `flow.py test`는 `/webhook/` 게시 URL을 호출하므로 미게시 상태의 Test URL 검증에는 직접 사용하지 않는다. JSON 문법 오류는 [malformed-json.http](malformed-json.http)의 원문 요청으로 별도 확인한다.

## JSON 문법 오류 계약 변경 이력

- **최초 기대값:** HTTP 400, Routine Scout 오류 JSON(`status: "error"`, `error.field: "body"`). 실제 HTTP 422 및 n8n 자체 오류 JSON과 **불일치**했다.
- **관찰 결과:** 사용자가 `{"events": [}`을 보냈을 때 HTTP 422, `code: 422`, `message: "Failed to parse request body"`를 확인했다. n8n의 선행 파서가 Webhook 워크플로우 실행 전에 반환했으므로 Routine Scout의 `status: "error"`와 `error.field: "body"`가 없다.
- **변경 후 재평가:** `SPEC.md`, `AGENTS.md`, `malformed-json.http`의 JSON 문법 오류 계약을 HTTP 422 및 n8n 자체 오류 JSON으로 맞췄다. 기존 관찰값은 이 변경된 계약에 **부합**한다. 이는 과거 응답의 재평가이며 새 HTTP 테스트 통과로 집계하지 않는다.
