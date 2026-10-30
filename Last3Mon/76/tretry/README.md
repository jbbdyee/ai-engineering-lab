# tretry · 강사가 수업 준비 때 직접 만든 본 (2026-10-29)

> **정답 자료** · 학생 저장소에는 수업 뒤 [VIBE-A-TRETRY.md](../VIBE-A-TRETRY.md)와 함께 올립니다.
> 이 본은 강사가 CLI 에이전트에 단계 요청문을 보내 만든 것이 아니라, Claude Code가 VIBE-Q의 요구 R1~R14와 [Doc/IMP-PLAN.md](Doc/IMP-PLAN.md)를 보고 직접 썼습니다. 학생이 만든 것과 파일 구성이 달라도 됩니다. 요구의 **확인 방법**이 같으면 됩니다.

## 설치 · 실행

```bash
cd ~/aio-01d4-stu/Last3Mon/76/tretry
uv sync && uv run pytest -q              # 테스트 17개 (기다리지 않음, 가짜 서버)
uv tool install --editable .             # 어느 폴더에서나 tretry (R14)
cd /tmp && tretry --help
```

| 하고 싶은 것 | 명령 |
| --- | --- |
| 명령을 다시 해 보기 | `tretry --tries 4 --backoff 0.5 --max-wait 8 --jitter 0.2 --timeout 10 -- <명령 ...>` |
| 다 실패하면 대신 | `--fallback "cat ~/cache/faq.json"` |
| 전체 마감 | `--deadline 5` |
| HTTP 호출 | `tretry http POST http://localhost:8800/tickets --body '{"title": "t"}' --idem-key auto --body-key key` |
| 순위 | `tretry stats` (`--json`) |
| 화면(TUI) | `tretry log` (`[f]` 실패만, `[r]` 다시 읽기, `[q]` 끝) |
| 다른 프로그램이 읽게 | `--json` |

- 종료 코드: 0 됨(대체 포함) · 1 다 실패 · 2 쓰는 법이 틀림 · 3 고칠 수 없는 실패 (HTTP 4xx, 408 · 425 · 429 빼고).
- 기록: `~/.tretry/log.jsonl` (`--log`, `$TRETRY_LOG`). 헤더 값은 남기지 않고 URL · 오류의 `sk-…` · `Bearer …` · `api_key=…`는 `***`.
- 회로 차단: 같은 대상의 최근 60초 시도(대체 제외) 5개가 모두 실패면 시도 없이 바로 대체 (`--breaker 0`은 끔). 대상은 `METHOD URL` 또는 명령 줄.

## 파일

| 파일 | 하는 일 | 요구 |
| --- | --- | --- |
| `src/tretry/retry.py` | 다시 하기 엔진 (`Policy` · `run_with_retry`), sleep · clock · 무작위를 바꿔 끼움 | R1 · R2 · R4 · R7 · R13 |
| `src/tretry/runners.py` | 한 번 해 보기: 명령(종료 코드 · 시간 초과) · HTTP(상태 코드 · `Retry-After` · 멱등 키) | R1 · R3 · R5 · R6 |
| `src/tretry/log.py` | JSON Lines 기록 · 키 지우기 · 순위 · 회로 차단 | R8 · R9 · R10 |
| `src/tretry/cli.py` | 명령 · `--json` · 종료 코드 | R12 |
| `src/tretry/app.py` | Textual 화면 | R11 |
