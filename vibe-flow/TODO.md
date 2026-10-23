# Routine Scout — n8n 워크플로우 구현 TODO

## 1. 프로젝트 개요 및 목표

Routine Scout는 작업 이벤트 목록에서 반복 패턴을 찾아 자동화 후보를 추천하는 n8n 워크플로우다. 테스트용 JSON을 Webhook으로 받으면 n8n이 직접 입력 검증, 패턴 집계, 추천 판단을 수행하고 JSON으로 응답한다. [SPEC.md](SPEC.md)의 수업 기준인 **Trigger → Condition → Action → Response**, 입력·출력 계약, 빈 입력과 실패 경로 검증을 따른다. 수업 사례는 운영 배포를 뜻하지 않으며 개인 실습의 전체 이력은 이 저장소만으로 확인할 수 없다.

## 2. 이번 MVP의 구현 범위

- 로컬 n8n 서버 `http://localhost:5678/`에서 `POST /webhook/routine-scout/analyze`를 처리한다.
- Webhook 입력과 JSON 출력만 사용한다. 외부 시스템, 외부 계정, LLM/Agent 및 macOS 앱은 연결하지 않는다.
- `source + action + target` 조합을 각각 집계하고 3회 이상 반복된 패턴을 모두 추천한다.
- 워크플로우 JSON, `push.sh`, 배포 및 실행은 다음 구현 단계의 작업이다.

## 3. 입력 및 출력 JSON 스키마

요청 본문은 JSON 객체이고 `events`는 배열이다. 각 이벤트는 `source`, `action`, `target`을 필수로 가진 객체다. 세 필드는 앞뒤 공백을 제거한 후에도 비어 있지 않은 문자열이어야 한다. 대소문자를 구별하고 추가 필드는 분석에서 무시한다. 빈 배열은 유효하다. 객체가 아닌 본문, 누락되거나 배열이 아닌 `events`, 객체가 아닌 이벤트, 누락·공백·문자열 외 자료형의 필드는 오류다. 오류가 하나라도 있으면 전체 요청을 거절한다.

요청 예시:

```json
{
  "events": [
    {"source": "codex", "action": "copy", "target": "chatgpt"},
    {"source": "codex", "action": "copy", "target": "chatgpt"},
    {"source": "codex", "action": "copy", "target": "chatgpt"}
  ]
}
```

정상 응답은 `status`, `recommendations`, `patterns`를 가진다. `patterns`에는 모든 패턴과 횟수를 담는다. 추천이 있으면 `status`는 `recommend`이고 추천 조건을 충족한 패턴만 `recommendations`에 담는다.

```json
{
  "status": "recommend",
  "recommendations": [
    {
      "source": "codex",
      "action": "copy",
      "target": "chatgpt",
      "repeat_count": 3,
      "suggestion": "codex에서 chatgpt로 copy하는 반복 작업의 자동화를 추천합니다."
    }
  ],
  "patterns": [
    {"source": "codex", "action": "copy", "target": "chatgpt", "repeat_count": 3}
  ]
}
```

추천할 패턴이 없으면 HTTP 200으로 같은 키를 반환한다. 아래는 빈 이벤트 배열의 결과다. 1~2회 패턴이 있으면 `patterns`에 그 횟수를 담는다.

```json
{"status": "no_recommendation", "recommendations": [], "patterns": []}
```

JSON 문법이 유효하지만 필수 필드가 누락되거나 자료형이 잘못된 업무 입력 오류는 Routine Scout가 HTTP 400과 아래 JSON을 반환한다. `field`는 문제 위치를 나타내며, 배열 안의 오류는 `events[0].source`처럼 표시한다. 원본 입력값은 오류 메시지에 넣지 않는다.

```json
{
  "status": "error",
  "recommendations": [],
  "patterns": [],
  "error": {"code": "INVALID_INPUT", "field": "events[0].source", "message": "필수 문자열 필드가 필요합니다."}
}
```

`Content-Type: application/json`의 JSON 문법 오류는 n8n의 선행 파서가 Webhook 실행 전에 거절한다. 로컬 n8n 2.42.6에서 `{"events": [}`에 대해 확인한 응답은 HTTP 422와 `code: 422`, `message: "Failed to parse request body"`를 포함한 n8n 자체 오류 JSON이다. 이 경우 Routine Scout의 `status: "error"`나 `error.field: "body"` 구조는 반환되지 않는다.

## 4. 반복 패턴 분석 기준

1. 전체 입력을 검증하고 세 필드의 앞뒤 공백을 제거한다. 세 값이 모두 같은 이벤트를 같은 패턴으로 본다. 구분자가 포함된 문자열도 섞이지 않도록 튜플 또는 충돌 없는 키로 집계한다.
2. 패턴별 `repeat_count`를 계산한다. 3회 이상인 모든 패턴을 추천하고, 1~2회 패턴은 `patterns`에만 담는다.
3. `patterns`와 `recommendations`를 횟수 내림차순으로 정렬한다. 동률이면 `source`, `action`, `target` 순서로 문자열 오름차순 정렬한다.
4. 추천 문구는 세 필드를 사용하는 고정 템플릿으로 만든다. 외부 AI 서비스를 사용하지 않는다.

## 5. n8n 노드 구성과 데이터 흐름

| 순서 | 노드 | 역할 |
| --- | --- | --- |
| 1 | Webhook | `POST /routine-scout/analyze` JSON 수신, 응답 방식을 Respond to Webhook으로 설정 |
| 2 | Code | 전체 입력 검증, 정규화, 패턴 집계·정렬, 추천 후보 생성; 오류도 단일 item으로 전달 |
| 3 | IF: 입력 유효성 | 오류 경로와 정상 경로 분리 |
| 4 | IF: 추천 여부 | 정상 경로에서 추천 후보가 하나 이상인지 판단 |
| 5 | 결과 생성 노드 | 추천, 추천 없음, 입력 오류의 JSON과 HTTP 상태 구성; Edit Fields(Set) 또는 Code 사용 |
| 6 | Respond to Webhook | 각 실행 경로의 단일 최종 JSON 반환 |

Code 노드가 실제 집계를 수행하고 IF 노드가 추천 여부를 판단한다. JSON 문법 오류는 n8n이 Code 노드 실행 전에 HTTP 422 자체 오류 JSON으로 처리하므로 Routine Scout 노드의 분기에는 들어오지 않는다.

## 6. 조건 분기 및 예외 처리

- **업무 입력 오류:** 문법이 유효한 JSON의 모든 이벤트를 검증한다. 첫 오류의 위치와 고정 메시지를 Routine Scout의 HTTP 400 JSON으로 반환하며 부분 결과는 반환하지 않는다.
- **JSON 문법 오류:** n8n의 선행 파서가 HTTP 422 자체 오류 JSON을 반환한다. Routine Scout의 응답 필드는 적용되지 않는다.
- **추천 있음:** 3회 이상인 패턴이 하나라도 있으면 HTTP 200 `recommend`; 해당 패턴을 모두 포함한다.
- **추천 없음:** 모든 패턴이 2회 이하이거나 `events`가 빈 배열이면 HTTP 200 `no_recommendation`이다.
- **실행 오류:** 예상치 못한 노드 실패를 JSON으로 반환할 경로를 검토한다. 내부 정보와 입력 원문은 노출하지 않는다.

## 7. 단계별 구현 체크리스트

- [ ] 수업용 n8n과 `flow.py` 위치 및 실행 환경을 확인하고 Webhook 경로 중복 여부를 확인한다.
- [ ] 요청·응답 계약, 추천 문구와 테스트용 요청·케이스를 확정한다.
- [ ] CLI 코딩 에이전트로 n8n 워크플로우 JSON을 생성한다.
- [ ] Code 노드에 전체 입력 검증, 충돌 없는 집계와 안정적인 정렬을 구현한다.
- [ ] IF와 결과 생성 노드에 추천, 추천 없음, 오류 경로를 구현하고 각 경로에서 JSON과 HTTP 상태를 반환한다.
- [ ] `flow.py check`로 노드 유형·버전·연결·Credential 참조와 민감정보 노출을 확인한다.
- [ ] 기존 수업 환경의 게시 절차에 맞춰 `push.sh`를 **구현 단계에** 작성한다. 실행 전 로컬 서버, 워크플로우 파일과 인증정보 취급을 확인한다.
- [ ] 로컬 n8n에 게시한 뒤 `flow.py call`과 `flow.py test`로 정상·오류 시나리오와 실행 경로를 검증한다.

## 8. 테스트 시나리오 및 완료 기준

| 시나리오 | 기대 결과 |
| --- | --- |
| 동일 작업 3회 | `recommend`, 해당 패턴 `repeat_count: 3` |
| 동일 작업 2회 | `no_recommendation`, `patterns`에 `repeat_count: 2` |
| 서로 다른 작업이 섞임 | 조합별 독립 집계, 3회 이상인 것만 추천 |
| 여러 패턴이 동시에 추천 기준 충족 | 모두 추천, 횟수 내림차순 및 동률 시 세 필드 오름차순 |
| 빈 이벤트 배열 | HTTP 200, `no_recommendation`, 두 배열 모두 빈 값 |
| 필수 필드 누락 또는 공백 문자열 | HTTP 400, `INVALID_INPUT`과 해당 `field` |
| 잘못된 입력 자료형 | HTTP 400, 배열·이벤트·필드의 자료형 오류 표시 |
| 잘못된 JSON 본문 | HTTP 422, n8n 자체 오류 JSON의 `code: 422` 및 `message: "Failed to parse request body"` |

**완료 기준:** 수업 도구의 형식 검사와 테스트를 통과하고 로컬 n8n에서 위 응답과 분기 경로를 확인한다. 정상 응답·업무 입력 오류·JSON 문법 오류가 각각 위 JSON 계약에 맞으며, 외부 시스템 호출이나 Credential 없이 n8n 내부에서 집계와 추천 판단을 수행한다. JSON 문법 오류는 워크플로우 실행 전 n8n 선행 파서의 응답으로 별도 확인한다.

## 9. 워크플로우 JSON 생성·검증·로컬 n8n 배포 계획

수업 방식대로 요구사항을 바탕으로 CLI 코딩 에이전트가 워크플로우 JSON과 테스트 케이스를 작성한다. 기존 `../Last3Mon/66/tools/flow.py` 및 `../Last3Mon/70/tools/flow.py`의 사용법과 현재 환경의 호환성을 확인한 후 `doctor → check → push → call → test` 순서로 검증한다. `check`는 노드·연결·Credential 및 비밀값 노출을 검사하고, `call`·`test`는 응답값과 분기 경로를 확인한다. 필요하면 반복 실행으로 정렬 결과의 안정성을 확인한다.

구현 단계의 `push.sh`는 검증된 JSON을 **로컬 n8n `http://localhost:5678/`에 게시하는 절차**를 담는다. 실행 전 대상 서버, 파일 경로와 사용 명령을 확인한다. 여기서 `flow.py push`와 `push.sh`의 push는 n8n 게시를 뜻하며 GitHub push와 구별한다. 이번 문서 수정 단계에서는 JSON 생성, 스크립트 작성·실행 및 n8n 게시를 수행하지 않는다.

## 10. 향후 확장 계획

- macOS 앱으로 실제 작업 이벤트를 사용자 동의 범위에서 수집하고 내용 없는 최소 메타데이터를 전달한다.
- 추천을 사용자가 검토·승인한 후 자동화를 등록하거나 실행한다.
- 추천 상태를 표현하는 오리지널 캐릭터 UI를 추가한다.

이 기능들은 이번 n8n 단독 MVP의 범위 밖이다. 실제 수집 가능성, 권한 및 데이터 보관 기준은 별도로 검증한다.
