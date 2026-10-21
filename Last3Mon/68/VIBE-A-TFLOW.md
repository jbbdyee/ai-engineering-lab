# 7교시 바이브 코딩 · `tflow` 만들기

> **정답본** · 수업이 끝난 뒤 공개합니다. 요청서는 [VIBE-REQ-TFLOW.md](VIBE-REQ-TFLOW.md), 문제는 [VIBE-Q-TFLOW.md](VIBE-Q-TFLOW.md).
> 68일차부터 바이브 코딩 프로그램은 **수업 준비 때 미리 만들어 보지 않습니다.** 아래 요청문은 예시이고, 확인 기준은 입력 파일에서 직접 센 값입니다. 걸린 시간은 수업 중 강사 바이브 코딩(8교시)에서 재어 기록합니다.

- 시간: 16:00~16:50 (50분) · 발표와 정리는 8교시
- 요구 R1~R6은 학생용과 같습니다.

## 요청서 → 요구 도출 예 (`SPEC.md` 예)

요청서의 말을 **확인할 수 있는 요구**로 바꾼 예입니다. 정답이 하나는 아닙니다. "됐다 / 안 됐다"를 말할 수 있는지가 기준입니다.

### 1. 요구

| 번호 | 요구 | 요청서의 말 | 확인 방법 |
| --- | --- | --- | --- |
| R1 | 웹훅에서 `main`을 따라가는 트리, If는 true/false · Switch는 출력 이름을 갈래에 | ① | `agents/it-agent.json`의 `Has question?` 아래 true · false. `reference/lab03-example2-isolated.json`의 `Route by type` 아래 4갈래 |
| R2 | `ai_languageModel` · `ai_tool`은 받는 Agent 아래에 따로 | ② | `IT help agent` 아래 모델 1 (`OpenAI chat model`), Tool 2 (`Search FAQ`, `Get ticket`) |
| R3 | 노드를 고르면 종류 · 중요한 설정 · 한국어 설명, 설명은 캐시 | ③ | 같은 노드를 두 번 고르면 두 번째는 LLM 호출 없음 (테스트에서 가짜 설명기 호출 1번) |
| R4 | `--md`로 mermaid 블록이 든 `.md` 파일 (TUI `m`도 같은 파일) | ④ | `it-agent.md`를 미리보기로 열면 그림, 노드 14개 상자 |
| R5 | 없는 노드를 가리키는 연결, 떨어진 노드를 경고 | ⑤ | 망가진 파일 두 개에서 경고 각 1개 |
| R6 | 터미널 TUI | "브라우저 말고 터미널" | `uv run tflow agents/it-agent.json`이 열리고 `q`로 닫힘 |

### 2. 숨은 요구

- 다시 모이는 노드: it-agent의 `Send result`는 `Auto answer` · `Hand off` 두 곳에서 들어옴 → 두 번째는 `↩ Send result (above)` 한 줄.
- 망가진 파일: 받지 않았으므로 테스트용으로 만든다 (연결 이름 하나 틀리게, 떨어진 노드 하나 더하기).
- 키 없음 · LLM 실패: "설명 없음 (키 없음)" / "설명 실패: …", 트리와 mermaid는 그대로.
- 비밀: LLM 입력에서 `credentials` 제외. 캐시 키는 노드 `type + parameters`의 해시 (이름만으로 하면 바뀐 노드에 옛 설명).
- mermaid: id `n0`, `n1` …, 보이는 이름은 `n3["Has question?"]`.

### 3. 범위 밖

편집, n8n API 연결, 실행 기록. (강사 바이브 코딩에서 `diff`, 실행 기록 붙이기를 보여 줌)

### 4. 순서와 이유

1. 파일 → Node · Link 목록 (`model.py`) + 숫자 테스트. 트리 · mermaid · TUI · 경고가 **모두 이것을 씀**.
2. 글자 트리 · `--md` (R1 · R4). 화면 없이 확인이 빠름. 그림은 터미널이 못 그리므로 `.md` 미리보기로.
3. TUI · 상세 · 경고 (R2 · R5 · R6).
4. LLM 설명 · 캐시 (R3). 비싸고 실패할 수 있는 것은 마지막, 없어도 앞의 것은 동작.

### 자주 빠뜨리는 것 (수업 중 본 것으로 채움)

| 빠뜨린 것 | 생기는 일 |
| --- | --- |
| 다시 모이는 노드 | 트리에 `Send result` 아래가 두 번, isolated 파일은 네 번 |
| 확인 방법의 숫자 | 에이전트가 "완료"라고 하면 그대로 넘어감 |
| 망가진 파일 | R5를 확인할 방법이 없음 |
| (수업 뒤 기록) | |

## 확인 기준 (입력 파일에서 센 값)

| 파일 | 노드 | 연결 | 확인할 것 |
| --- | --- | --- | --- |
| `agents/meeting-agent.json` | 7 | main 5 · ai_languageModel 1 | 웹훅 → `Has notes?` → true `Meeting notes agent` / false `Reject empty` |
| `agents/it-agent.json` | 14 | main 11 · ai_languageModel 1 · ai_tool 2 | `IT help agent`에 모델 `OpenAI chat model`, Tool `Search FAQ`·`Get ticket`. `Send result`는 `Auto answer`·`Hand off` 두 곳에서 들어옴 |
| `reference/lab03-example2-isolated.json` | 18 | main 19 · ai_languageModel 1 | `Route by type` 출력 4개(it · meeting · other · needs input)가 `Collect results` 입력 0~3으로 |

- 다시 모이는 노드: 두 번째부터는 펼치지 않고 `↩ Send result (위에 있음)`처럼 표시하면 충분.
- mermaid id: `n0`, `n1` … 처럼 번호로, 보이는 이름은 `n3["Has question?"]`. 갈래 이름은 `-->|true|`.

## 단계별 요청문 예

### 1. 글자로 트리와 mermaid

```text
~/vibe/tflow 에 Python 프로젝트를 만들어 줘. uv 사용, 패키지·명령 이름 tflow, 코드와 화면 글자는 영어(설명만 한국어).
이번 단계는 TUI 없이 글자 출력만.
1. tflow/model.py: n8n 워크플로우 JSON을 읽어 Node(name, type, parameters)와 Link(source, target, kind, output_index) 목록으로.
   kind는 main, ai_languageModel, ai_tool 등 connections의 키. output_index는 바깥 목록 순서.
2. tflow/tree.py: 웹훅(또는 들어오는 main 연결이 없는 노드)에서 main을 따라가는 트리 글자.
   If는 0=true 1=false, Switch는 parameters.rules.values[i].outputKey 를 갈래 이름으로. 이미 나온 노드는 "↩ 이름 (above)"로 한 줄만.
   ai_* 연결은 받는 Agent 아래에 "◇ model …", "◇ tool …"로.
3. tflow/mermaid.py: flowchart LR. id는 n0, n1…, 보이는 이름은 따옴표 안에, 갈래 이름은 화살표 글자, ai 연결은 점선(-.->).
4. tflow <파일> 은 트리, tflow <파일> --md 는 <파일 이름>.md 를 만든다 (--out 으로 경로 지정).
   내용: "# <워크플로우 이름>", "노드 N · 연결 M" 한 줄, 그리고 ```mermaid 블록.
5. pytest: 테스트용으로 ~/aio-01d4-stu/Last3Mon/68/agents/it-agent.json 을 tests/data 에 복사해 두고
   노드 14, main 연결 11, ai_languageModel 1, ai_tool 2 를 확인. Send result 가 트리에 두 번 펼쳐지지 않는지 확인.
```

### 2. TUI · 상세 · 경고

```text
이제 Textual TUI를 붙여 줘. model.py 를 그대로 다시 써.
- 왼쪽 Tree 위젯(1단계 트리와 같은 모양), 오른쪽 상세 패널. 위에 경고 줄(없으면 숨김).
- 노드를 고르면 상세에 종류(type 마지막 부분)와 종류별 중요한 설정:
  webhook: httpMethod, path / httpRequest·httpRequestTool: method, url / agent: systemMessage 앞 300자, 붙은 모델·Tool
  code: jsCode 앞 10줄 / if·switch: 조건의 leftValue, operation, rightValue / set: 필드 이름과 값
- 경고: 연결이 없는 노드를 가리킴, 어디서도 들어오지 않고 웹훅도 아닌 노드(모델·Tool 제외).
- 테스트: 연결 이름 하나를 틀리게 바꾼 파일, 떨어진 노드를 더한 파일을 tests/data 에 만들고 경고를 확인.
- m 키: --md 와 같은 .md 파일을 저장하고 아래 줄에 저장 경로를 알림 (mermaid.py 를 그대로 다시 씀).
- q 로 종료. 화면 테스트는 Textual의 run_test 로 하나만.
```

### 3. 한국어 설명과 캐시

```text
상세 패널에 "하는 일:" 한국어 1~2문장을 더해 줘.
- tflow/explain.py: Explainer 인터페이스(explain(node, context) -> str). 실제 구현은 OpenAI gpt-4.1-mini, 키는 OPENAI_API_KEY 환경 변수.
  context = 워크플로우 이름, 앞 노드·뒤 노드 이름, 이 노드의 parameters (credentials 는 보내지 않음).
- 캐시: ~/.cache/tflow/explain.json, 키는 노드 type + parameters 의 sha256. 같으면 다시 묻지 않음.
- 키가 없거나 실패하면 "설명 없음 (키 없음)" 또는 "설명 실패: <짧은 이유>", 트리는 그대로.
- 설명은 백그라운드(worker)로 받아 화면이 멈추지 않게.
- 테스트는 FakeExplainer 로. 캐시에 두 번째 요청이 가지 않는지 확인.
```

## 7교시에 볼 것 (예상되는 막힘)

| 볼 것 | 막혔을 때 한마디 |
| --- | --- |
| 트리가 끝없이 길어짐 / 같은 노드 반복 | "이미 나온 노드는 한 줄로 끝내라고 하세요" |
| mermaid가 안 그려짐 | "노드 이름을 id로 쓰지 말고 번호 id" |
| 미리보기에 그림 대신 글자만 | "블록이 ` ```mermaid `로 시작하는지, 앞뒤 펜스가 맞는지" |
| TUI 안에서 그림을 그리려 함 | "터미널은 못 그립니다. `.md`로 내보내 미리보기" |
| If 갈래가 반대 | "connections main 의 0번이 true" |
| 설명이 매번 느림 | "캐시 키를 무엇으로 했는지 물어보세요" |
| Credential이 LLM으로 감 | "credentials 는 빼고 보내라고" |
