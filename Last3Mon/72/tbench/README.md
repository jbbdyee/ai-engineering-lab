# tbench · 강사가 수업 준비 때 직접 만든 본 (2026-10-26)

> **정답 자료** · 학생 저장소에는 수업 뒤 [VIBE-A-TBENCH.md](../VIBE-A-TBENCH.md)와 함께 올립니다.
> 이 본은 강사가 CLI 에이전트에 단계 요청문을 보내 만든 것이 아니라, Claude Code가 VIBE-A의 SPEC · IMP-PLAN을 보고 직접 썼습니다. 학생이 만든 것과 파일 구성이 달라도 됩니다. 요구 R1~R14의 **확인 방법**이 같으면 됩니다.

## 설치 · 실행

```bash
cd ~/aio-01d4-stu/Last3Mon/72/tbench
uv sync && uv run pytest -q              # 가짜 서버 테스트 12개 (진짜 헬프데스크를 부르지 않음)
uv tool install --editable .             # 어느 폴더에서나 tbench (R14)
cd /tmp && tbench --help
```

| 하고 싶은 것 | 명령 |
| --- | --- |
| 화면(TUI)으로 재기 | `tbench http://localhost:5678/webhook/my-helpdesk --body-file requests/faq-vpn-nocache.json -n 20` |
| 글자로 · 저장 · 기준 | `tbench <url> --body-file x.json -n 10 --plain --save --max-p95 2.5 --max-failures 0` |
| 요청 고르기 | `tbench <url> --pick requests` |
| 동시에 · 미리 부르기 | `--concurrency 3` · `--warmup 1` |
| 키 머리글 | `--header 'Authorization: Bearer $MY_KEY'` (저장 · 기록에는 `***`) |
| 비교 · 목록 | `tbench compare a.json b.json` · `tbench history` |
| 설정 저장 · 부르기 | `tbench profile save vpn <url> --body-file requests/faq-vpn-nocache.json -n 10` · `tbench profile list` · `tbench run vpn --plain` |
| 한 번마다 한 줄 | `--log runs.jsonl` |

저장 위치는 `~/.tbench/` (`results/`, `profiles.toml`). 테스트는 `TBENCH_HOME`을 임시 폴더로 바꿔 씁니다.

## 파일

| 파일 | 하는 일 |
| --- | --- |
| `src/tbench/runner.py` | 엔진: 한 번 부르기(시간 · 상태 · 실패 종류 · `timings`), `run()` 제너레이터 (warmup · 동시) |
| `src/tbench/stats.py` | nearest-rank 백분위, 요약, 기준 검사(PASS · FAIL) |
| `src/tbench/store.py` | 저장(조건 · 본문 해시 · 키 가리기), compare, history, 기록 줄 |
| `src/tbench/profiles.py` | `~/.tbench/profiles.toml` |
| `src/tbench/cli.py` | 명령줄, `--plain` 출력, 종료 코드 |
| `src/tbench/app.py` | Textual 화면 (worker + `call_from_thread`), `--pick` 고르기 |
| `tests/conftest.py` | pytest 안의 가짜 서버 (지연 · N번째마다 500 · 첫 응답만 느림 · 상태 코드 · `timings`) |
