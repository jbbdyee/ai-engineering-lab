# 문의 일괄 접수 장애 대응 런북

이 문서는 Lab 01~03의 강사용 실습 결과를 바탕으로 작성했다. 아래 수치는 이 환경에서 새로 실행해 확인한 값이 아니다.

## 1. 실패의 종류

| 상황 | 확인할 신호 | 자동 처리 | 사람이 할 일 |
| --- | --- | --- | --- |
| 필수값 누락·요청 안의 중복 ID·10건 초과 | `rejected` 또는 HTTP 400과 이유 | 잘못된 항목 또는 요청 거절 | 입력을 고쳐 다시 요청 |
| 접수 API의 일시 실패 | 응답의 `created` | 최대 3회 시도, 요청 ID를 멱등 키로 사용 | 접수 건 수와 중복 여부 확인 |
| 접수 API의 지속 실패·시간 초과 | `failed`, DLQ, `high · dlq` | 실패 항목을 DLQ에 저장 | 원인 복구 뒤 재처리 |
| DLQ 저장 실패 | `dlq_saved: false`, `critical · dlq_down` | 잃을 뻔한 ID를 알림에 기록 | ID와 원래 요청을 즉시 확보하고 수동 복구 계획 수립 |
| 분류 실패 | `unclassified` | `미분류`·`보통`으로 접수 | 분류 복구 후 해당 건 확인 |
| 처리하지 못한 워크플로우 오류 | `critical · unexpected` | Error Workflow가 노드·오류·실행 ID를 알림 | n8n 실행 기록 확인 후 코드 담당에게 전달 |
| 재처리 시도 한도 도달 | `high · parked`, DLQ의 `parked` | 자동 재처리에서 제외, DLQ에 보존 | 원인과 요청을 검토해 수동 처리 결정 |

시간 초과는 접수 실패가 확정되었다는 뜻이 아니다. API가 나중에 접수 건을 만들 수 있으므로 재처리 전후에 같은 `key`로 중복 접수 건이 없는지 확인한다. Lab 01 강사용 결과에서 `slow` 요청은 실패로 응답했지만 약 8초 뒤 접수 건이 만들어졌다.

## 2. 알림을 받으면

1. `uv run tools/flow.py ops`로 고장 스위치, DLQ, 알림, 접수 건을 확인한다. 운영 상태 웹훅은 `curl -s -X POST http://localhost:5678/webhook/my-ops-status -H 'Content-Type: application/json' -d '{}'`로 조회한다.
2. 알림을 원인별로 나눈다. `high · dlq`는 데이터 API 복구 후 재처리한다. `critical · unexpected`는 알림의 `workflow`, `node`, `message`, `execution_id`로 n8n Executions에서 실행을 열고 코드 담당자에게 전달한다. `critical · dlq_down`은 알림의 lost IDs와 원래 요청을 우선 확보한다.
3. 데이터 API 담당자에게 복구를 확인한다. 실습에서는 사람이 `uv run tools/flow.py fault tickets ok`를 실행한 뒤 `ops`에서 fault switch가 정상인지 확인한다. `/health`만으로는 고장 스위치 상태를 알 수 없다.
4. `curl -s -X POST http://localhost:5678/webhook/my-replay -H 'Content-Type: application/json' -d '{}'`로 재처리한다. 응답의 `replayed`, `ok`, `still_failed`, `parked`, `duplicates`를 기록한다. `still_failed`가 있으면 원인을 다시 확인한다.
5. `ops`에서 DLQ의 미보류 건이 0인지, 접수 건이 성공한 만큼 반영되었는지, 같은 요청 ID의 접수 건이 중복 생성되지 않았는지 확인한다. parked 건은 별도로 검토한다. `critical · unexpected` 알림은 재처리 후에도 남을 수 있다.

**하지 말 것:** 재처리 전에 `/dlq-clear` 또는 `ops --reset`으로 요청을 지우지 않는다. parked 건을 자동으로 반복 실행하지 않는다. `nightly-report`의 알려진 버그를 이 절차 중 임의로 수정·배포하지 않는다.

## 3. 장애 연습 기록 기준

Lab 03 강사용 실행 결과: 장애 시작 시 접수 API 오류로 2건이 DLQ에 남고, `nightly-report`는 500을 반환했다. `high · dlq`와 `critical · unexpected`를 구분한 뒤 접수 API를 복구하고 재처리하여 `ok: 2`, DLQ 0, 접수 건 2를 확인했다. critical 알림은 남았다. 이 환경의 실습 결과는 `cases/lab03-drill.json` 실행 후 여기에 별도로 기록한다.

## 4. 책임

| 역할 | 할 일 |
| --- | --- |
| 1차 대응자 | 알림 분류, DLQ와 원래 요청 보존, 재처리 결과 기록 |
| 데이터 API 담당자 | 접수 API·DLQ 서비스 복구와 고장 스위치 확인 |
| 워크플로우 담당자 | `unexpected` 실행 조사, 수정·배포 절차 진행 |
| parked 건 담당자 | 요청별 원인 확인 후 수동 재처리 또는 종결 결정 |

구체적인 담당자와 연락처는 운영 팀이 지정한다.
