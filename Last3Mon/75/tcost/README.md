# tcost · 강사가 수업 준비 때 직접 만든 본 (2026-10-28)

> **정답 자료** · 학생 저장소에는 수업 뒤 [VIBE-A-TCOST.md](../VIBE-A-TCOST.md)와 함께 올립니다.
> 이 본은 강사가 CLI 에이전트에 단계 요청문을 보내 만든 것이 아니라, Claude Code가 VIBE-A의 SPEC · IMP-PLAN을 보고 직접 썼습니다. 학생이 만든 것과 파일 구성이 달라도 됩니다. 요구 R1~R14의 **확인 방법**이 같으면 됩니다.

## 설치 · 실행

```bash
cd ~/aio-01d4-stu/Last3Mon/75/tcost
uv sync && uv run pytest -q              # 테스트 13개 (API를 부르지 않음)
uv tool install --editable .             # 어느 폴더에서나 tcost (R14)
cd /tmp && tcost --help
```

| 하고 싶은 것 | 명령 |
| --- | --- |
| 글 파일의 토큰 · 비용 | `tcost count prompt.txt --out 100` (폴더면 `.txt` · `.prompt`만) |
| 워크플로우의 LLM 단계 | `tcost workflow reference/baseline-cost.json` |
| 보고서의 실제 사용량 · 한 달 | `tcost usage runs --per-day 1000 --days 22` |
| 두 모델 비교 | `tcost compare prompt.txt --model gpt-4.1-mini --model gpt-5.4-nano --out 100` |
| 예산으로 하루 몇 번 | `tcost budget 1.0 prompt.txt --out 100` |
| 폴더에서 찾은 것 | `tcost scan .` |
| 화면(TUI) | `tcost reference my-work runs` (폴더 여럿, `[r]` 다시 읽기, `[q]` 끝) |
| 비용 관문 | `tcost count prompt.txt --out 200 --max-usd 0.0002; echo $?` (넘으면 1) |

- 단가: `--prices <파일>`, `$TCOST_PRICES`, `~/.tcost/prices.json`, 없으면 함께 든 `src/tcost/prices.json` (2026-10-28 확인). 확인한 지 30일이 넘으면 알림.
- 종료 코드: 0 괜찮음 · 1 `--max-usd`를 넘음 · 2 오류 (파일이 없음 · 모르는 모델 · 워크플로우가 아님).
- 토큰은 이 컴퓨터에서 셉니다 (tiktoken `o200k_base`). OpenAI가 세는 값과 조금 다를 수 있습니다.

## 파일

| 파일 | 하는 일 | 요구 |
| --- | --- | --- |
| `src/tcost/prices.py` · `prices.json` | 단가표(날짜 · 출처), 비용 식, 오래됨 알림, 모르는 모델 | R1 · R2 · R3 · R12 |
| `src/tcost/tokens.py` | 토큰 세기 (API 없이) | R1 · R13 |
| `src/tcost/workflow.py` | 워크플로우의 LLM 단계 · 고정 지시문 | R4 |
| `src/tcost/usage.py` | 보고서 모으기 · 한 달 | R5 · R6 |
| `src/tcost/scan.py` | 폴더 나누기 | R11 |
| `src/tcost/cli.py` | 명령 · `--json` · `--max-usd` · 종료 코드 | R7 · R9 · R10 |
| `src/tcost/app.py` | Textual 화면 | R8 |
| `tests/` | baseline · lean 워크플로우와 작은 보고서(`tests/data`, 비밀 없음) | |
| `Doc/IMP-PLAN.md` | 만든 순서 (엔진 1 → 2 → TUI 1 → 설치 → 엔진 3 · 4) | |

## 2026-10-28에 확인한 것

| 확인 | 결과 |
| --- | --- |
| `uv run pytest -q` | 13 passed |
| `tcost workflow reference/baseline-cost.json` | `Answer` 지시문 **1,670토큰** (n8n이 잰 답 단계 입력 1,781 중 고정 몫) |
| `tcost workflow answers/75-lab02-challenge2-long-question.json` | `Answer` 75토큰 · 출력 상한 200 |
| `tcost usage answers --per-day 1000` | 보고서 23개 · 요청 82 · $0.038746 · skipped 26 |
| 긴 프린터 질문(6,298자)만 `count --out 60` | 2,613토큰 · mini $0.001141 (n8n 실제 $0.001196), `--max-usd 0.0003` → 종료 코드 1 |
| `tcost count x --model gpt-4.1-nano` | `unknown model 'gpt-4.1-nano'`, 종료 코드 2 |
| `uv tool install --editable .` → `/tmp`에서 `tcost --help` | 됨 |
