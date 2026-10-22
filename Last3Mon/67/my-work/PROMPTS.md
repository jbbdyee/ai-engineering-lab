# 67일차 실습 요청문 기록

## Lab 03 예제 2 · 검증과 담당자 연결

이 기록은 이미 구현한 `it-agent.json`의 조건과 결과 모양을 정리한 것입니다. 구현 전에 작성했던 요청문으로 소급하지 않습니다.

### 1. 좋은 답의 검사 기준

`Check answer`의 Code 노드에서 다음 다섯 조건을 확인합니다. 모두 통과해야 자동 답변을 보냅니다.

1. `answer_not_empty`: Agent의 답을 앞뒤 공백 제거한 뒤에도 글자가 있어야 합니다.
2. `tool_found_data`: 질문에 맞는 도구의 결과에 실제 데이터가 있어야 합니다. FAQ는 `results`에 항목이 있어야 하고, 접수 조회는 `ticket_id`가 있어야 합니다. 빈 FAQ 결과·404 `ticket not found`·403 `not your ticket`은 찾은 데이터로 세지 않습니다.
3. `ticket_tool_for_ticket_question`: 질문에 `T-`와 네 자리 숫자로 된 접수 번호가 있으면 `Get_ticket`을 사용해야 합니다.
4. `korean_answer`: 답에 한글이 포함되어야 합니다.
5. `short_answer`: 답은 400자 이하여야 합니다.

### 2. 번호로 나눈 구현 요청문

1. **입력 검증:** `IT question webhook` 뒤의 `Has question?`에서 본문의 `question`을 앞뒤 공백 제거한 뒤 비어 있는지 검사하세요. 비어 있으면 Agent를 호출하지 않고 `Reject empty`에서 HTTP 400과 `{"error":"question is required"}`를 반환하세요. 정상 질문만 기존 `IT help agent`로 보내세요.
2. **결과 검증:** Agent 뒤에 `Check answer`를 두고 위 다섯 조건을 Code로 검사하세요. Agent의 `output`과 `intermediateSteps`, 웹훅의 원래 질문을 읽어 `answer`, `tools_used`, `sources`, `failed`, `passed`를 만드세요. 검사 통과 여부를 LLM에게 다시 묻지 마세요. 기존 FAQ·접수 조회 도구와 웹훅의 `user`에서 가져오는 `requester` 설정은 유지하세요.
3. **결과 모양:** `Passed?`의 true 출력은 `Auto answer`로 보내 `route: "자동 답변"`, `answer`, `tools_used`, `sources`를 반환하세요. false 출력은 `Hand off`로 보내 `route: "담당자 연결"`, `answer: "정확한 답을 찾지 못해 IT 담당자에게 문의를 전달했습니다."`, `draft`, `tools_used`, `failed`를 반환하세요. 두 갈래 모두 `Send result`로 이어 주세요.

검증 기준은 `cases/lab03.json`입니다. 테스트 파일의 기대 결과는 바꾸지 않습니다.
