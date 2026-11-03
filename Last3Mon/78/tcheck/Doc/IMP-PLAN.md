# tcheck IMP-PLAN

## 엔진 1단계 · 읽기 · 스키마 · 코드 · n8n과 같은 결과 (R1 · R2 · R3 · R4 · R12 · R13)
- [x] load.py: `read_rows(path)` — `.csv`(첫 줄 열 이름) · JSON 목록 · `{"items"}` · 78일차 요청 파일(`{"schema", "batch", "csv" | "items"}`), `read_schema(name, url, file)` — 데이터 API `GET /schemas/<name>` 또는 `--schema-file`
- [x] checks.py: `check(rows, schema, batch)` — 스키마의 `fields`를 돌며 타입마다 (필드 이름을 코드에 쓰지 않음), 코드는 AGENTS.md 3절 그대로, 키 중복, `row`는 1부터
- [x] cli: `tcheck check FILE [--schema] [--url | $TCHECK_URL]`, 종료 코드 0 · 1(못 읽음) · 2(쓰는 법)
- [x] tests: 직원 9줄 중 4줄 · 접수 건 2줄 · FAQ B-3 5줄, n8n `my-check`가 낸 rows · codes와 **같음** (`tests/data/n8n-my-check.json`), 가짜 데이터 API
- 확인: `uv run pytest -q`, `uv run tcheck check ../requests/employees-new.json --url http://localhost:8800`

## 엔진 2단계 · JSON · 내보내기 · 게이트 (R5 · R6 · R7)
- [x] `--json`: my-check와 같은 모양
- [x] `--out` 깨끗한 줄 · `--rejects` 나쁜 줄 + `errors` 칸 (.csv · .json)
- [x] `tcheck gate --max-invalid 0.3`: 넘으면 종료 코드 4, 같으면 통과
- [x] tests: 파일 두 개 · 직원 0.5556 → 4 · 0.6 → 0 · 1/10 · 0.1 → 통과
- 확인: `uv run tcheck gate ../requests/employees-new.json --url http://localhost:8800; echo $?`

## TUI 1단계 · 탭 · 거르기 · 내보내기 (R11)
- [x] app.py `CheckApp`: 위 요약 한 줄, 탭(문제 줄 · 코드별 · 깨끗한 줄), `[/]` 거르기(키 · 코드), `[Esc]` 풀기, `[e]` 깨끗한 줄 내보내기
- [x] 엔진(`checks`)의 결과를 보여 주기만
- [x] tests: `run_test`로 5 · 5 · 4줄, `email`로 거르면 1줄, `e` → 파일

## 설치 (R14)
- [x] `[project.scripts] tcheck = "tcheck.cli:main"`, `uv tool install --editable .`, `cd /tmp && tcheck --help`

## 엔진 3단계 · 내용 규칙 · 고침 목록 · 품질 기록 (R8 · R9 · R10)
- [x] `--content answer`: Lab 01의 `pii`(하이픈 없는 휴대전화 · 메일) · `external_link`(호스트가 정확히 intra.example.com)
- [x] `--fix`: `fix_list`(줄 순서 · 코드마다 말) · `message`(`TK-1: 9줄 중 2줄 통과, 7줄 고칠 것`)
- [x] `--log`: 데이터 API `POST /quality-log`에 my-check(Lab 03 과제 2)와 같은 한 줄
- [x] tests: 내용 규칙 다섯 줄, 고침 말, 가짜 API에 기록 한 줄
