# 테스트 보고서 · 실행 로그 분석

- 이름: 수강생
- 사용한 CLI 에이전트: agy
- 워크플로우 파일: `my-work/log-report.json`, `my-work/log-summary.json`, `my-work/helpdesk.json`, `my-work/weekly.json`, `my-work/slo-alert.json`

## 1. 통과한 테스트

| 테스트 파일 | 결과 |
| --- | --- |
| `cases/lab01.json` (지표) | Passed 5/5 |
| `cases/lab01-edges.json` (경계, 재기만) | Passed 6/6 |
| `cases/lab01-challenge.json` (날짜별 · 릴리스별) | Passed 6/6 |
| `cases/lab01-challenge2.json` (단계 · 비용) | Passed 5/5 |
| `cases/lab02.json` (실패 묶음 · 답 못 한 주제 · 이상 시간대) | Passed 6/6 |
| `cases/lab02-periods.json` (기간을 바꾸면, 재기만) | Passed 5/5 |
| `cases/lab02-challenge.json` (다시 묻는 주제) | Passed 5/5 |
| `cases/lab02-challenge2.json` (요약 · 숫자 확인) | Passed 3/3 |
| `cases/replay-after.json` (고친 뒤 다시 돌리기) | Passed 10/10 |
| `cases/lab03.json` (고치기 전 · 후) | Passed 4/4 |
| `cases/lab03-slo.json` (SLO) | Passed 4/4 |
| `cases/replay-normal.json` · `lab03-cost.json` (고친 것의 대가, 재기만) | Passed 10/10 · 4/4 |
| `cases/lab03-challenge.json` (주간 보고) | Passed 7/7 |
| `cases/lab03-challenge2.json` (SLO 알림) | Passed 6/6 |

## 2. 실패와 고친 내용

| 실패한 케이스 | 처음 결과 | 내가 생각한 원인 (어느 정의?) | 에이전트가 고친 곳 | 고친 뒤 |
| --- | --- | --- | --- | --- |
| `base-report` vs `lab01` (두 주 602건 vs 666건) | 0/5 실패 (total 602, 월요일 0건) | `started_at < to`로 끝날이 누락되고 `route: null`인 오류 건을 집계에서 제외함 | `started_at <= to` 포함 범위 및 오류 건을 `오류` 갈래로 포함 | 5/5 통과 (666건 정상 집계) |
| `replay-before` (느린 FAQ) | 10건 모두 오류 (`Search FAQ` 타임아웃) | FAQ API 지연(1.2초) 시 기존 1000ms 타임아웃으로 조기 종료됨 | `options.timeout` 3000ms, `retryOnFail: true`, `maxTries: 2` 적용 | `replay-after` 10/10 전건 성공 |
| 와이파이 질문 (답하지 못함) | 와이파이 질문 5건 담당자 연결 | FAQ DB에 와이파이 관련 항목 부재 | `/faq/add` 엔드포인트로 CORP-WIFI 안내 등록 (사람) | 5건 모두 자동 답변 성공 |
| 둘째 주 SLO 위반 알림 연속 호출 | 알림 중복 발송 우려 | 알림 폭주 방지 쿨다운 로직 부재 | `/alerts/list`로 최근 600초 내 동일 알림 확인 후 `suppressed` 처리 | 첫 회 `sent` 후 재호출 시 `suppressed` (6/6 통과) |

## 3. 지표 정의에서 헷갈린 것

- **백분위수(`p50_ms`, `p95_ms`)**: 산술평균이나 단순 보간이 아닌 `ceil(p * n)`번째(1-indexed) 값을 찾는 nearest-rank 정의를 엄격하게 따라야 기대값과 일치함.
- **단계별 시간(`steps`)**: 해당 단계를 실제로 거친 실행(즉, 해당 단계 ms > 0)만 모아서 백분위를 계산해야 왜곡되지 않음. 단계를 거치지 않아 0ms인 건을 포함하면 p50이 비정상적으로 낮아짐.
- **미답변율(`unanswered_rate`)**: 담당자 연결 건은 `status: success`이므로 `failures`에는 포함되지 않으며, `unanswered_rate`로 분리하여 계산해야 함.
- **이상 시간대(`anomalies`)**: 건수 5건 이상, 오류 1건 이상, 그리고 '그 기간 전체 오류율의 3배 이상'이라는 세 가지 조건을 모두 만족해야 함. 기준 기간에 따라 문턱값이 달라짐.

## 4. 아직 숫자로 모르는 것

- **FAQ 검색 API가 느려지는 근본 원인**: `Search FAQ` 노드의 timeout을 3000ms로 늘려 오류는 해결했으나, 응답 시간 p95가 3560ms로 증가하여 SLO(3000ms)를 위반함. 백엔드 데이터 API 또는 인덱싱 성능 저하 원인은 n8n 외부 시스템 로그를 추가 분석해야 함.
- **버전 1.2.0의 높은 재문의율(62.5%)의 실제 원인**: 표본 수가 8건으로 너무 적어 통계적 유의성이 떨어지므로, 추가적인 사용자 피드백 및 질문 내용 정성 분석이 필요함.
