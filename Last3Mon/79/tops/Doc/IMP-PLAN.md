# tops IMP-PLAN

## 엔진 1단계 · 읽기 · 상태 · 읽기만 · 종료 코드 (R1 · R2 · R3 · R5 · R7 · R13 · R14)
- [x] client.py: `post(base, path, body)` — 부를 수 있는 주소 목록(`READ_ONLY`) 밖이면 보내기 전에 오류, HTTP 오류의 JSON 몸은 돌려줌, 못 읽으면 `ReadError`
- [x] client.py: `facts(n8n, file, from, to)` — `--file`이 먼저, `health`가 없는 사실(과제 1 전)은 거절
- [x] view.py: `status_lines(facts)` — 색은 `health` 그대로, 숫자는 AGENTS.md 3절 브리핑 표의 꼴, `null`은 "source not answering" · ⚪
- [x] cli: `tops status [--n8n | $TOPS_N8N] [--file] [--from --to] [--json]`, 종료 코드 0 · 1 · 2 · 4(전체 빨강)
- [x] tests: 사실 사본 → 일곱 줄, `cost: null` → ⚪, `health`를 바꾸면 그 색, 쓰는 주소는 막힘(요청 0건), 꺼진 n8n → 1, 가짜 서버
- 확인: `uv run pytest -q`, `uv run tops status --n8n http://localhost:5678; echo $?`

## 엔진 2단계 · 질문 · 브리핑 (R4 · R6)
- [x] `tops ask "질문"`: `[영역 · 라우터]` + `refused (이유)` 또는 `numbers ✔/✘` + 답
- [x] `tops brief`: `markdown` 그대로
- [x] tests: 작업 요청 거절 · LLM 라우터 답(`[cost · llm]`) · 브리핑 표 줄

## TUI 1단계 · 탭 · 새로고침 · 질문하기 · 못 읽는 탭 (R11 · R12)
- [x] app.py `OpsApp`: 위 한 줄, 탭(Areas · Brief · Ask · Audit · Tools), `[r]` 새로고침, `[?]` 질문하기, `[q]` 끝
- [x] 탭마다 따로 읽고 못 읽으면 그 탭에 "not available", Enter 뒤 포커스를 표로
- [x] tests: `run_test`로 영역 6줄 · 거절 답 · 감사 3줄, 파일만 주면 영역 6줄 + 질문하기 · 감사 "not available"

## 설치
- [x] `[project.scripts] tops = "tops.cli:main"`, `uv tool install --editable .`, `cd /tmp && tops --help`

## 엔진 3단계 · 평가 관문 · 감사 · 지난 도구 (R8 · R9 · R10)
- [x] `tops eval FILE [--min-score]`: `8/8 · score 1 · gate pass (min 0.9)`, 틀린 질문 줄, gate fail → 4, 빈 목록(400) → 2
- [x] `tops audit [--api | $TOPS_API]`: `/audit/list`의 질문 · 영역 · 라우터 · 거절
- [x] `tops tools`: `tlog slo --url … --from 2026-10-26 --to 2026-10-30 --json`의 breaches, `tcheck` 설치 여부, 없으면 "not installed"
- [x] tests: 골든 8 → 0 · 틀린 기대 → 4 · 빈 목록 → 2, 감사 3줄, 없는 도구, tlog 결과 한 줄
