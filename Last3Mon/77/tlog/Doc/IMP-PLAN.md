# tlog IMP-PLAN

## 엔진 1단계 · 읽기 · 정의대로 세기 · JSON · 종료 코드 (R1 · R2 · R5 · R12 · R13)
- [x] load.py: `read(file, url, from, to, tag, source)`, 날짜 포함(`from ≤ started_at[:10] ≤ to`), JSON 목록 · `{"logs"}` · JSON Lines(반쯤 쓰인 줄은 건너뜀), 데이터 API는 `POST /logs/query`, `--file`이 `--url`보다 먼저
- [x] metrics.py: `pct`(nearest rank, `ceil(p × n)`번째) · `js_round`(half up, Math.round와 같게) · `rate`(4자리, 0건 0) · `summary`(total · errors · error_rate · p50 · p95 · by_route · by_day · by_release)
- [x] cli: `tlog summary [--json]`, 종료 코드 0 · 1(못 읽음) · 2(쓰는 법)
- [x] tests: 두 주 사본 → 666 · 21 · 0.0315 · 1205 · 2537, 둘째 주 357 · 0.0588 · 2598, 빈 기간 0, 가짜 데이터 API
- 확인: `uv run pytest -q`, `uv run tlog summary --file tests/data/run-logs.json --from 2026-10-19 --to 2026-10-30`

## 엔진 2단계 · 문제 · 이상 · SLO (R3 · R4 · R7)
- [x] `problems`: failures(노드 · 메시지, 많은 순) · unanswered_topics · repeat_topics(비율 높은 순, 같으면 수)
- [x] `anomalies`: 시간마다, 5건 이상 · 그 기간 오류율 × 3 이상 · 오류 1건 이상, 시간순
- [x] `slo`: 기본 0.01 · 3000 · 0.02, `--error-rate` · `--p95` · `--unanswered`, 크면 위반, 위반이면 종료 코드 4
- [x] tests: 16 · 5 · 와이파이 34 · 09시 · 15시 · 프린터 0.0988, 둘째 주 위반 둘 · 첫 주 기준 0.06이면 지킴
- 확인: `uv run tlog problems --file … --from 2026-10-19 --to 2026-10-30`, `uv run tlog slo --url http://localhost:8800 --from 2026-10-26 --to 2026-10-30; echo $?`

## TUI 1단계 · 묶음 고르기 (R11)
- [x] app.py `LogApp`: 위 요약 한 줄, 왼쪽 묶음(실패 · `[t]` 시간대 · 느린 실행 20), 고르면 오른쪽에 그 실행들, `[r]` 다시 읽기
- [x] 엔진(`load` · `metrics`)을 불러 쓰기만
- [x] tests: `run_test`로 요약 줄 · 16줄 · `down` → 5줄 · `t` → `2026-10-26T09` · 다시 `t` → 20줄
- 확인: `uv run tlog ui --file tests/data/run-logs.json --from 2026-10-19 --to 2026-10-30`

## 설치 (R14)
- [x] `[project.scripts] tlog = "tlog.cli:main"`
- [x] `uv tool install --editable .`, `/tmp`에서 `tlog --help`

## 엔진 3단계 · 단계 · 비용 · 비교 · tretry · 주간 보고 (R6 · R8 · R9 · R10)
- [x] `steps`(값 > 0인 실행만) · `cost_usd`(5자리) · `cost_per_run`(6자리) · `llm_calls`
- [x] `tlog compare --prev-from --prev-to [--json]`
- [x] `load.from_tretry`: 시도 줄을 `final`까지 묶어 실행 하나로 (성공 · 대체 · 실패, 시간 = 마지막 시도의 시작 + 걸린 시간)
- [x] `tlog weekly --prev-from --prev-to`: 숫자 표 · 문제 · 할 일 규칙 (LLM 없음)
- [x] tests: FAQ p95 39 (646) · 답 2509 (596) · 0.07836 · 0.000118 · 596, compare +48, tretry 3줄 → 실행 2, 주간 보고 글
