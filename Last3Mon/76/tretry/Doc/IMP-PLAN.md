# tretry IMP-PLAN

## 엔진 1단계 · 다시 하기 · 대체 · 종료 코드 (R1 · R2 · R3 · R4 · R12 · R13)
- [x] retry.py: `Policy(tries, backoff, max_wait, jitter, deadline)`, `wait(i) = min(backoff × 2^(i-1), max_wait) × (1 - jitter × 무작위)`
- [x] `run_with_retry(attempt, policy, fallback, per_try_timeout, sleep, clock, rand)` → `Result(ok, output, attempts, stopped, used_fallback, seconds)`
- [x] `Outcome(ok, retryable, error, output, status, retry_after)`: 다시 할 수 있나는 실행기가 정함
- [x] runners.command(argv): 종료 코드 ≠ 0 · 시간 초과 → 다시, 명령 없음 → 다시 안 함
- [x] cli: `tretry [옵션] -- <명령>`, 종료 코드 0 · 1 · 2 · 3, `--json`
- [x] tests: 가짜 시계 [0.5, 1.0], 상한 1 · 2 · 4 · 4, jitter, 대체, 다시 못 함은 1번 · 대체 안 함
- 확인: `uv run pytest -q`, `uv run tretry --tries 3 --backoff 0.2 -- false; echo $?`

## 엔진 2단계 · HTTP · 멱등 키 · 기록 (R5 · R6 · R8)
- [x] runners.http(method, url, body, headers, idem_key, body_key): 2xx 성공 · 5xx · 408 · 425 · 429 · 시간 초과 · 연결 실패 다시 · 그 밖 4xx 다시 안 함, `Retry-After`
- [x] `--idem-key auto|값`: 실행에 한 번 만들어 헤더 `Idempotency-Key`, `--body-key`면 본문에도
- [x] log.py: JSON Lines `~/.tretry/log.jsonl` (`--log`, `$TRETRY_LOG`), 시도마다 한 줄, 키 · 토큰은 `***`
- [x] tests: 가짜 서버 500 → 201 · 400 · 느림, 같은 키 3번, 기록에 `secret123` · `sk-` 없음
- 확인: 데이터 API `flaky`에서 `tretry http POST .../tickets --idem-key x --body-key key`

## TUI 1단계 · 기록 보기 (R11)
- [x] app.py `LogApp`: 왼쪽 대상 순위(실패한 시도 많은 순), 고르면 오른쪽에 그 대상의 시도, `[f]` 실패만, `[r]` 다시 읽기
- [x] 엔진(`log.stats` · `log.runs`)을 불러 쓰기만
- [x] tests: `run_test`로 두 표 · `down` · `f`
- 확인: `uv run tretry log`

## 설치 (R14)
- [x] `[project.scripts] tretry = "tretry.cli:main"`
- [x] `uv tool install --editable .`, `/tmp`에서 `tretry --help`

## 엔진 3단계 · 마감 · 순위 · 회로 차단 (R7 · R9 · R10)
- [x] `--deadline`: 시도 전 남은 시간, 마감을 넘는 기다림은 하지 않음, 마지막 시도의 시간 제한을 남은 시간으로
- [x] `tretry stats [--json]`: 대상마다 runs · 성공률 · 실행당 시도 · 실패한 시도 · 대체 · p95
- [x] `--breaker N`(기본 5, 0 끔): 최근 60초 그 대상의 시도(대체 제외) N개가 모두 실패면 바로 대체, 대체가 없으면 멈춤
- [x] tests: 3초 시도 · 마감 7 → 2번, 마감이 시간 제한을 줄임, 실패 5번 뒤 바로 대체, stats 숫자
