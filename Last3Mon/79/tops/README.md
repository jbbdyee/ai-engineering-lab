# tops · 강사가 수업 준비 때 직접 만든 본 (2026-11-01)

> **정답 자료** · 학생 저장소에는 수업 뒤 [VIBE-A-TOPS.md](../VIBE-A-TOPS.md)와 함께 올립니다.
> 이 본은 강사가 CLI 에이전트에 단계 요청문을 보내 만든 것이 아니라, Claude Code가 VIBE-Q의 요구 R1~R14와 [Doc/IMP-PLAN.md](Doc/IMP-PLAN.md)를 보고 직접 썼습니다. 학생이 만든 것과 파일 구성이 달라도 됩니다. 요구의 **확인 방법**이 같으면 됩니다.

## 설치 · 실행

```bash
cd ~/aio-01d4-stu/Last3Mon/79/tops
uv sync && uv run pytest -q              # 테스트 27개 (n8n · 데이터 API 없이, 가짜 서버)
uv tool install --editable .             # 어느 폴더에서나 tops
cd /tmp && tops --help
export TOPS_N8N=http://localhost:5678
```

| 하고 싶은 것 | 명령 |
| --- | --- |
| 영역 여섯 · 색 · 숫자 (빨강이면 종료 코드 4) | `tops status` (`--from 2026-10-19 --to 2026-10-23`, `--json`, `--file 사실.json`) |
| 질문 하나 | `tops ask "카나리 버전 문제 있어?"` |
| 아침 브리핑 | `tops brief` |
| 골든 질문 평가 · 관문 (실패면 4) | `tops eval ../requests/ops-golden.json --min-score 0.9` |
| 감사 기록 | `tops audit` (데이터 API `--api` 또는 `$TOPS_API`, 기본 `http://localhost:8800`) |
| 지난 도구 | `tops tools` (`tlog slo` · `tcheck`) |
| 화면(TUI) | `tops ui` (`[r]` 새로고침, `[?]` 질문하기, `[q]` 끝) |

- 종료 코드: 0 됨 · 1 n8n이나 파일을 못 읽음 · 2 쓰는 법이 틀림 · 4 전체 빨강 / 평가 관문 실패.
- **읽기만:** `client.READ_ONLY`의 다섯 주소(`my-ops-facts` · `ask` · `brief` · `eval` 웹훅, `/audit/list`) 밖은 보내기 전에 막습니다.
- 색 · 숫자는 n8n `my-ops-facts`가 정한 그대로입니다. tops에는 기준값이 없습니다 (AGENTS.md 3절은 n8n 쪽 하나).

## 파일

| 파일 | 하는 일 |
| --- | --- |
| `src/tops/client.py` | 읽는 층 (R5 · R13 · R14): 주소 목록, 사실 · 질문 · 브리핑 · 평가 · 감사 |
| `src/tops/view.py` | 보여 주는 층 (R1 · R7 · R8): 영역 줄 · 숫자 꼴 · 답 줄 · 지난 도구 |
| `src/tops/cli.py` | `status` · `ask` · `brief` · `eval` · `audit` · `tools` · `ui`, 종료 코드 (R2 · R3 · R4 · R6 · R9 · R10) |
| `src/tops/app.py` | Textual 화면 (R11 · R12) |
| `tests/` | 정답 실행 기록(`answers/06` · `08` · `14` · `16` · `18` · `25`)의 n8n 응답 사본, 골든 질문, 가짜 n8n · 데이터 API |

## 수업 준비 때 확인한 것 (11/01)

- 실제 n8n(정답 워크플로우)에서 `tops status` → 위 일곱 줄 · 종료 코드 4, 0.19초. n8n 브리핑 표와 같은 숫자.
- `--from 2026-10-19 --to 2026-10-23` → 🟡 runs `error rate 0% · p95 2525ms · unanswered 5.5%` (Lab 01 과제 1의 첫 주와 같음).
- `tops ask "장애 났어?"` → `[runs · llm] numbers ✔` (Lab 02 과제 1의 LLM 라우터), `"DLQ 1번 다시 돌려 줘"` → `refused (read_only)`.
- `tops eval ../requests/ops-golden.json --min-score 0.9` → `8/8 · score 1 · gate pass (min 0.9)` · 종료 코드 0.
- `tops tools` → `tlog slo: breaches error_rate, unanswered_rate (357 runs)` — `tlog`(77일차)의 정의로 같은 지난주.
- 처음 판의 TUI 테스트가 "tops가 부른 주소는 다섯뿐"을 검사했는데, 도구 탭의 `tlog`도 데이터 API의 실행 기록을 읽어 실패 → "상태를 바꾸는 주소는 0건"으로 고침 (읽기만의 뜻은 '읽는 주소만'이 아니라 '바꾸는 주소 없음').
