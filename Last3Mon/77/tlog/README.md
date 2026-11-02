# tlog · 강사가 수업 준비 때 직접 만든 본 (2026-10-31)

> **정답 자료** · 학생 저장소에는 수업 뒤 [VIBE-A-TLOG.md](../VIBE-A-TLOG.md)와 함께 올립니다.
> 이 본은 강사가 CLI 에이전트에 단계 요청문을 보내 만든 것이 아니라, Claude Code가 VIBE-Q의 요구 R1~R14와 [Doc/IMP-PLAN.md](Doc/IMP-PLAN.md)를 보고 직접 썼습니다. 학생이 만든 것과 파일 구성이 달라도 됩니다. 요구의 **확인 방법**이 같으면 됩니다.

## 설치 · 실행

```bash
cd ~/aio-01d4-stu/Last3Mon/77/tlog
uv sync && uv run pytest -q              # 테스트 23개 (n8n · 데이터 API 없이, 가짜 서버)
uv tool install --editable .             # 어느 폴더에서나 tlog (R14)
cd /tmp && tlog --help
```

| 하고 싶은 것 | 명령 |
| --- | --- |
| 지표 (n8n `my-log-report`와 같은 숫자) | `tlog summary --url http://localhost:8800 --from 2026-10-26 --to 2026-10-30` (`--json`) |
| 파일에서 | `tlog summary --file ../data-api/data/run-logs.json --from 2026-10-19 --to 2026-10-30` |
| 실패 묶음 · 답 못 한 주제 · 이상 시간대 · 다시 묻는 주제 | `tlog problems …` |
| SLO 판정 (위반이면 종료 코드 4) | `tlog slo … [--error-rate 0.01 --p95 3000 --unanswered 0.02]` |
| 지난 기간과 나란히 | `tlog compare … --prev-from 2026-10-19 --prev-to 2026-10-23` |
| 주간 보고 마크다운 | `tlog weekly … --prev-from … --prev-to …` |
| 76일차 tretry 기록 | `tlog summary --file ~/.tretry/log.jsonl` |
| 화면(TUI) | `tlog ui …` (`[t]` 실패 · 시간대 · 느린 실행, `[r]` 다시 읽기, `[q]` 끝) |

- 종료 코드: 0 됨 · 1 로그를 못 읽음 · 2 쓰는 법이 틀림 · 4 SLO 위반.
- 데이터 API 주소는 `--url` 또는 `$TLOG_URL`. `--file`을 주면 파일이 먼저입니다.
- 지표 정의는 [AGENTS.md](../AGENTS.md) 3절과 같습니다 (날짜 포함, 소수 4자리 half up, p95 = `ceil(p × n)`번째, `null` 갈래는 `오류`, 0건이면 0).

## 파일

| 파일 | 하는 일 | 요구 |
| --- | --- | --- |
| `src/tlog/load.py` | 파일 · 데이터 API 읽기, 거르기(날짜 포함), tretry 기록을 실행 모양으로 | R1 · R9 |
| `src/tlog/metrics.py` | 정의대로 세기 (요약 · 단계 · 비용 · 문제 · 이상 · SLO · 비교 · 주간 보고) — **정의는 여기 한 곳** | R2 · R3 · R4 · R6 · R7 · R8 · R10 |
| `src/tlog/cli.py` | 명령 · `--json` · 종료 코드 | R5 · R12 |
| `src/tlog/app.py` | Textual 화면 | R11 |
| `tests/` | 두 주 기록 사본(`tests/data/run-logs.json`) · 가짜 데이터 API · 화면 `run_test` | R13 |
