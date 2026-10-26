# 자주 묻는 것 · 막혔을 때

## 자주 묻는 것

<details><summary>Slack · Jira를 실제로 연동해야 하나요?</summary>

아니요. 기본은 데이터 API(연습용)입니다 ([02-ENVIRONMENT-AND-SERVICES](02-ENVIRONMENT-AND-SERVICES.md) 2절). 평가 기준은 "연동 노드가 인증과 에러 처리를 포함해 안정적으로 구성되었는가"이고, 연습용으로 그것을 보이면 됩니다. 설계서에 실제 서비스로 바꿀 때 달라지는 것(인증 방식 · 오류 코드 · 한도)을 함께 적습니다. 실제 연동은 가산입니다.
</details>

<details><summary>병렬을 넣었는데 빨라지지 않아요.</summary>

n8n v1 실행 순서는 갈래를 차례로 실행합니다 (66일차). 구조상 병렬(서로 기다리지 않는 두 일)이라는 설계는 맞고, 시간은 합이 됩니다. 설계서에 "왜 병렬 구조인가(서로 독립)"와 잰 시간을 적고, 운영에서 정말 동시에 하려면 무엇이 필요한지(하위 워크플로우를 비동기로 부르고 모으기, 큐)를 씁니다.
</details>

<details><summary>루프는 어디에 넣어야 하나요?</summary>

목적이 있는 곳에만: 보완 질문(요청 사이, `attempt`), 검색 점수가 낮을 때 질문을 다시 써서 한 번 더 검색(요청 안), 외부 호출 재시도. **끝(최대 횟수)**이 없는 루프는 감점입니다 ([04-REFERENCE-ARCHITECTURE](04-REFERENCE-ARCHITECTURE.md) 4절).
</details>

<details><summary>In-Memory 벡터 저장소로 백업 · 복구 · 확장을 어떻게 쓰나요?</summary>

오늘 구현하는 것(원본 문서는 git, 색인 워크플로우로 언제든 재생성, 버전 메모리 키와 되돌리기, 재색인 시간 · 비용 측정)과 운영에서 할 것(지속형 저장소 · 스냅숏 · 파티션)을 나눠 씁니다 ([05-RAG-DESIGN-GUIDE](05-RAG-DESIGN-GUIDE.md) 7절). 오늘 잰 숫자로 확장을 어림하면 평가 기준을 채웁니다.
</details>

<details><summary>공통 시나리오의 기대와 우리 팀 판단이 달라요.</summary>

공통 시나리오는 바꾸지 않습니다. 기대 칸에 여러 값이 허용된 곳(예: WF-05 `권한 없음` 또는 `담당자 이관`)에서 고르고, 설계서에 근거를 적습니다. 정말 틀렸다고 생각하면 강사에게 말합니다.
</details>

<details><summary>LLM 결과가 실행마다 달라 시험이 흔들려요.</summary>

① 판단을 Code로 옮길 수 있는지 봅니다 (점수 기준 · 권한 · 키워드). ② Agent 출력을 JSON으로 받고 못 읽으면 안전한 쪽으로. ③ 시나리오의 기대를 문장이 아니라 계약 칸(`route` · `sources`)으로. ④ `--repeat 3`으로 재고 흔들린 것을 결과서에 씁니다.
</details>

<details><summary>팀원 노트북마다 결과가 달라요.</summary>

같은 `workflows/*.json`을 push했는지(`git pull`), 데이터 API가 단위 프로젝트 판인지(`doctor`), 고장 스위치가 꺼져 있는지(`fault all ok`), 색인을 다시 만들었는지(In-Memory는 n8n을 다시 켜면 비어 있음)를 봅니다.
</details>

## 막혔을 때

| 증상 | 할 일 |
| --- | --- |
| `call`이 404 | 웹훅 경로(`<팀>-support`)를 바꿨는지, push했는지 |
| `call`이 401 | Header Auth를 걸었다면 `FLOW_WEBHOOK_KEY` |
| 검색 결과가 늘 비어 있음 | n8n을 다시 켰다면 색인 워크플로우를 다시 부름, 메모리 키가 색인 · 검색에서 같은지 |
| 모든 LLM 단계 실패 | `flow.py llm up` (누가 `llm down`을 남김), `doctor` |
| 티켓이 두 개씩 생김 | `POST /tickets`의 `key`에 `request_id`를 넣었는지, 재시도가 key 없이 다시 보내는지 |
| 장애 시나리오 뒤 다른 시나리오가 실패 | `flow.py fault all ok`, 시나리오 파일의 `after` |
| Error Workflow가 안 돎 | 게시(활성화)했는지, 본체 워크플로우 설정에 지정했는지 |
| 같은 곳을 3번 고쳐도 실패 | 요청을 더 작게, 64~79일차 `reference/`에서 그 부분만 가져오기, 강사 호출 |
| 하루가 끝났는데 통과 수가 그대로 | 가산을 멈추고 필수 시나리오부터 (01 문서 3절 끝) |
