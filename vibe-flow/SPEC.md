# n8n 워크플로우 학습 정리와 실제 사례

## 목적과 범위

이 문서는 저장소에 있는 65~70일차 n8n 수업 자료와 실습 산출물을 바탕으로, 지금까지 배운 워크플로우의 구조와 업무 사례를 정리한다. 여기서 **실제 사례**는 수업에서 구현하거나 테스트하도록 제공된 구체적인 업무 시나리오를 뜻한다. 운영 환경에 배포됐다는 의미는 아니다. 개인 실습의 전체 이력은 이 저장소만으로 확인할 수 없다.

## 공통 구조

워크플로우는 **Trigger → Condition → Action → Response**로 설계한다. Trigger는 수동 실행 또는 HTTP Webhook이고, Condition은 IF·Switch로 입력 유효성이나 업무 종류를 판단한다. Action은 Set·Code·HTTP/LLM·Agent·하위 워크플로우 등으로 일을 처리한다. 마지막에는 호출자가 사용할 수 있는 응답을 만든다. [65일차 개요](../Last3Mon/65/README.md)

설계할 때는 입력·출력 계약, 빈 입력 처리, 자동 처리 가능한 범위, 담당자 연결 조건을 먼저 정한다. 66일차부터는 요구를 적어 CLI 코딩 에이전트로 n8n JSON을 만들고, `flow.py check → push → call → test`로 형식과 실행 결과를 확인하는 방식으로 발전했다. `push`는 n8n에 게시하는 실습 명령이며 GitHub push와 다르다. [66일차 실습](../Last3Mon/66/README.md)

## 배운 워크플로우와 업무 사례

| 단계 | 핵심 개념 | 구체적인 사례와 흐름 | 결과·예외 처리 | 근거 |
| --- | --- | --- | --- | --- |
| 65일차: 기본 분기 | Manual/Webhook, IF, Switch | 문의 접수 시 내용을 확인하고, 긴급 여부와 분류값에 따라 처리 경로·담당 팀을 정한다. | 빈 내용은 거절하고, 분류 결과를 응답한다. | [65일차 개요](../Last3Mon/65/README.md), [Webhook 라우터 JSON](../Last3Mon/65/n8n/workflows/02-webhook-router.json) |
| 65일차: AI 문의 | LLM 분류, FAQ 조회, 조건 분기 | `POST /ai-request`로 들어온 문의를 분류하고 FAQ를 찾는다. FAQ가 있으면 LLM으로 답변을 작성한다. | FAQ가 없으면 담당자에게 넘긴다. n8n 장애 때는 별도 miniflow 실행 경로를 시험한다. | [AI 문의 실습](../Last3Mon/65/LAB-03-AI-WORKFLOW-FAILOVER.md), [워크플로우 JSON](../Last3Mon/65/n8n/workflows/03-ai-request-flow.json) |
| 66일차: 회의록 자동화 | JSON 파싱, 항목별 처리, 병렬 작업과 합치기 | 회의 제목·본문을 받아 요약과 할 일 추출을 두 갈래로 진행하고 결과를 합친다. 추출된 할 일을 항목별로 확인해 보고서를 만든다. | 빈 회의록은 거절하고, 할 일이 없는 경우 별도 결과를 낸다. 담당·기한이 미정이면 확인 필요로 표시한다. | [66일차 개요](../Last3Mon/66/README.md), [개인 워크플로우 JSON](../Last3Mon/66/n8n/myworkflows/66-agy-meeting-notes.json) |
| 67일차: IT 문의 Agent | Agent의 Tool 선택, 데이터 API, 답변 검증 | IT 질문을 받은 Agent가 FAQ 검색이나 접수 현황 조회 Tool을 골라 사용한다. 접수 현황은 요청자 본인 건만 보여 준다. | 질문이 비면 거절하고, 근거가 부족하거나 검증에 실패하면 담당자에게 연결한다. | [67일차 개요](../Last3Mon/67/README.md), [데이터 Tool 실습](../Last3Mon/67/LAB-02-Q-DATA-TOOLS.md) |
| 68일차: 복합 업무 도우미 | 업무 분해, 라우팅, 여러 Agent 결과 수집 | “VPN 문의와 회의록 정리” 같은 한 요청을 IT·회의 업무로 나눠 각각의 Agent에 보내고 통합 답변을 만든다. | 필요한 입력이 빠지면 추가 입력을 요청하고, 담당 Agent가 실패하면 해당 업무의 실패를 다른 결과와 분리해 표시한다. | [68일차 개요](../Last3Mon/68/README.md), [검증·격리 실습](../Last3Mon/68/LAB-03-Q-VERIFY-AND-ISOLATE.md) |
| 69일차: 공지문 작성 팀 | 역할 분리, 순차 협업, 재검토, Fork-Join | 작성자 Agent가 공지 초안을 쓰고 검토자 Agent가 사실·규칙을 확인한다. 통과한 문안은 제목과 메신저 글로 다듬는다. | 검토 실패 시 의견에 따라 한 번 수정·재검토한다. 계속 실패하거나 검토자가 꺼지면 담당자 확인으로 보낸다. | [69일차 개요](../Last3Mon/69/README.md), [개인 설계](../Last3Mon/69/my-work/DESIGN.md) |
| 70일차: 공지 키트와 규칙 검사 | 템플릿, Sub-workflow, 버전 관리 | 점검·보안·교육 공지의 공통 구조는 하나의 키트로 묶고, 종류별 문구는 설정 표로 관리한다. 공지와 SMS가 같은 규칙 검사 모듈을 재사용한다. | 새 종류·알 수 없는 종류를 구분하고, 모듈 변경 시 기존 호출자와의 호환성을 확인한다. 깨지는 변경은 v2로 분리한다. | [70일차 개요](../Last3Mon/70/README.md), [개인 설계](../Last3Mon/70/my-work/DESIGN.md) |

## 사례를 통해 배운 설계 원칙

1. **입력과 결과를 먼저 정의한다.** Webhook 필드, 성공 응답, 오류 응답을 정해야 분기와 테스트가 명확해진다. 회의록 사례의 빈 본문, IT 사례의 빈 질문이 대표적이다.
2. **규칙이 분명한 일은 조건 노드로 처리한다.** 빈 값 검사, 업무 종류 라우팅, 규칙 검사는 IF·Switch·Code가 맡는다. 분류·요약·초안처럼 해석이 필요한 곳에 LLM 또는 Agent를 둔다.
3. **Agent의 답을 그대로 확정하지 않는다.** FAQ 출처와 본인 접수 건 범위를 확인하고, 검증 실패는 담당자 연결로 처리한다.
4. **병렬과 순차 협업을 구분한다.** 회의 요약과 할 일 추출, 독립 업무의 IT·회의 처리는 결과를 합칠 수 있다. 공지 작성→검토→수정은 앞 단계 결과가 필요하므로 순서대로 실행한다.
5. **재사용할 때 계약과 버전을 관리한다.** 공통 규칙은 하위 워크플로우로 빼고, 입력·출력 형태가 바뀌면 기존 사용처를 점검하거나 새 버전을 만든다.

## 검증 기준

- JSON의 노드 유형·연결·Credential 참조와 민감정보 노출 여부를 `flow.py check`로 확인한다.
- 정상 입력뿐 아니라 빈 입력, 할 일 없음, 입력 누락, Agent 장애, 규칙 위반을 `call`과 `test` 케이스로 확인한다.
- 응답값과 함께 실행 경로를 확인한다. 특히 자동 답변, 담당자 연결, 재검토, 모듈 버전 분기가 의도대로 선택됐는지 본다.
- 수업 문서의 기대 흐름과 저장소의 JSON은 근거 자료다. 실제 운영 적합성은 별도 데이터·권한·장애 조건으로 다시 검증해야 한다.

## Routine Scout 프로젝트 명세

### 목적과 구현 범위

Routine Scout는 작업 이벤트 목록에서 반복되는 `source + action + target` 조합을 찾아 자동화 후보를 추천하는 **n8n 단독 MVP**다. 사용자는 테스트용 JSON을 Webhook에 보내고 JSON 결과를 받는다. 집계와 추천 판단은 n8n 내부에서 수행한다. 외부 시스템, 외부 계정, LLM/Agent, 실제 macOS 사용 행동 수집은 이번 MVP에 포함하지 않는다.

프로젝트 개발 서버는 `http://localhost:5678/`이고 요청 경로는 `POST /webhook/routine-scout/analyze`다. 이 절의 경로와 응답 계약은 [TODO.md](TODO.md)의 구현 계획과 같다. 위의 수업 사례와 공통 설계·검증 원칙은 그대로 적용한다.

### 입력 JSON

본문은 JSON 객체이며 `events`는 필수 배열이다. 각 원소는 객체이고 `source`, `action`, `target`은 필수 문자열이다. 세 값은 앞뒤 공백을 제거한 뒤에도 비어 있으면 안 된다. 값의 대소문자는 구별하고 추가 필드는 분석에서 무시한다. 빈 `events` 배열은 유효하다.

```json
{
  "events": [
    {"source": "codex", "action": "copy", "target": "chatgpt"},
    {"source": "codex", "action": "copy", "target": "chatgpt"},
    {"source": "codex", "action": "copy", "target": "chatgpt"}
  ]
}
```

### 분석 및 출력 JSON

검증이 끝난 모든 이벤트를 세 필드 조합으로 집계한다. 문자열에 구분자가 들어 있어도 다른 조합과 충돌하지 않는 키를 사용한다. 같은 패턴이 **3회 이상**이면 모두 추천한다. `patterns`는 1회 이상인 모든 패턴의 `source`, `action`, `target`, `repeat_count`를 담고, `recommendations`는 기준을 충족한 패턴에 고정 템플릿 `suggestion`을 더해 담는다. 두 배열 모두 횟수 내림차순, 동률이면 `source` → `action` → `target` 문자열 오름차순으로 정렬한다.

추천이 있으면 HTTP 200과 `status: "recommend"`를 반환한다.

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

추천이 없으면 HTTP 200, `status: "no_recommendation"`, 빈 `recommendations`와 집계된 `patterns`를 반환한다. 빈 `events`의 응답은 다음과 같다.

```json
{"status": "no_recommendation", "recommendations": [], "patterns": []}
```

### n8n 노드와 예외 처리

기본 흐름은 **Webhook → Code → IF(입력 유효성) → IF(추천 여부) → 결과 생성 → Respond to Webhook**이다. Code가 전체 입력을 검증하고 패턴을 집계·정렬한다. 유효성 IF는 오류와 정상 경로를 나누고, 추천 여부 IF는 추천 후보의 존재를 판단한다. 결과 생성 노드는 각 경로의 JSON과 HTTP 상태를 만들며 Respond to Webhook이 최종 응답을 보낸다. 각 실행 경로는 한 번만 응답해야 한다.

JSON 문법에는 문제가 없지만 객체가 아닌 본문, `events` 누락·자료형 오류, 객체가 아닌 이벤트, 필수 필드 누락·공백·자료형 오류가 있으면 요청 전체를 거절한다. 이 업무 입력 검증 오류는 Code 노드가 처리하며 첫 오류의 위치를 `field`에 기록한다. 예를 들어 `events[0].source`다. HTTP 400 응답의 구조는 다음과 같으며 원본 입력값은 메시지에 넣지 않는다.

```json
{
  "status": "error",
  "recommendations": [],
  "patterns": [],
  "error": {"code": "INVALID_INPUT", "field": "events[0].source", "message": "필수 문자열 필드가 필요합니다."}
}
```

`Content-Type: application/json` 요청의 JSON 문법이 잘못된 경우에는 n8n의 선행 JSON 파서가 Webhook 워크플로우 실행 전에 요청을 거절한다. 로컬 n8n 2.42.6에서 `{"events": [}` 요청에 대해 관찰한 응답은 **HTTP 422**와 `code: 422`, `message: "Failed to parse request body"`를 포함한 n8n 자체 오류 JSON이다. 이 경로에서는 Routine Scout의 Code 노드가 실행되지 않으므로 위 HTTP 400 응답이나 `status: "error"`, `error.field: "body"` 구조를 요구하지 않는다. 정상 JSON과 업무 입력 검증 오류는 기존 응답 계약을 유지한다. 예상하지 못한 노드 오류도 내부 정보와 입력 원문을 노출하지 않는 JSON으로 처리할 경로를 검토한다.

### 테스트 및 구현 검증

동일 작업 3회와 2회, 여러 종류가 섞인 입력, 여러 패턴의 동시 추천과 동률 정렬, 빈 배열, 필수 필드 누락·공백, 잘못된 자료형, 잘못된 JSON 본문을 각각 시험한다. 응답의 HTTP 상태·JSON 필드·횟수·정렬뿐 아니라 실제 n8n 분기 경로를 확인한다.

수업에서 사용한 CLI 코딩 에이전트로 워크플로우 JSON을 작성하고 기존 `../Last3Mon/66/tools/flow.py` 또는 `../Last3Mon/70/tools/flow.py`의 환경 적합성을 확인한다. `doctor → check → push → call → test` 순서로 로컬 n8n에서 검증한다. `check`에서는 노드 유형·버전·연결·Credential 및 민감정보를 확인한다. 구현 단계의 `push.sh`는 검증된 JSON을 로컬 n8n에 게시하는 절차로 작성하며, n8n 게시와 GitHub push를 구별한다. 형식 검사와 모든 시나리오가 통과하고 정상 응답·업무 입력 오류·JSON 문법 오류가 각각 위 JSON 계약에 맞아야 MVP가 완료된다.

### 향후 확장

실제 macOS 작업 이벤트 수집, 사용자 승인 후 자동화 등록·실행, 캐릭터 UI는 향후 확장에만 해당한다. 수집 가능성, 권한과 데이터 보관 기준은 별도로 검증한다.
