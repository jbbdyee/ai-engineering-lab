# 66일차 실습 준비 · 수업 전에 미리 해 두면 좋은 것

- 수업일: 2026-10-16 (66일차) · 바이브 코딩으로 만드는 단일 업무 자동화 워크플로우 (오늘부터 CLI 코딩 에이전트로 n8n을 만듭니다)
- 준비 시간: 약 20분
- 먼저 WSL에서 `cd ~/aio-01d4-stu && git pull`로 오늘 자료를 받습니다 (수강생 저장소: https://gl.isitsoft.kr/publicproj/aio-01d4-stu).
- **수업 전날까지** 1~3절을 끝내 주세요.

```mermaid
flowchart LR
  A["1. n8n 켜기"] --> B["2. CLI 코딩 에이전트<br/>설치 · 로그인"] --> C["3. doctor<br/>ready"] --> D["4. 미리 읽기"]
```

---

## 1. n8n 켜기 (전날 필수, 3분)

65일차에 설치한 n8n을 그대로 씁니다.

| 무엇 | 어디 |
| --- | --- |
| n8n 공식 설치 (compose.yml · .env) | `~/day65-n8n` (65일차 [SETUP-N8N](../../Last3Mon/65/SETUP-N8N.md) 5단계, 지우지 않음) |
| 켜고 끄기 (n8n) | `~/aio-01d4-stu/Last3Mon/65/n8n` (`~/day65-n8n/compose.yml`을 불러 씀) |

```bash
sudo systemctl disable --now ollama 2>/dev/null   # WSL에 설치한 Ollama가 있으면 끄고 자동 시작도 끔
cd ~/aio-01d4-stu/Last3Mon/65/n8n
docker compose rm -sf ollama                      # Ollama 컨테이너가 있으면 지움 (없으면 그냥 지나감)
docker compose start
```

- **66일차부터 LLM은 OpenAI API 키(`Last3Mon/.env`, Credential `OpenAI (.env)`)만 씁니다.** Ollama는 쓰지 않으므로 위처럼 꺼서 메모리를 아낍니다. 다음 날부터는 같은 명령을 그대로 써도 됩니다.
- `~/day65-n8n`에서 `docker compose start`로 켰어도 n8n은 같은 것입니다.
- `docker compose start`가 `.../day65-n8n/compose.yml: no such file or directory`이면 n8n을 홈이 아닌 곳에 설치한 것입니다. 65일차 SETUP-N8N 문제 해결 표대로 `Last3Mon/65/n8n/.env`에 `N8N_HOME=<설치 폴더>`를 적습니다 (`flow.py`도 이 값을 읽습니다).

## 2. CLI 코딩 에이전트 (전날 필수, 10분)

아래 중 **하나 이상**이 WSL 터미널에서 실행되고 로그인되어 있어야 합니다.

| 에이전트 | 실행 | 확인 |
| --- | --- | --- |
| Codex CLI | `codex` | `codex --version` |
| Claude Code | `claude` | `claude --version` |
| Antigravity CLI | `agy` | `agy --version` |

- 처음 실행하면 브라우저 로그인 안내가 나옵니다. 끝까지 진행한 뒤 아무 질문("안녕")이나 해서 답이 오는지 봅니다.
- 설치가 안 되어 있으면 IT 문의 시간에 강사에게 알려 주세요.

## 3. 준비 확인 (전날 필수, 3분)

```bash
cd ~/aio-01d4-stu/Last3Mon/66
uv run tools/flow.py doctor
```

```text
✔ n8n install folder /home/<사용자>/day65-n8n
✔ n8n container day65-n8n-n8n-1
✔ n8n http://localhost:5678
! data API http://localhost:8800 (not used today)
✔ credential 'OpenAI (.env)' (openAiCourse0001)
✔ node catalog (for check)
✔ CLI coding agent: codex, claude
ready
```

| ✘ 항목 | 할 일 |
| --- | --- |
| ! n8n install folder | `~/day65-n8n`에 `compose.yml`이 없음. 다른 곳에 설치했다면 `N8N_HOME=<폴더> uv run tools/flow.py doctor` (경고만, n8n이 켜져 있으면 실습 가능) |
| n8n container | 1절 n8n 켜기. `flow.py`는 Docker 프로젝트 `day65-n8n`의 n8n 컨테이너를 자동으로 찾습니다. 그래도 못 찾으면 `N8N_CONTAINER=<이름>` (`docker ps`로 확인) |
| credential | `cd ~/aio-01d4-stu/Last3Mon/65/n8n && bash register-credentials.sh` |
| CLI coding agent | 2절 |

---

## 4. 미리 읽어 오면 좋은 내용 (선택, 약 5분)

### 4.1 n8n 워크플로우는 JSON 파일이다

64·65일차에 화면에서 만든 워크플로우는 **Download**하면 JSON 파일입니다. 노드 목록(`nodes`)과 연결(`connections`)이 들어 있습니다. 오늘부터는 이 파일을 **CLI 코딩 에이전트가 씁니다.** 우리는 무엇을 만들지(요청문)와 무엇이 맞는 결과인지(테스트)를 정합니다.

### 4.2 오늘의 회의록

`cat ~/aio-01d4-stu/Last3Mon/66/requests/weekly.json` — 이 회의록에서 할 일이 몇 개인지, 담당자와 기한이 없는 할 일은 무엇인지 미리 세어 옵니다.

### 4.3 JSON 객체 · 목록

| 모양 | 예 |
| --- | --- |
| 객체 | `{"owner": "이준호", "due": "금요일"}` |
| 목록 | `[{"owner": "이준호"}, {"owner": "박서연"}]` |
| 글자 속의 JSON | `"{\"owner\": \"이준호\"}"` — LLM의 답은 이 모양 (읽어야 객체가 됨) |

## 5. 당일 준비물

- 충전된 노트북과 충전기, WSL의 Docker, Windows Terminal(WSL) 창 **두 개**, 웹 브라우저

## 확인

- [ ] http://localhost:5678 이 열린다
- [ ] `codex` / `claude` / `agy` 중 하나에 로그인하고 답을 받았다
- [ ] `uv run tools/flow.py doctor` → 마지막 줄 `ready`
