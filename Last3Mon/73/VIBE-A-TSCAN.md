# 7교시 바이브 코딩 · `tscan` 만들기

> **정답본** · 수업이 끝난 뒤(8교시 뒤) 학생 저장소에 올립니다. 그 전에는 올리지 않습니다. 요청서는 [VIBE-REQ-TSCAN.md](VIBE-REQ-TSCAN.md), 문제는 [VIBE-Q-TSCAN.md](VIBE-Q-TSCAN.md).
> 아래 TODO · SPEC · IMP-PLAN · 요청문과 확인 기준은 예시입니다. 8교시 강사 바이브 코딩에서 걸린 시간을 재어 6절에 적습니다.
> **10/26:** R1~R14를 모두 넣은 본을 [tscan/](tscan/)에 직접 만들어 봤습니다 (7절). 요청문으로 CLI 에이전트에 시킨 것이 아니라 Claude Code가 SPEC · IMP-PLAN을 보고 쓴 것이라, 8교시 걸린 시간 표와는 따로 봅니다.

## 1. `Doc/TODO.md` 예

```markdown
# tscan TODO

## 만들고 싶은 것
어느 폴더에서나 `tscan`으로 폴더 · 커밋하려는 파일에서 키 · 개인정보를 찾아 가린 채로 보여 주고,
커밋 전에 저절로 막고, 다른 프로그램이 읽을 결과도 주는 도구.

## 요청의 말 → 할 일
| # | 요청의 말 (짧게) | 할 일 (내 말) | 꼭 · 나중 |
| --- | --- | --- | --- |
| ① | 키 · 주민번호 · 전화 · 이메일, 몇째 줄 | 종류마다 모양을 정해 찾고 파일 · 줄을 보여 줌 | 꼭 |
| ② | 화면에 그대로 X | 앞뒤 몇 글자만, 원래 값은 어디에도 남기지 않음 | 꼭 |
| ③ | .env 값이 다른 파일에 | .env 값을 모아 다른 파일에서 같은 글자를 찾음 | 꼭 |
| ④ | 날짜 · 주문 번호를 잡지 않게 | 모양을 좁히고, 잡으면 안 되는 것도 시험 | 꼭 |
| ⑤ | 커밋 전에, git add 한 것만 | staged 내용만 보고 찾으면 실패로 끝남 | 꼭 |
| ⑥ | 저절로, 다른 훅은 그대로 | pre-commit 훅 설치 · 해제, 남의 훅은 건드리지 않음 | 꼭 |
| ⑦ | "이건 괜찮아" | 무시 목록 파일 | 나중 |
| ⑧ | 화면에서 고르고 앞뒤 보기 | TUI 목록 + 미리 보기(가려서) + 괜찮아 표시 | 꼭 |
| ⑨ | 예전 커밋 | git 기록의 더한 줄을 검사 | 나중 |
| ⑩ | 다른 프로그램이 읽게 | JSON 결과 + 종료 코드 | 나중 |
| ⑪ | 우리 회사 모양 | 설정 파일에 모양을 더함 | 나중 |
| ⑫ | 종류별 · 파일별 · 건너뛴 것 | 요약, 큰 파일 · 바이너리는 건너뛰고 셈 | 건너뛰기 꼭 · 요약 나중 |
| 끝 | 시험에 진짜 키 X | 가짜 값만, 파일로 두지 않음 | 꼭 |
| 끝 | 진짜 비밀을 찾으면 | 화면 닫고 알림 · 폐기 (도구 밖의 절차) | 메모 |

## 요청에 없지만 걱정되는 것
- 가짜 비밀 파일을 테스트 폴더에 두면 다 만든 도구가 내 저장소에서 그것을 또 찾음
- git add 뒤에 파일을 고치면 작업 파일과 커밋될 내용이 다름
- 훅 안에서 tscan 명령을 찾지 못하면?

## 오늘 50분 안에 못 할 것 같은 것
⑦ ⑨ ⑩ ⑪ ⑫ 요약
```

## 2. `Doc/SPEC.md` 예 (요구 표는 VIBE-Q와 같음, 확인 기준을 구체적으로)

| 요구 | 확인 기준 |
| --- | --- |
| R1 | 임시 폴더 `notes.md`에 가짜 키 1 · 전화 1 · 이메일 1 · 주민번호 1 → 그 넷, 줄 1 · 2 · 2 · 3 |
| R2 | `--plain` · `--json` 출력에 가짜 값 다섯 모두 0번 (`010-****-1234`, `t***@example.com`, `900101-*******`, `sk-…****…ij`) |
| R3 | `.env`의 `TOKEN=abc123def456`, `config.py`에 같은 글자 → `env_value config.py:1`, `.env` 자신은 `env_value`로 세지 않음 |
| R4 | `date 2026-10-27, order 202610271234, version 1.0.10-20261027` 줄 → 0건 |
| R5 | 임시 git 저장소: 가짜 키 파일 `git add` 뒤 작업 파일을 지워도 `tscan staged` 종료 코드 1, 다시 `git add` → 0 |
| R6 | `install-hook` → `.git/hooks/pre-commit`에 `tscan staged`, 실행 권한. 이미 남의 훅 → 덮지 않고 종료 코드 2, `uninstall-hook`도 남의 훅은 그대로 |
| R7 | `.tscanignore`의 `notes.md:3`(그 줄) · `email:*.md`(종류 + 경로 글롭) · `vendor/*`(경로) |
| R8 | TUI 행 5개, 내려가면 미리 보기 앞뒤 2줄에 원래 값 없음, `[i]` → `.tscanignore`에 `notes.md:1`, 행 4개 |
| R9 | 가짜 키를 커밋 → 지우는 커밋 → `tscan history`에 첫 커밋의 `a.txt` |
| R10 | `--json` `{"findings": [{kind, path, line, masked}], "summary": {...}}`, 종료 코드 0 · 1 · 2 (git 저장소가 아닌 곳에서 `staged` → 2) |
| R11 | `.tscan.toml`의 `[[rule]] name = "employee_id"`, `pattern = "E-\\d{6}"` → `E-123456` 찾음 |
| R12 | `--summary` → `by kind …`, 파일별 수, `skipped  binary 1  too_big 1` |
| R13 | 1.1MB 파일 · NUL 바이트 파일 · `node_modules/` 안 → 찾지 않음, 건너뛴 수 2 |
| R14 | `uv tool install --editable .` 뒤 `cd /tmp && tscan --help` 성공 |

숨은 요구 · 범위 밖은 VIBE-Q 표와 같습니다.

## 3. `Doc/IMP-PLAN.md` 예

```markdown
# tscan IMP-PLAN

## 엔진 1단계 · 찾고 가리기 (R1 · R2 · R3 · R4 · R13)  ← 7교시
- [ ] src/tscan/scanner.py: PATTERNS(종류 · 정규식 · 경계), mask(value, kind), scan_text → Finding(kind, path, line, masked)
- [ ] src/tscan/files.py: iter_files(건너뛰기), read_text(1MB · NUL), .env 값 모으기, scan_folder → (findings, {files, skipped})
- [ ] tests/conftest.py: 가짜 비밀을 테스트 안에서 이어 붙여 tmp_path 에 (찾을 것 · 찾으면 안 되는 것 · 큰 파일 · 바이너리)
- [ ] cli.py: tscan scan <folder> [--plain]
- 확인: uv run pytest -q · uv run tscan scan <tmp> --plain

## 엔진 2단계 · 커밋 전에 막기 (R5 · R6)  ← 7교시
- [ ] gitscan.py: staged() = git diff --cached --name-only --diff-filter=ACM -z + git show :<path>
- [ ] install_hook / uninstall_hook (표시 줄로 내 훅만), 종료 코드 0 · 1 · 2
- 확인: 임시 저장소에서 가짜 키 git add → tscan staged; echo $?

## TUI 1단계 · 목록 · 미리 보기 (R8)  ← 7교시
- [ ] app.py: 요약 Static · DataTable(kind, file, line, value) · 미리 보기 Static, 검사는 worker
- [ ] 미리 보기는 mask_line 으로 (같은 가리기)
- 확인: uv run tscan <tmp>

## 설치 (R14)  ← 7교시 끝
- [ ] pyproject [project.scripts] tscan = "tscan.cli:main", uv tool install --editable .

## 엔진 3단계 · 무시 · JSON · 요약 (R7 · R10 · R12)
## 엔진 4단계 · 기록 · 사용자 모양 (R9 · R11)
## TUI 2단계 · [i] 무시 · [r] 다시 검사
```

## 4. 단계별 요청문 예

### 엔진 1단계 · 찾고 가리기

```text
Doc/SPEC.md 와 Doc/IMP-PLAN.md 를 읽고 "엔진 1단계"만 만들어 줘. uv 프로젝트(src/tscan), 명령 이름 tscan, 코드와 화면 글자는 영어.
tscan scan <folder> [--plain]: 한 줄에 "kind path:line masked", 끝에 "found N in M file(s), skipped K".
- 종류: openai_key(sk-[A-Za-z0-9_-]{20,}), rrn(생년월일 6자리 + 1~4로 시작하는 7자리), phone(01[016789] + 3~4 + 4), email.
  각 종류는 앞뒤가 숫자 · 점 · 하이픈이 아닐 때만 (날짜 · 버전 · 주문 번호를 잡지 않게).
- 가리기: 전화 앞 3 · 끝 4, 이메일 첫 글자 + ***@도메인, 주민번호 앞 6 + -*******, 키 앞 3 + …****… + 끝 2.
  찾은 결과 객체에는 가린 값만 담는다. 원래 값은 어디에도 담지 않는다.
- .env 파일들의 값(6자 이상)을 모아, 다른 파일에 같은 글자가 있으면 kind env_value (값은 가려서).
- .git, node_modules, .venv, 1MB 넘는 파일, 바이너리(앞 8KB 에 NUL)는 건너뛰고 이유별로 센다.
- pytest: 가짜 비밀은 테스트 안에서 이어 붙여 만들어 tmp_path 에 쓴다 (저장소에 가짜 비밀 파일을 두지 않음).
  찾아야 할 것과 찾으면 안 되는 것(2026-10-27, 202610271234, 1.0.10-20261027) 둘 다.
끝나면 IMP-PLAN 의 엔진 1단계 체크를 표시하고 확인 명령을 알려 줘.
```

### 엔진 2단계 · 커밋 전에 막기

```text
IMP-PLAN 의 "엔진 2단계"만:
- tscan staged: git diff --cached --name-only --diff-filter=ACM -z 의 파일마다 staged 내용(git show :<path>)을 검사. 찾으면 목록 + 종료 코드 1, 없으면 0.
  git 저장소가 아니면 종료 코드 2 와 한 줄 안내.
- tscan install-hook / uninstall-hook: .git/hooks/pre-commit 에 "# tscan pre-commit hook" 표시 줄과 "exec tscan staged", 실행 권한.
  이미 다른 훅이 있으면 덮지 않고 안내 (종료 코드 2). 지울 때도 표시 줄이 있는 내 훅만.
- 테스트: 임시 git 저장소에서 git add 뒤 작업 파일을 고쳐도 staged 내용으로 판단하는지, 남의 훅이 그대로인지.
```

### TUI 1단계 · 목록 · 미리 보기

```text
IMP-PLAN 의 "TUI 1단계"만. tscan <folder> (명령 없이 폴더) 는 Textual 앱:
위 요약(파일 · 찾은 것 · 건너뜀), 가운데 DataTable(kind, file, line, value), 아래 미리 보기(고른 줄의 앞뒤 2줄).
미리 보기는 엔진의 mask_line 으로 가린 글자만 (앞뒤 줄의 다른 비밀도 가려짐). 검사는 worker(thread), 결과는 call_from_thread.
키: [i] 고른 것을 .tscanignore 에 "path:line" 으로 더하고 다시 검사, [r] 다시 검사, [q] 끝. 엔진 코드는 바꾸지 않는다.
```

### 설치

```text
pyproject.toml 에 [project.scripts] tscan = "tscan.cli:main" 이 있는지 보고, 없으면 넣어 줘.
그리고 내가 실행할 명령만 알려 줘: uv tool install --editable . , uv tool list, cd /tmp && tscan --help
```

### 엔진 3 · 4단계 (이어서)

```text
IMP-PLAN 의 "엔진 3단계"만: .tscanignore (path:line · kind:glob · glob), --json {"findings", "summary"}, --summary (종류별 · 파일별 · 건너뛴 이유별).
그다음 "엔진 4단계": tscan history [--max 200] (git log -p 의 + 줄만, path 는 "<짧은 커밋> <파일>"),
.tscan.toml 과 ~/.tscan/rules.toml 의 [[rule]] name · pattern 을 종류로 더함. 테스트는 가짜 값만.
```

## 5. 7교시에 볼 것

| 볼 것 | 막혔을 때 한마디 |
| --- | --- |
| TODO · SPEC 없이 에이전트부터 | "요청서로 Doc/TODO.md부터. 찾으면 안 되는 것이 SPEC에 없으면 잘못 찾기를 모릅니다" |
| IMP-PLAN이 한 단계짜리 | "엔진과 화면을 나누고, 엔진도 1 · 2로. 단계마다 commit" |
| 날짜 · 번호를 전화번호로 찾음 | "찾으면 안 되는 것도 테스트에. 앞뒤 경계" |
| 찾은 값을 그대로 출력 · 결과 객체에 원래 값 | "가리기 전 값은 객체에도 남기지 말게" |
| `tests/data/`에 가짜 비밀 파일 | "테스트 안에서 이어 붙여 tmp_path에" |
| 작업 파일을 검사함 (staged가 아님) | "`git show :<path>`로 staged 내용" |
| 훅이 안 돎 | "실행 권한(chmod +x), 설치한 tscan이 PATH에 있는지" |
| 기존 훅을 덮어씀 | "있으면 멈추고 알리게, 표시 줄로 내 훅만" |
| 미리 보기에 다른 비밀이 그대로 | "미리 보기도 같은 가리기를 거치게" |
| `tscan`을 못 찾음 | `uv tool update-shell` 뒤 새 터미널, `uv tool list` |

### 자주 빠뜨리는 것 (수업 준비 때 예상)

| 빠뜨린 것 | 생기는 일 |
| --- | --- |
| 찾으면 안 되는 것의 테스트 | 날짜 · 번호마다 경고 → 아무도 안 씀 (요청서 ④) |
| 결과 객체에 원래 값 | JSON 결과 · 오류 메시지 · 로그로 비밀이 다시 나감 |
| staged 내용 | `git add` 뒤 고친 파일을 보고 통과 → 커밋에는 비밀 |
| 가짜 비밀을 테스트 안에서 | 내 저장소를 검사할 때 테스트 파일이 걸림 |
| 엔진과 화면 나누기 | 훅에서 TUI가 떠 커밋이 멈춘 채 기다림 |
| `[project.scripts]` | `uv tool install`은 되는데 `tscan` 명령이 없음 |

## 6. 강사 바이브 코딩 (8교시, 15분 · 시간 기록)

| 할 것 | 걸린 시간 | 메모 |
| --- | --- | --- |
| 엔진 1단계 + 엔진 2단계를 위 요청문으로 | (8교시에 잼) | |
| `tscan install-hook` 뒤 가짜 키 커밋이 멈추는 장면 (74일차 배포 전 검사의 씨앗) | (8교시에 잼) | |

## 7. 수업 준비 때 직접 만들어 본 본 (10/26, `tscan/`)

| 확인 | 결과 |
| --- | --- |
| `uv run pytest -q` (가짜 비밀만) | **12 passed** (0.9초): 종류 · 줄 · 날짜 안 찾음 · 건너뛰기, JSON에 원래 값 없음, `env_value`, 전각으로 숨긴 키, 미리 보기 가리기, 무시 목록 · 사용자 모양 · 요약, 없음 → 0, staged(작업 파일을 고쳐도 index로), 남의 훅 그대로, 지운 키를 기록에서, 저장소 아님 → 2, TUI 행 · 미리 보기 · `[i]` |
| `uv tool install --editable .` → `cd /tmp && tscan --help` | 됨 |
| `tscan scan Last3Mon/73/tscan` (자기 자신) | **found 0** (가짜 비밀을 테스트 안에서 이어 붙였기 때문) |
| `tscan scan Last3Mon/73 --summary` (오늘 실습 폴더) | 188개 파일에서 63건: phone 48 · email 12 · rrn 2 · openai_key 1. 키 1은 `tools/flow.py`의 연습용 가짜 키 `sk-invalid-…`, 나머지는 실습 문서 · 데이터 API 예시 연락처와 테스트 기록 |

만들며 알게 된 것 (학생이 막힐 만한 곳):

| 알게 된 것 | 정한 방법 |
| --- | --- |
| 실습 폴더에는 **일부러 넣은 예시 연락처**가 많음 (실습 문서 · `answers/` · `runs/`) | 학생에게 "찾은 것이 많다 = 고장"이 아님을 먼저 말함. `.tscanignore`의 `runs/*` · `answers/*`로 줄여 보기 (R7) |
| 전화번호 정규식이 `010.1414.2135`(점) · `01014142135`(붙임)도 잡아야 함 | Lab 03 출력 필터와 같은 `[-. ]?`, 대신 앞뒤 경계에 점 · 하이픈 · 숫자를 넣어 버전 · 날짜를 뺌 |
| 주민번호 모양만 보면 12자리 주문 번호 일부를 잡음 | 월 01~12 · 일 01~31 · 7번째 1~4, 앞뒤 경계 |
| 가린 키끼리 겹침 (`.env` 값이 키 모양이기도 함) | 한 줄에서 겹치는 찾음은 앞에서부터 가장 긴 것 하나만 |
| `git add` 뒤 파일을 고치면 작업 파일과 index가 다름 | `git show :<path>`로 index 내용 (테스트로 고정) |
| 전각으로 쓴 키 | 오늘 Lab 01 과제 2의 NFKC · 보이지 않는 글자 지우기를 줄마다 |
| `history`의 줄 번호 | 파일의 줄이 아니라 그 커밋에서 **더한 줄의 순번** (커밋 · 파일이 더 중요) |
