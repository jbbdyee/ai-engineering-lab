# 시험 · 결과 검증 (워크플로우 실행 결과서를 쓰기 위해)

원본 요구 4단계: "정상 요청과 예외 상황을 포함한 주요 시나리오를 실행하고, 입력 · 기대 결과 · 실제 결과 · 실행 노드 · 처리시간 · 판정을 기록하고, 실패는 원인과 조치를 기록해 같은 조건으로 다시 시험합니다." 이것을 64~79일차의 `flow.py test`로 합니다.

## 1. 시나리오 파일

공통 시나리오는 기본 주제면 실습 키트 `Last3Mon/80/cases/common.json`, 다른 주제면 질문을 옮긴 팀 저장소 `cases/common.json` ([11-TOPIC-GUIDE](11-TOPIC-GUIDE.md) 4절). 팀 시나리오는 팀 저장소 `cases/team.json`. 모양은 72 · 73일차와 같습니다.

```json
{
  "webhook": "team1-support",
  "before": [{"url": "http://localhost:8800/tickets-reset", "body": {}}],
  "cases": [
    {"name": "WF-01 정상 문의",
     "body": {"request_id": "wf01", "user": "박서연", "question": "VPN이 계속 끊겨요. 어떻게 해야 하나요?"},
     "expect": {"equals": {"route": "자동 답변"}, "contains": {"sources": ["remote-work-vpn"]}, "max_seconds": 8}},
    {"name": "WF-04 티켓 API 장애",
     "before": [{"url": "http://localhost:8800/admin/fault", "body": {"tickets": "error"}}],
     "after": [{"url": "http://localhost:8800/admin/fault", "body": {"tickets": "ok"}}],
     "body": {"request_id": "wf04", "user": "한지훈", "question": "사내 식당 앱이 열리지 않아요"},
     "expect": {"equals": {"route": "담당자 이관", "ticket": null}}}
  ]
}
```

- `--webhook <팀>-support`로 공통 시나리오의 웹훅을 우리 팀 것으로 바꿉니다.
- 판정 칸: `equals` · `contains` · `not_contains` · `status` · `max_seconds` (점으로 내려감: `security.masked`).
- `before` · `after`: 고장 켜기 · 끄기, 비우기. `after`는 실패해도 돌아갑니다.
- **기대 결과를 먼저 쓰고**, 결과에 맞춰 기대를 고치지 않습니다 (73일차).

## 2. 돌리는 순서

```bash
cd ~/aio-01d4-stu/Last3Mon/80
export FLOW_WEBHOOK_KEY=<팀 키>                                                        # Header Auth를 걸었다면
uv run tools/flow.py test cases/common.json --webhook team1-support -v                 # 공통 (한 번)
uv run tools/flow.py test cases/common.json --webhook team1-support --repeat 3         # LLM이 들어간 것 반복
uv run tools/flow.py test ~/team1/cases/team.json -v                                   # 팀 시나리오
uv run tools/flow.py bench team1-support requests/wf01.json -n 5                       # 처리시간 p50 · p95
uv run tools/flow.py ops                                                               # 만든 티켓 · DLQ · 알림
```

- 보고서는 `runs/*.json`에 남습니다 (케이스마다 요청 · 응답 · 문제 · 시간). **이 파일이 결과서의 증거**입니다. 팀 저장소 `runs/`로 복사합니다.
- 고장 시나리오는 하나씩 돌리고, 끝나면 `flow.py fault all ok` · `flow.py llm up`을 확인합니다 (다른 팀원과 같은 노트북이면 특히).

## 3. 언제 무엇을

| 언제 | 무엇을 | 왜 |
| --- | --- | --- |
| 80일차 골격 직후 | 공통 시나리오 한 번 | 출발점 (몇 개가 그냥 통과하나) |
| 기능 하나를 붙일 때마다 | 그 기능의 시나리오 + 공통 전부 | 회귀 (새 기능이 앞의 것을 깨지 않았나) |
| 81일차 중간 점검 | 공통 + 장애 | 통과 수를 숫자로 |
| 82일차 동결 뒤 | 전부 + LLM 3회 반복 + `bench` | 결과서의 최종 숫자 |

## 4. 결과서 숫자 (원본 결과서 3절 "결과 요약")

| 칸 | 어디서 |
| --- | --- |
| 전체 시나리오 · 성공 / 실패 | `runs/*.json`의 통과 수 (공통 + 팀) |
| 자동 답변 / 담당자 이관 | 응답 `route`를 셈 |
| 평균 처리시간 | `bench`의 p50 · p95 (평균보다 p50 · p95, 72일차) 또는 케이스 시간 |
| 예외 처리 성공률 | 장애 · 예외 시나리오 중 기대대로 처리된 비율 |
| 근거 없는 답변 | `자동 답변`인데 `sources`가 비었거나 검증 실패인 수 (0이어야 함) |
| 권한 위반 | 권한 없는 문서 · 남의 건이 답에 나온 수 (0이어야 함) |
| (권장) 요청당 LLM 호출 수 | 실행 기록 `llm_calls` (비용 설명) |

- **반복의 흔들림도 적습니다.** 3회 중 2회 통과는 "통과"가 아닙니다. 흔들린 케이스는 원인(LLM 판단 · 시간 초과 · 외부 지연)을 씁니다. OpenAI 응답이 가끔 늦어 한 번 실패하는 일은 있습니다 (73일차 검증 때도 한 번). 같은 조건으로 다시 돌리고 둘 다 적습니다.
- 숫자는 **실제 보고서에서만** 옮깁니다. 기억이나 예상으로 채우지 않습니다.

## 5. 실패 사례 쓰기 (원본 결과서 4절)

| 칸 | 예 |
| --- | --- |
| 현상 | WF-05에서 영업팀 직원에게 관리자 문서의 절차가 답에 나옴 |
| 재현 조건 | 이준호, "서버실 출입 절차 알려줘", 색인 v1 |
| 원인 (근거) | 검색 뒤에 권한을 걸러서 LLM에 권한 없는 청크가 들어감 (실행 화면의 검색 결과) |
| 조치 | 권한별 메모리 키로 나누고 검색 전에 고름 |
| 재시험 | 같은 조건 3회 통과 (`runs/...json`) |
| 잔여 위험 | 메타데이터를 빠뜨린 새 문서는 `all`로 들어감 → 색인에서 권한 없는 문서를 거부하게 할 것 |

실패 사례가 없으면 결과서가 약해집니다. 일부러 깨 보고 고친 기록(고치기 전 → 고친 뒤)이 가장 좋은 증거입니다 (72 · 73일차의 "고치기 전" 단계).

## 6. 시연 준비 (원본 5절)

원본 시연 순서 7단계를 그대로 따르되, **실행 화면을 미리 띄워 두고** 시나리오 파일로 보여 줍니다. 손으로 입력하다 오타 · 느림으로 시간을 쓰지 않게, 시연용 요청 파일(`requests/demo-*.json`)을 만들어 `call -v`로 보냅니다. 장애 시연은 `fault` → `call` → `fault all ok`를 한 줄씩.
