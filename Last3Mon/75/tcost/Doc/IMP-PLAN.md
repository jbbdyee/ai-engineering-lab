# tcost IMP-PLAN

## 엔진 1단계 · 단가와 토큰 (R1 · R2 · R3 · R13)
- [x] prices.load(): `checked` · `source` · `models`, `--prices` · `$TCOST_PRICES` · `~/.tcost/prices.json` · 함께 든 파일
- [x] Prices.cost(model, in, out): (in × input + out × output) / 1,000,000, 소수 8자리
- [x] warning(): 30일 넘었거나 날짜가 없으면 알림
- [x] tokens.count(): tiktoken `o200k_base`, 이 컴퓨터에서 (API를 부르지 않음)
- [x] cli: `tcost count <파일 · 폴더> [--out N] [--model M]`
- [x] tests: 1,000토큰 × 0.40 = $0.0004, `--out 100` 더하기, 날짜 경고
- 확인: `uv run pytest -q`, `uv run tcost count <지시문 파일> --out 100`

## 엔진 2단계 · 보고서 모으기 · 한 달 (R5 · R6)
- [x] usage.collect(paths): `runs/*.json`에서 `usage.by_step`이 있는 결과만, 없는 것은 skipped
- [x] 합 · 요청 수 · 호출 수, 모델별 · 사람별 · 시간대별(파일 이름의 시각)
- [x] month(per_day, days): 평균 × 하루 요청 × 일하는 날
- [x] cli: `tcost usage <폴더> [--per-day 1000 --days 22]`
- [x] tests: 결과 3개 중 400 하나 skipped, 사람별 합, 한 달
- 확인: `uv run tcost usage ~/aio-01d4-stu/Last3Mon/75/runs --per-day 1000`

## TUI 1단계 · 탭 셋 (R8)
- [x] Prompts: 글 파일 · 워크플로우 LLM 단계마다 토큰, 모델별 1,000번 비용
- [x] Usage: 보고서 합 · 모델별 · 사람별 표, 시간대별 막대
- [x] Compare: 토큰이 많은 지시문 열 개를 모델별로 (출력 100 가정)
- [x] 엔진은 고치지 않고 불러 쓰기만, `[r]` 다시 읽기
- [x] tests: `run_test`로 세 탭이 채워짐
- 확인: `uv run tcost ~/aio-01d4-stu/Last3Mon/75/reference ~/aio-01d4-stu/Last3Mon/75/runs`

## 설치 (R14)
- [x] `[project.scripts] tcost = "tcost.cli:main"`, 단가 파일을 wheel에 함께
- [x] `uv tool install --editable .`, `/tmp`에서 `tcost --help`

## 엔진 3단계 · 워크플로우 · 비교 · 모르는 모델 (R4 · R7 · R12)
- [x] workflow.llm_steps(): HTTP `chat/completions` 노드의 `jsonBody`에서 모델 · system 글 · `max_completion_tokens`, AI Agent 노드도
- [x] cli: `tcost workflow <파일 · 폴더>`, `tcost compare <파일> --model a --model b`
- [x] 단가표에 없는 모델은 0원이 아니라 오류(알려진 목록)
- [x] tests: baseline `Answer` 1,000토큰 넘음 · lean 200 아래, `gpt-9` → 종료 코드 2

## 엔진 4단계 · 예산 · 다른 프로그램 · 폴더 (R9 · R10 · R11)
- [x] cli: `tcost budget <달러> <파일>` 모델별 하루 몇 번
- [x] `--json`, `--max-usd`: 넘으면 종료 코드 1, 오류 2
- [x] scan(): `.txt` · `.prompt` 글 (`.md` 문서는 skipped), `nodes` · `connections` 워크플로우, `results` 보고서, 나머지 skipped
- [x] tests: 테스트 파일은 skipped, 긴 글 `--max-usd 0.0002` → 1
