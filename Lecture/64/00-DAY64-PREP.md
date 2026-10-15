# 64일차 실습 준비 · 수업 전에 미리 해 두면 좋은 것

- 수업일: 2026-10-14 (64일차) · AI 워크플로우 개념 및 구성 요소 이해
- 준비 시간: 약 1시간 (대체용 Ollama 모델을 새로 받는 경우. 이미 있으면 약 30분)
- **가장 먼저 0절(수업 저장소 받기)** 을 하고, **수업 전날까지** 1~2절을 끝내 주세요. 3~4절은 시간이 될 때 읽어 오면 수업이 훨씬 쉬워집니다.

```mermaid
flowchart LR
  Z["0. 수업 저장소 받기<br/>git clone"] --> A
  A["1. 실습 환경<br/>WSL · uv · API 키<br/>(대체: Ollama)"] --> B["2. 확인 명령<br/>pytest · check"]
  B --> C["3. 미리 읽기<br/>JSON · 지난 실습"]
  C --> D["4. 생각해 오기<br/>내 업무 시나리오"]
```

---

## 0. 가장 먼저: 수업 저장소 받기 (2분)

실습 코드와 안내 문서는 모두 공개 저장소 **https://gl.isitsoft.kr/publicproj/aio-01d4-stu** 에 있습니다. 공개(public) 저장소라 **계정·로그인 없이 누구나** 받을 수 있습니다. WSL(Ubuntu) 터미널을 열고 홈 폴더에서 아래 명령을 실행합니다.

```bash
cd ~
git clone https://gl.isitsoft.kr/publicproj/aio-01d4-stu.git
cd ~/aio-01d4-stu && ls          # Last3Mon  Lecture 가 보이면 성공
```

- 이 문서와 앞으로의 안내에 나오는 폴더는 모두 `~/aio-01d4-stu` 기준입니다.
- 앞으로 **매일 수업 전**에 `cd ~/aio-01d4-stu && git pull`로 새 자료를 받습니다.
- 사용자 이름·비밀번호를 묻는다면 주소 오타입니다. 주소를 다시 확인하세요. `git: command not found`가 나오면 `sudo apt update && sudo apt install -y git` 후 다시 실행합니다.
- WSL이 아직 준비되지 않았다면 안내서 1절(WSL 확인)을 먼저 한 뒤 이 명령을 실행합니다.

## 1. 실습 환경 준비 (전날 필수, 약 40분)

오늘 실습은 Windows 11 노트북의 **WSL(Ubuntu)** 에서 진행합니다. LLM은 과정에서 받은 키로 **OpenAI API**(`gpt-4.1-mini`)를 씁니다. 이 구성은 65일차 이후에도 그대로 씁니다.

**Ollama는 대체용입니다.** OpenAI API 키가 작동하지 않을 때(키 오류, 사용 한도 초과, 인터넷 끊김)만 노트북에서 직접 실행하는 Ollama(`gemma3:4b`)가 대신 답합니다. 평소 실습에는 쓰지 않지만, 수업 중에 키가 막히면 바로 넘어갈 수 있도록 **전날 미리 준비해 둡니다**.

```mermaid
flowchart LR
  W["워크플로우의 LLM 노드"] -->|"기본"| O["OpenAI API<br/>gpt-4.1-mini"]
  W -.->|"키가 작동하지 않을 때만"| L["Ollama (노트북)<br/>gemma3:4b / gemma3:1b"]
```

자세한 순서는 **[사전 준비 안내 (SETUP-WSL-LLM)](../../Last3Mon/64/SETUP-WSL-LLM.md)** 를 따라 하세요. 할 일만 요약하면 다음과 같습니다.

| 순서 | 할 일 | 시간 |
| --- | --- | --- |
| 1 | WSL(Ubuntu) 동작 확인 | 5분 |
| 2 | uv 설치 (수업 저장소는 0절에서 이미 받음) | 10분 |
| 3 | `Last3Mon/.env`에 OpenAI API 키 넣기 | 3분 |
| 4 | 노트북 메모리 확인 → 대체 모델 결정 (8GB: `gemma3:1b`, 16GB 이상: `gemma3:4b`) | 2분 |
| 5 | (대체용) Ollama가 이미 있는지 확인 → 없을 때만 설치와 모델 다운로드 | 1분 / 10~20분 |
| 6 | 연결 확인 (OpenAI, 대체 Ollama) | 5분 |

### 5단계 전에: Ollama를 이미 쓸 수 있는지 먼저 확인

8~9월 Ollama 실습에서 이미 설치해 둔 분이 많습니다. 새로 설치하기 전에 WSL 터미널에서 아래 명령으로 확인합니다.

```bash
ollama --version     # 버전이 나오면 Ollama 설치됨
ollama list          # gemma3:4b (8GB 노트북은 gemma3:1b)가 보이면 모델도 준비됨
```

| 결과 | 할 일 |
| --- | --- |
| 버전과 모델이 모두 보임 | 설치·다운로드를 건너뛰고 6단계(연결 확인)로 |
| 버전은 나오지만 모델이 없음 | 모델만 받기: `ollama pull gemma3:4b` (8GB 노트북은 `gemma3:1b`) |
| `command not found` | 안내서 5절대로 설치. 단, Windows나 Docker에 Ollama가 이미 있으면 안내서 7절을 먼저 확인 |
| `ollama list`에서 연결 오류 | 다른 터미널에서 `ollama serve` 실행 후 다시 확인 |

> 설치·다운로드가 필요한 경우, Ollama 모델 파일이 1~3GB라서 수업 중에 여러 명이 동시에 받으면 강의실 네트워크가 매우 느려집니다. **다운로드는 꼭 집에서 미리** 해 주세요.

## 2. 준비가 끝났는지 확인 (전날 필수, 5분)

WSL 터미널에서 실습 폴더로 이동해 아래 두 명령을 실행합니다.

```bash
cd ~/aio-01d4-stu/Last3Mon/64/workflow-lab
uv run pytest -q          # 18 passed, 1 skipped 가 나오면 성공
uv run miniflow check     # Reply (openai, ...) 가 나오면 성공
OPENAI_API_KEY=sk-wrong uv run miniflow check   # Reply (ollama, ...) 가 나오면 대체도 준비 완료
```

| 결과 | 의미 |
| --- | --- |
| 세 명령 모두 성공 | 준비 완료 |
| `pytest`는 성공, 첫 `check`가 실패 | `.env`의 키 문제. 안내서 8절(문제 해결) 확인 |
| 첫 `check`는 성공, 두 번째가 실패 | 대체용 Ollama 문제. 수업은 OpenAI로 할 수 있으니 1교시 전에 말씀해 주세요 |
| 모두 실패 | uv 또는 저장소 위치 문제. 안내서 2절부터 다시 확인 |

해결이 안 되면 수업 당일 1교시 전에 말씀해 주세요. 키를 아직 못 받았으면 `.env`의 `MINIFLOW_LLM=ollama`로, 둘 다 안 되면 `export MINIFLOW_LLM=mock`으로 Mock LLM을 써서 실습을 따라올 수 있습니다.

---

## 3. 미리 읽어 오면 좋은 내용 (선택, 약 15분)

### 3.1 JSON 기초: 오늘 워크플로우를 적는 형식

오늘 실습에서는 워크플로우를 **JSON** 파일로 적습니다. JSON은 데이터를 "이름: 값" 짝으로 적는 형식입니다. 지난 실습에서 FastAPI 요청·응답이나 Pydantic 모델로 이미 여러 번 본 형식입니다.

```json
{
  "name": "날씨 안내",
  "inputs": ["city"],
  "nodes": [
    {"id": "start", "type": "input"},
    {"id": "weather", "type": "tool", "tool": "get_weather", "args": {"city": "{{input.city}}"}}
  ],
  "edges": [["start", "weather"]]
}
```

| 기호 | 뜻 | 위 예시에서 |
| --- | --- | --- |
| `{ }` | 객체: "이름": 값 짝의 묶음 | 노드 하나 `{"id": "start", ...}` |
| `[ ]` | 목록: 여러 값을 순서대로 | `"nodes": [ ... ]` 노드 목록 |
| `"이름": 값` | 이름과 값 한 쌍 | `"type": "tool"` |
| `,` | 항목 사이 구분 | 마지막 항목 뒤에는 쓰지 않음 |

자주 하는 실수

- 문자는 반드시 **큰따옴표** `"`로 감쌉니다. 작은따옴표 `'`는 JSON에서 쓸 수 없습니다.
- 마지막 항목 뒤에 쉼표를 붙이면 오류가 납니다. `{"a": 1, "b": 2,}` (X)
- 괄호 `{ }`, `[ ]`의 짝이 맞아야 합니다. VS Code에서 괄호를 클릭하면 짝이 강조됩니다.

### 3.2 지난 실습 떠올리기

오늘 배우는 노드는 모두 지난 3개월 동안 코드로 만들어 본 것들입니다. 아래 표의 실습을 한 번 떠올려 보세요.

| 오늘의 노드 | 지난 실습 | 떠올릴 것 |
| --- | --- | --- |
| LLM 노드 | 10일차 LLM API(OpenAI/Anthropic/Gemini) 호출, 27일차 Structured Output | 프롬프트를 보내고 답을 받는 흐름, 정해진 형식으로 답 받기 |
| Tool 노드 | 29~31일차 Tool Use·MCP (`mini_agent_03_tool`, `mini_agent_03_mcp`) | 외부 기능(날씨 조회 등)을 호출해 결과를 받는 흐름 |
| Memory 노드 | 35·39일차 Memory (`mini_agent_05_memory`) | 사용자 선호·이력을 저장하고 다음 요청에 다시 쓰는 흐름 |
| 실행 순서·병렬 | 48일차 분산 협업 (`mini_multi_agent_04`) | 여러 Agent를 동시에 실행하고 결과를 합치는(Join) 흐름 |
| 로컬 LLM | 8~9월 Ollama 실습 (`llama3.2`, `gemma3:4b`) | 노트북에서 모델을 실행하는 방법 |

### 3.3 용어 미리 보기

| 용어 | 한 줄 뜻 |
| --- | --- |
| 워크플로우 | 업무를 정해진 순서의 단계로 나누어 실행하는 흐름 |
| 노드 | 워크플로우에서 한 가지 일을 하는 단계 하나 |
| 연결(Edge) | 노드 사이의 실행 순서와 데이터가 지나가는 길 |
| 페이로드 | 노드 사이를 오가는 데이터 |
| 실행 기록(Trace) | 실행할 때마다 남는 노드별 입력·출력·시간 기록 |

---

## 4. 생각해 오기 (선택, 5분)

5~6교시 Lab 03에서 **업무 하나를 골라 자동화 시나리오로 분석**합니다. 아래 질문에 대한 답을 하나 생각해 오면 실습 시간을 아낄 수 있습니다.

- 학교·회사·아르바이트·일상에서 **자주 반복하는 일** 중 하나는 무엇인가요?
- 그 일은 어떤 순서로 진행되나요? (예: 메일 확인 → 내용 분류 → 자료 찾기 → 답장)
- 그중 **판단이 필요한 단계**와 **정해진 규칙대로 하는 단계**는 각각 어디인가요?

떠오르지 않으면 수업에서 제시하는 예시 시나리오 5개 중 하나를 골라도 됩니다.

---

## 5. 당일 준비물

- 충전된 노트북과 충전기 (대체용 Ollama는 배터리를 많이 사용합니다)
- Windows Terminal (WSL 터미널), VS Code
- 웹 브라우저 (워크플로우 그림 확인용 [Mermaid Viewer](https://mermaidviewer.com/ko))
- 과정에서 받은 OpenAI API 키 (`Last3Mon/.env`에 넣어 오기). 키는 채팅·문서·화면 캡처에 올리지 않습니다
- (선택) Anthropic·Gemini 키가 있으면 (예: 10일차에 발급한 Gemini 키) 같은 워크플로우를 다른 제공사 모델로도 비교해 볼 수 있습니다

## 확인

- [ ] `git clone`으로 `~/aio-01d4-stu`를 받았다
- [ ] `uv run pytest -q` → `18 passed, 1 skipped`
- [ ] `uv run miniflow check` → `Reply (openai, ...)`
- [ ] `ollama list`에 대체 모델(`gemma3:4b` 또는 `gemma3:1b`)이 보인다 (이미 있으면 새로 받지 않음)
- [ ] `OPENAI_API_KEY=sk-wrong uv run miniflow check` → `Reply (ollama, ...)`
- [ ] JSON 기초(3.1)를 읽었다
- [ ] Lab 03에서 분석할 업무 후보를 하나 생각했다
