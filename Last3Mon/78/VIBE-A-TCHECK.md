# 7교시 바이브 코딩 · `tcheck` 정답본

> **강사용 정답본** · 학생 저장소에는 수업 뒤에 올립니다. 학생용: [VIBE-REQ-TCHECK.md](VIBE-REQ-TCHECK.md) → [VIBE-Q-TCHECK.md](VIBE-Q-TCHECK.md).
> 강사가 직접 만든 본: [tcheck/](tcheck/README.md) (테스트 22개, `uv tool install --editable .`). 아래 판정은 2026-11-01 강사 Mac에서 78일차 데이터 API에 실제로 돌린 값이고, n8n `my-check`의 응답(정답 실행 기록 `answers/18` · `answers/21`)과 비교했습니다. 68일차부터 바이브 코딩은 CLI 에이전트로 다시 만들어 재지 않습니다 (요청문은 예시).

## 1. TODO 예 (요청의 말 → 할 일)

| # | 요청의 말 | 할 일 (내 말) | 꼭 · 나중 |
| --- | --- | --- | --- |
| ① | CSV · JSON · 요청 파일 | `.csv` · JSON 목록 · `{"items"}` · `{"schema", "batch", "csv" \| "items"}` | 꼭 |
| ② | 스키마는 API에서, 파일로도 | `GET /schemas/<name>` · `--schema-file`, 필드 이름을 코드에 쓰지 않음 | 꼭 |
| ③ | 몇째 줄 · 왜 · 같은 코드 | 줄 번호 1부터, AGENTS.md 3절 코드 | 꼭 |
| ④ | n8n과 똑같은 판정 | 공백 = 빈 값, 선택 칸, 실제 날짜, 정규식 ASCII, 키 중복 | 꼭 |
| ⑤ | JSON, 같은 칸 이름 | `--json` = `my-check` 모양 | 꼭 |
| ⑥ | 깨끗한 줄 · 나쁜 줄 파일 | `--out` · `--rejects` (+ `errors` 칸, 고치지 않음) | 꼭 |
| ⑦ | 거절될까? · 종료 코드 | `gate --max-invalid 0.3`, 넘으면 4 | 꼭 |
| ⑧ | 개인정보 · 바깥 링크 | `--content answer` (Lab 01 규칙) | 나중 |
| ⑨ | 사람이 읽는 말 · 한 줄 | `--fix` (`fix_list` · `message`) | 나중 |
| ⑩ | 품질 기록에도 | `--log` (`/quality-log`) | 나중 |
| ⑪ | 화면 · 탭 · 거르기 · 내보내기 | `ui` | 꼭 |
| ⑫ | 종료 코드 | 0 · 1 · 2 · 4 | 꼭 |
| 끝 | n8n 없이 시험 · 같은 판정 확인 | 스키마 · 배치 · n8n 결과 사본, 가짜 데이터 API | 꼭 |

## 2. 요청문 (처음 한 번 + 다음 단계 한 줄)

단계마다 긴 요청문을 쓰지 않습니다. 할 일은 이미 `Doc/SPEC.md` · `Doc/IMP-PLAN.md`에 있으니, 에이전트가 그 파일을 읽게 하면 됩니다.

### 처음 한 번

```text
Doc/SPEC.md 와 Doc/IMP-PLAN.md 를 읽고 체크 안 된 첫 단계만 만들어 줘. uv 프로젝트, 명령 이름 tcheck, 코드와 화면 글자는 영어.
끝나면 IMP-PLAN 체크를 표시하고 확인 명령을 알려 줘. 다음 단계는 내가 말할 때까지 하지 마.
```

### 그다음 단계마다 (같은 한 줄)

```text
확인했고 commit 했어. 다음 단계.
```

- 그냥 "계속"만 치면 단계 두세 개를 한꺼번에 하거나 체크 · 확인 명령을 빼먹기 쉽습니다. 이 한 줄은 처음 요청의 약속(한 단계만 · 체크 · 확인 명령 · 멈춤)을 이어 가게 합니다.
- 대화가 길어지면 새 세션에서 **처음 요청**을 다시 보냅니다. "체크 안 된 첫 단계"부터 이어집니다.
- 에이전트가 단계 내용을 잘못 알았다면, 요청문을 길게 쓰기보다 **SPEC · IMP-PLAN을 고치고** 다시 시킵니다.

### 틀렸을 때만 · 고쳐 달라는 요청문 예

무엇이 틀렸나(보인 것) · SPEC의 어느 요구인가 · 어디만 고치나 · 무엇으로 확인하나, 넷을 적습니다.

```text
tcheck check tickets-new.json 이 4째 줄(opened 2026-02-30)을 통과시켜. n8n my-check 는 bad_format:opened 야. SPEC R4 대로 실제 있는 날짜인지까지 봐야 해.
checks.py 의 date 판정만 고치고, 2026-02-30 · 2026-13-01 은 bad_format, 2026-10-28 은 통과인 테스트를 넣어 줘. 다른 파일은 건드리지 마.
```

## 3. 확인 기준과 강사 실측 (11/01, 78일차 데이터 API)

| 요구 | 기준 | 실측 |
| --- | --- | --- |
| R1 | 요청 파일(CSV 든) · CSV · 목록 | `employees-new.json` · `employees.csv` · `tickets-new.json` 모두 9줄 |
| R2 | 스키마 셋, 필드 이름 없이 | `employee` · `ticket` · `faq` 같은 `field_errors`로, 없는 스키마 → 1 |
| R3 | 직원 | 3 `bad_format:email` · 4 `not_allowed:dept` · 5 `bad_format:joined` · 6 `missing:name` · 8 `duplicate_in_batch`, 9줄 중 4줄 |
| R4 | `my-check`와 같은 판정 | 직원 HR-1 · 접수 건 TK-1 · FAQ B-3의 `rows` · `codes` · `valid`가 **모두 같음** (`tests/data/n8n-my-check.json`) |
| R5 | `--json` | `{schema, batch, total, valid, invalid, rows, codes}` — 위와 같은 비교 |
| R6 | 파일 둘 | 직원 → 깨끗한 4줄 · 나쁜 5줄 (첫 줄 `errors` = `bad_format:email`) |
| R7 | `tcheck gate` | 직원 0.5556 → `✘ rejected` · **종료 코드 4**, `--max-invalid 0.6` → 0, B-2 `--content answer` 0.1 · 기준 0.1 → `✔ accepted` (같으면 통과) |
| R8 | `--content answer` | B-2 → FAQ-209 `pii`, `faq-edges.json` → 10줄 중 4줄 (FAQ-406 `pii` · FAQ-409 `external_link`) — Lab 01 예제 3의 내 검사와 같은 4줄, B-1 → 13줄 중 8줄 나쁨 (0.6154) |
| R9 | `--fix` 접수 건 | `TK-1: 9줄 중 2줄 통과, 7줄 고칠 것`, 3째 "priority은(는) low · normal · high 중 하나로" |
| R10 | `--log` | `flow.py quality` → `HR-1  employee  total 9  valid 4  score 0.4444` |
| R11 | `run_test` | 문제 줄 5 · 코드 5 · 깨끗한 줄 4, `email`로 거르면 1줄, `e` → 깨끗한 4줄 파일 |
| R12 | `uv run pytest -q` | 22 passed in 3.0s |
| R13 | 종료 코드 | 없는 파일 1 · 없는 스키마 1 · 스키마를 안 줌 2 · 모르는 명령 2 · 거절 4 |
| R14 | `/tmp`에서 `tcheck --help` | `usage: tcheck [-h] {check,gate,ui} ...`, `tcheck check …` 0.06초 |

- 수업 준비 때 찾은 실수 (학생도 겪기 쉬움): ① Python `re`의 `\w`는 한글도 맞아 메일 판정이 JavaScript와 다를 수 있음 → `re.ASCII`. ② TUI 거르기 상자를 연 `/`가 상자 글자에 들어가고, 상자를 닫아도 포커스가 남아 `e`가 글자로 들어감 → `/`를 지우고 닫을 때 표로 포커스.
- 같은 FAQ B-1을 스키마 + 내용 규칙으로 보면 Lab 01 예제 2의 8줄과 **같은 줄**이 나쁩니다. 코드 이름만 다릅니다 (`title_missing` ↔ `missing:title`, `id_format` ↔ `bad_format:id`). 발표 때 "같은 판정 · 다른 이름"을 짚을 거리.

## 4. 7교시에 볼 것

| 볼 것 | 막혔을 때 한마디 |
| --- | --- |
| 판정이 n8n과 다름 | "어느 줄 · 어느 코드가 다른지 붙여 주고, AGENTS.md 3절 스키마 표 그대로" |
| 필드 이름이 코드에 | "스키마의 fields를 돌며 type마다" |
| 2월 30일 · 13월이 통과 | "실제 있는 날짜인지까지" |
| 빈 선택 칸이 `bad_format` | "비었으면 required만 보고 다음 칸으로" |
| 테스트가 진짜 API를 부름 | "가짜 서버로, 진짜는 확인 단계에서만" |
| 규칙이 여기저기 | "checks.py 한 곳" |
| `gate`가 늘 0 | "넘으면 거절, 거절이면 4" |
| 나쁜 줄 파일에 고친 값 | "원래 줄 그대로 + errors 칸만" |
