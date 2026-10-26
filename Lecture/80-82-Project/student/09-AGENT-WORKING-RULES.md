# CLI 코딩 에이전트로 프로젝트하기

66~79일차처럼 워크플로우 JSON은 CLI 코딩 에이전트(codex · claude · agy)에게 **내가 쓴 요청문**으로 만들게 하고, **내가** push · test로 확인합니다. 하루짜리 실습과 다른 점은 **여러 사람 · 여러 날 · 여러 파일**이라는 것입니다.

## 1. 팀 저장소의 `AGENTS.md`

에이전트는 저장소 뿌리의 `AGENTS.md`(claude는 `CLAUDE.md`에 `@AGENTS.md` 한 줄)를 읽습니다. 64~79일차의 `AGENTS.md`를 바탕으로 팀 것을 만듭니다. **첫날 리드가 만들고 팀이 함께 고칩니다.**

```markdown
# AGENTS.md · <팀이름> Tech Support 워크플로우

## 1. 작업 순서
1. 요청을 읽고 입력 · 노드 순서 · 결과 모양을 3~5줄로 먼저 보여 준다.
2. workflows/<팀>-<이름>.json 을 고친다 (새 파일은 요청받을 때만).
3. uv run ~/aio-01d4-stu/Last3Mon/80/tools/flow.py check workflows/<파일> → 오류가 없을 때까지.
4. 바꾼 노드 · check 결과 · 사람이 실행할 push · test 명령을 한국어로 보고한다.
5. push · test는 사람이 한다. 같은 곳을 3번 고쳐도 실패하면 멈추고 다른 방법을 제안한다.

## 2. 환경
(Last3Mon/80/AGENTS.md 2절을 옮김: n8n · OpenAI Credential · 데이터 API · 웹훅 경로)

## 3. 계약
(docs/WORKFLOW-DESIGN.md의 요청 · 응답 · route 값 · 연결선 페이로드 표를 가리킴)

## 4. 노드 규칙
(Last3Mon/80/AGENTS.md 5절의 검증된 노드를 가리킴: Webhook Header Auth · HTTP Request 재시도 · Agent · Vector Store · Error Trigger)

## 5. 하지 말 것
- 공통 계약(요청 · 응답 칸, route 값)을 바꾸지 않는다.
- 키 · 토큰을 JSON · 문서에 쓰지 않는다. Credential id만 쓴다.
- 테스트를 통과시키려고 cases/*.json 의 기대 결과를 바꾸지 않는다.
- 다른 사람이 맡은 workflows/ 파일을 고치지 않는다 (요청받은 경우만).
```

## 2. 요청문은 설계서에서

3일 프로젝트에서 요청문의 재료는 **설계서**입니다. 설계서의 표(역할 카드 · 연결선 페이로드 · 예외 처리 표)를 먼저 쓰고, 에이전트에게는 "설계서의 그 표대로"라고 시킵니다. 그러면 ① 요청문이 짧아지고 ② 설계서와 구현이 같아지고(평가 기준) ③ 다른 팀원이 같은 표로 다른 부분을 만들 수 있습니다.

```text
docs/WORKFLOW-DESIGN.md 4절의 "분류 Agent" 역할 카드와 6절의 "전처리 → 분류" 연결선 표를 읽고,
workflows/team1-support.json 의 Classify 노드와 Parse class(Code)를 그 표대로 만들어 줘.
출력 JSON 을 못 읽으면 type "unknown", urgency "normal", missing [] 로 (fail-closed: 뒤에서 이관).
기대 결과 cases/team.json 의 "분류" 세 케이스, 공통 cases/common.json 의 WF-01 · WF-02.
```

## 3. 여러 사람이 함께

| 할 일 | 방법 |
| --- | --- |
| 파일 나누기 | 한 사람 = 한 워크플로우 파일 (04 문서 5절의 하위 워크플로우) |
| 바꾸기 전 | `git pull` → 내 파일만 에이전트에게 |
| 바꾼 뒤 | `flow.py check` → `push` → 공통 시나리오 → `git commit` (메시지에 통과 수: "분류 Agent · common 7/14") |
| 계약을 바꿔야 할 때 | 리드에게 → 설계서 3절을 먼저 고치고 → 그다음 코드 |
| 다른 사람 n8n에서 확인 | 상대가 `git pull` → `flow.py push workflows/*.json` |

## 4. 하루짜리 실습과 다른 점

| 실습 | 프로젝트 |
| --- | --- |
| 요청문 뼈대 · 빈칸이 주어짐 | 요청문을 처음부터 (설계서가 재료) |
| 정답 워크플로우 · `reference/`가 있음 | 없음. 64~79일차의 내 `my-work/`와 `reference/`를 **가져다 고침** |
| 테스트 파일이 주어짐 | 공통은 주어짐, 팀 것은 직접 |
| 한 사람 · 한 파일 | 여러 사람 · 여러 파일 · 저장소 |

64~79일차의 `reference/` · `answers/` 워크플로우를 가져다 쓰는 것은 **권장**합니다. 가져온 것은 설계서에 "어디서 가져와 무엇을 바꿨나"를 한 줄 적습니다.
