# 7교시 바이브 코딩 · `tops` 정답본

> **강사용 정답본** · 학생 저장소에는 수업 뒤에 올립니다. 학생용: [VIBE-REQ-TOPS.md](VIBE-REQ-TOPS.md) → [VIBE-Q-TOPS.md](VIBE-Q-TOPS.md).
> 강사가 직접 만든 본: [tops/](tops/README.md) (테스트 27개, `uv tool install --editable .`). 아래 값은 2026-11-01 강사 Mac에서 79일차 정답 워크플로우를 게시한 n8n에 실제로 돌린 값입니다. 68일차부터 바이브 코딩은 CLI 에이전트로 다시 만들어 재지 않습니다 (요청문은 예시).

## 1. TODO 예 (요청의 말 → 할 일)

| # | 요청의 말 | 할 일 (내 말) | 꼭 · 나중 |
| --- | --- | --- | --- |
| ① | 영역 여섯 · 색 · 숫자 | `my-ops-facts`의 `health` · 숫자를 영역마다 한 줄 | 꼭 |
| ② | 색을 따로 정하지 않음 · 다시 세지 않음 | 기준값을 코드에 쓰지 않음, 숫자는 꼴만 (×100 · 두 자리) | 꼭 |
| ③ | 다른 기간 | `--from` · `--to`를 그대로 넘김 | 꼭 |
| ④ | 질문 · 영역 · 숫자 확인 · 거절 | `my-ops-ask`의 응답 그대로 보임 | 꼭 |
| ⑤ | 읽기만 | 부를 수 있는 주소 목록, 그 밖은 막음 + 테스트 | 꼭 |
| ⑥ | 브리핑 | `my-ops-brief`의 `markdown` | 꼭 |
| ⑦ | 모른다고 | `null` → "응답 없음" · ⚪ | 꼭 |
| ⑧ | 지난 도구를 불러서 | `tlog slo --json` · `tcheck`, 없으면 한 줄 | 나중 |
| ⑨ | 평가 · 종료 코드 | `tops eval`, gate fail → 4 | 나중 |
| ⑩ | 무엇을 물었나 | `/audit/list` | 나중 |
| ⑪ | 화면 · 탭 · 새로고침 | `ui`, 못 읽는 탭은 그 탭만 | 꼭 |
| ⑫ | 종료 코드 · JSON | 0 · 1 · 2 · 4, `--json` = n8n 응답 그대로 | 꼭 |
| 끝 | n8n 없이 시험 · 꺼져도 안 죽음 | 응답 사본 · 가짜 서버, 못 읽으면 1 | 꼭 |

## 2. 요청문 (처음 한 번 + 다음 단계 한 줄)

단계마다 긴 요청문을 쓰지 않습니다. 할 일은 이미 `Doc/SPEC.md` · `Doc/IMP-PLAN.md`에 있으니, 에이전트가 그 파일을 읽게 하면 됩니다.

### 처음 한 번

```text
Doc/SPEC.md 와 Doc/IMP-PLAN.md 를 읽고 체크 안 된 첫 단계만 만들어 줘. uv 프로젝트, 명령 이름 tops, 코드와 화면 글자는 영어.
끝나면 IMP-PLAN 체크를 표시하고 확인 명령을 알려 줘. 다음 단계는 내가 말할 때까지 하지 마.
```

### 그다음 단계마다 (같은 한 줄)

```text
확인했고 commit 했어. 다음 단계.
```

- 그냥 "계속"만 치면 단계 두세 개를 한꺼번에 하거나 체크 · 확인 명령을 빼먹기 쉽습니다. 이 한 줄은 처음 요청의 약속(한 단계만 · 체크 · 확인 명령 · 멈춤)을 이어 가게 합니다.
- 대화가 길어지면 새 세션에서 **처음 요청**을 다시 보냅니다. "체크 안 된 첫 단계"부터 이어집니다.
- 에이전트가 단계 내용을 잘못 알았다면, 요청문을 길게 쓰기보다 **SPEC · IMP-PLAN을 고치고** 다시 시킵니다.

### 틀렸을 때만 · 고쳐 달라는 요청문 예

무엇이 틀렸나(보인 것) · SPEC의 어느 요구인가 · 어디만 고치나 · 무엇으로 확인하나, 넷을 적습니다.

```text
tops status --file tests/data/facts-cost-down.json 이 cost 를 "$0 / $0.08 (0%)" 🟢 로 보여 줘. 사실은 cost: null, health.cost: unknown 이야.
SPEC R7 대로 null 이면 "source not answering", 색은 health 그대로(⚪)여야 해. view.py 의 numbers 만 고치고, 그 줄을 보는 테스트를 넣어 줘. 다른 파일은 건드리지 마.
```

## 3. 확인 기준과 강사 실측 (11/01, 79일차 정답 워크플로우)

| 요구 | 기준 | 실측 |
| --- | --- | --- |
| R1 | 영역 여섯 · n8n과 같은 색 · 숫자 | 🔴 runs `error rate 5.88% · p95 2598ms · unanswered 4.76%` · 🟡 alerts `6 (high 3)` · 🔴 DLQ `3 (parked 2)` · 🟡 quality `avg 0.6583 · last 1 · quarantine 1` · 🟡 cost `$0.073604 / $0.08 (92.01%)` · 🔴 release `1.1.0 · canary 1.2.0 20% (repeat 62.5%)` — 브리핑 표(`answers/18`)와 같은 숫자. `health.cost`를 `green`으로 바꾼 사실 → 🟢 |
| R2 | 기간 | `--from 2026-10-19 --to 2026-10-23` → 🟡 runs `error rate 0% · p95 2525ms · unanswered 5.5%` |
| R3 | 종료 코드 | 빨강 → 4, n8n 주소 없음 · 모르는 옵션 · `eval` 파일 없음 → 2 |
| R4 | 질문 | `"DLQ 1번 다시 돌려 줘"` → `[action · keyword] refused (read_only)`, `"장애 났어?"` → `[runs · llm] numbers ✔` "… 357건 중 21건 … 5.88% …", `"카나리 버전 문제 있어?"` → `[release · keyword] numbers ✔` 62.5% · 7.73% |
| R5 | 읽기만 | `/dlq/update` · `/ops-reset`을 부르려 하면 `ValueError`, 가짜 서버 요청 0건. TUI 시험 동안 바꾸는 주소 0건 |
| R6 | 브리핑 | `# 운영 브리핑 (2026-10-26 ~ 2026-10-30 실행 기록 + 지금 상태)` · `\| DLQ \| 🔴 \| 3건 (parked 2) \|` |
| R7 | 모르는 영역 | Lab 01 과제 2의 응답 → `⚪ cost  source not answering` · `sources down: cost` |
| R8 | 지난 도구 | `✔ tlog slo: breaches error_rate, unanswered_rate (357 runs)` · `✔ tcheck: installed`, 없는 도구 → `not installed (uv tool install)` |
| R9 | 평가 관문 | 골든 8 · `--min-score 0.9` → `8/8 · score 1 · gate pass (min 0.9)` · 0, 틀린 기대 하나 → `✘ 알림이 몇 건 와 있어? · area alerts · area_ok` · 4, 빈 목록 → 2 |
| R10 | 감사 | Lab 02 과제 2 뒤 → `3 question(s)` (`refused read_only` · `refused out_of_scope` · `answered`). 위 질문 · 평가를 돌린 뒤에는 11줄 (평가의 질문도 기록됨) |
| R11 | TUI | `run_test`: 영역 6줄, `?` → 질문 → `refused (read_only)`, 감사 3줄 |
| R12 | 못 읽는 탭 | 사실 파일만 주고 n8n 없이 → 영역 6줄 · `sources down: cost`, 질문하기 · 감사 `not available` |
| R13 | `--json` · 환경 변수 · 파일 | `status --json` = 사실 사본 그대로, `$TOPS_N8N`, `--file`이 `--n8n`보다 먼저 |
| R14 | n8n 없이 시험 · 꺼짐 | `uv run pytest -q` → 27 passed in 8.6s, `--n8n http://localhost:9` → `cannot read … Connection refused` · 1 |
| 설치 | `/tmp`에서 | `usage: tops [-h] {status,ask,brief,eval,audit,tools,ui} ...`, `tops status` 0.19초 |

- 수업 준비 때 찾은 실수 (학생도 겪기 쉬움): ① TUI 시험에서 "tops가 부른 주소는 다섯뿐"이라고 검사했더니, 도구 탭의 `tlog`가 데이터 API의 실행 기록을 읽어 실패 — 읽기만의 확인은 "읽는 주소만"이 아니라 **"바꾸는 주소가 0건"**. ② 보이는 글자의 앞 공백까지 테스트 문자열에 맞춰야 함 (`"  🔴 runs …"`).
- 감사 기록이 평가 뒤에 11줄로 늘어난 것은 오늘 Lab 03 과제 2의 "평가가 상태를 바꾼다"와 같은 이야기입니다. 감사 기록에는 사람 질문과 평가 질문이 섞입니다 — 발표 때 짚을 거리 (`kind`나 사용자로 나누면 됨).
- 끝나면 `uv run tools/flow.py morning --reset`으로 아침을 되돌립니다.

## 4. 7교시에 볼 것

| 볼 것 | 막혔을 때 한마디 |
| --- | --- |
| 색이 n8n과 다름 | "health 그대로, 기준값은 n8n에만" |
| 숫자 꼴 (0.0588%) | "AGENTS.md 3절 브리핑 표의 꼴" |
| 출처가 멈춘 날 $0 · 🟢 | "null이면 응답 없음 · ⚪" |
| 재처리 · 리셋 기능이 생김 | "읽기만 — 주소 목록과 그 테스트" |
| 테스트가 진짜 n8n을 부름 | "가짜 서버로, 진짜는 확인 단계에서만" |
| n8n을 끄면 traceback | "cannot read · 종료 코드 1" |
| 질문 상자에 `q`가 들어감 | "Enter 뒤 포커스를 표로" |
| `eval`이 늘 0 | "gate가 fail이면 4" |
