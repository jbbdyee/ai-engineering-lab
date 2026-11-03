# tcheck · 강사가 수업 준비 때 직접 만든 본 (2026-11-01)

> **정답 자료** · 학생 저장소에는 수업 뒤 [VIBE-A-TCHECK.md](../VIBE-A-TCHECK.md)와 함께 올립니다.
> 이 본은 강사가 CLI 에이전트에 단계 요청문을 보내 만든 것이 아니라, Claude Code가 VIBE-Q의 요구 R1~R14와 [Doc/IMP-PLAN.md](Doc/IMP-PLAN.md)를 보고 직접 썼습니다. 학생이 만든 것과 파일 구성이 달라도 됩니다. 요구의 **확인 방법**이 같으면 됩니다.

## 설치 · 실행

```bash
cd ~/aio-01d4-stu/Last3Mon/78/tcheck
uv sync && uv run pytest -q              # 테스트 22개 (n8n · 데이터 API 없이, 가짜 서버)
uv tool install --editable .             # 어느 폴더에서나 tcheck (R14)
cd /tmp && tcheck --help
```

| 하고 싶은 것 | 명령 |
| --- | --- |
| 검사 (n8n `my-check`와 같은 판정) | `tcheck check ../requests/employees-new.json --url http://localhost:8800` (`--json`) |
| 스키마를 파일에서 | `tcheck check employees.csv --schema-file ../data-api/data/schemas/employee.json` |
| 깨끗한 줄 · 나쁜 줄 파일 | `tcheck check … --out clean.csv --rejects rejects.csv` |
| 배치 게이트 (넘으면 종료 코드 4) | `tcheck gate … --max-invalid 0.3` |
| FAQ 내용 규칙 (개인정보 · 바깥 링크) | `tcheck check ../requests/faq-batch-2.json --schema faq --content answer` |
| 보낸 사람에게 고침 목록 | `tcheck check … --fix` |
| 품질 기록 한 줄 | `tcheck check … --log` (데이터 API `/quality-log`) |
| 화면(TUI) | `tcheck ui …` (`[/]` 거르기, `[Esc]` 풀기, `[e]` 깨끗한 줄 내보내기, `[q]` 끝) |

- 종료 코드: 0 됨 · 1 파일이나 스키마를 못 읽음 · 2 쓰는 법이 틀림 · 4 게이트가 배치를 거절.
- 데이터 API 주소는 `--url` 또는 `$TCHECK_URL`. `--schema-file`을 주면 파일이 먼저입니다. 스키마 이름은 `--schema` 또는 요청 파일의 `"schema"`.
- 판정 규칙은 [AGENTS.md](../AGENTS.md) 3절 "스키마" 표와 같습니다 (공백만 있는 값은 빈 값, 선택 칸은 비면 통과, 실제 있는 날짜, 키 중복, `row`는 1부터, 소수 4자리 half up).

## 파일

| 파일 | 하는 일 |
| --- | --- |
| `src/tcheck/load.py` | 읽는 층 (R1 · R2 · R10): CSV · JSON · 요청 파일, 스키마(API · 파일), 품질 기록 보내기 |
| `src/tcheck/checks.py` | 규칙 한 곳 (R3 · R7 · R8 · R9 · R13): 타입마다 판정 · 내용 규칙 · 게이트 · 고침 목록 · 기록 한 줄 · 나누기 |
| `src/tcheck/cli.py` | `check` · `gate` · `ui`, 종료 코드 (R5 · R6 · R12) |
| `src/tcheck/app.py` | Textual 화면 (R11) |
| `tests/` | 직원 CSV · 접수 건 · FAQ B-3 · 스키마 셋 사본, n8n `my-check`가 낸 결과(`n8n-my-check.json`), 가짜 데이터 API (R12) |

## 수업 준비 때 확인한 것 (11/01)

- 같은 세 배치(직원 HR-1 · 접수 건 TK-1 · FAQ B-3)의 `rows` · `codes` · `valid`가 n8n `my-check`의 응답(`answers/18` · `answers/21`)과 **모두 같음** (`test_same_rows_and_codes_as_n8n`).
- FAQ B-1에 `--schema faq --content answer`: 13줄 중 8줄 나쁨 (0.6154) — Lab 01 예제 2의 내 검사와 같은 8줄 (코드는 스키마 꼴 `missing:title` · `bad_format:id` …).
- 반올림은 JavaScript `Math.round`처럼 half up (`js_round`). 77일차 `tlog`와 같은 까닭.
- 처음 판에서 TUI의 거르기 상자를 연 `/` 글자가 상자에 들어가고, 상자를 닫은 뒤에도 포커스가 남아 `e`(내보내기)가 글자로 들어갔음 → 글자 앞의 `/`를 지우고, 닫을 때 표로 포커스를 옮김.
