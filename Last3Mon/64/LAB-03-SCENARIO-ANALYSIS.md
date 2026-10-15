# Lab 03 · 업무 자동화 시나리오 분석과 워크플로우 설계

- 관련 강의: [3단계 · 업무 자동화 시나리오 분석](../../Lecture/64/03-STAGE3-AUTOMATION-SCENARIO.md)
- 소요 시간: 약 45분 (개인 또는 2인 1조)
- 목표: 하나의 업무를 분석해 노드와 연결로 바꾸고, 실제로 실행해 검증한다.
- 제출물
  - `my-work/LAB-03-SCENARIO-ANALYSIS.md` (분석 문서)
  - `workflow-lab/flows/my-scenario.json` (워크플로우)

## 1. 예시 먼저 실행해 보기 (10분)

```bash
cd Last3Mon/64/workflow-lab
uv run miniflow memory --clear
uv run miniflow run flows/05-tech-support-ticket.json -i user=kim -i ticket="비밀번호를 잊어버려서 로그인이 안 돼요"
uv run miniflow run flows/05-tech-support-ticket.json -i user=kim -i ticket="VPN 접속이 계속 끊겨요"
uv run miniflow run flows/05-tech-support-ticket.json -i user=lee -i ticket="점심 메뉴 추천해줘"
```

| 실행 | 확인할 것 |
| --- | --- |
| 1번째 | `category`와 `faq_id`가 무엇인가? |
| 2번째 | `history` 노드 출력에 1번째 문의가 남아 있는가? |
| 3번째 | 어느 노드에서 왜 멈추었는가? `draft` 노드는 무엇이라고 답했는가? 이 경우 실제 업무에서는 어떻게 처리해야 할까? |

3번째 실행에서는 FAQ 검색 결과가 없는데도 LLM이 답변 초안을 만들고, 마지막 `result` 노드에서 멈춥니다. Mock으로 실행(`MINIFLOW_LLM=mock`)하면 `draft` 노드에서 바로 멈춥니다. **근거가 없을 때 실제 LLM이 어떻게 행동하는지** 실행 기록에서 확인해 보세요.

| 모델 (수업 전 측정) | `draft`가 쓴 답 | `result` |
| --- | --- | --- |
| `gpt-4.1-mini` | "점심 메뉴 추천에 관한 FAQ가 현재 제공되지 않아 … 양해 부탁드립니다" (솔직하게 답함) | `'0' not found`로 실패 |
| 대체 `gemma3:4b` (`MINIFLOW_LLM=ollama`) | "… FAQ 검색 결과가 없습니다. (FAQ ID: other-123)" (**없는 FAQ 번호를 지어냄**) | `'0' not found`로 실패 |

좋은 모델은 근거가 없다고 말했지만, 워크플로우는 어느 쪽이든 마지막에 가서야 멈춥니다. 모델이 바뀌어도 안전하려면 "FAQ가 없으면 담당자에게" 같은 **경로**가 필요합니다 (65일차 Condition).

`uv run miniflow show flows/05-tech-support-ticket.json`으로 구조도 확인합니다.

## 2. 시나리오 분석 (15분)

1. 아래 시나리오 중 하나를 고릅니다. 직접 겪은 업무로 만들어도 됩니다.

   | 번호 | 시나리오 |
   | --- | --- |
   | S1 | 회의록 요약 후 할 일 정리 |
   | S2 | 쇼핑몰 상품 리뷰 분류와 답글 초안 |
   | S3 | 신규 입사자 질문 응답 |
   | S4 | 출장 전 날씨·준비물 안내 |
   | S5 | IT 문의 처리 확장 (분류별 담당 부서 안내) |

2. 템플릿을 복사합니다.

   ```bash
   mkdir -p Last3Mon/64/my-work
   cp Last3Mon/64/templates/SCENARIO-ANALYSIS-TEMPLATE.md Last3Mon/64/my-work/LAB-03-SCENARIO-ANALYSIS.md
   ```

3. 모든 항목을 채우고 AS-IS·TO-BE를 Mermaid로 그립니다.
4. TO-BE의 각 단계를 LLM·Tool·Memory·데이터 처리·사람 확인 중 하나로 분류합니다.

## 3. 워크플로우로 옮기기 (15분)

TO-BE를 `flows/my-scenario.json`으로 작성합니다. 지금 사용할 수 있는 노드와 Tool로 표현할 수 있는 부분만 작성하고, 나머지(메일 발송, 사람 확인 등)는 분석 문서에 "향후 노드"로 적습니다.

시작용 뼈대:

```json
{
  "name": "My scenario",
  "description": "시나리오 설명",
  "inputs": ["user", "text"],
  "nodes": [
    {"id": "start", "type": "input"},
    {"id": "history", "type": "memory_read", "key": "my:{{input.user}}"},
    {"id": "judge", "type": "llm",
     "prompt": "다음 내용을 분류해 주세요: {{input.text}}",
     "mock": {"rules": [{"if_contains": ["키워드"], "then": "분류값"}], "default": "other"}},
    {"id": "save", "type": "memory_write", "key": "my:{{input.user}}",
     "value": {"last_text": "{{input.text}}", "last_label": "{{nodes.judge.output}}"}},
    {"id": "result", "type": "output", "value": {"label": "{{nodes.judge.output}}"}}
  ],
  "edges": [["start", "history"], ["start", "judge"], ["history", "save"], ["judge", "save"], ["save", "result"]]
}
```

```bash
uv run miniflow validate flows/my-scenario.json
uv run miniflow show flows/my-scenario.json
uv run miniflow run flows/my-scenario.json -i user=me -i text="..."
```

Tip

- LLM 노드의 프롬프트에는 답의 형식(정해진 값, 문장 수 등)을 분명히 적습니다. LLM 답이 매번 달라 흐름 확인이 어려우면 `mock`의 `rules`·`template`을 함께 적고 `MINIFLOW_LLM=mock`으로 구조부터 확인합니다.
- 사용할 수 있는 Tool은 `uv run miniflow tools`로 확인합니다 (`get_weather`, `search_faq`, `count_chars`).
- `show` 결과를 분석 문서의 "구현한 워크플로우" 항목에 붙여 넣습니다.

## 4. 검증 (5분)

정상 입력 2개와 문제가 생길 수 있는 입력 1개로 실행하고, 결과를 분석 문서의 "실행 결과" 표에 기록합니다.

## 확인

- [ ] 분석 템플릿의 모든 항목을 채웠다.
- [ ] AS-IS와 TO-BE를 Mermaid로 그렸다.
- [ ] `my-scenario.json`이 `validate`를 통과했다.
- [ ] 정상 입력과 문제 입력의 실행 결과를 비교했다.
