# 7교시 바이브 코딩 · `tbench` 만들기

> **정답본** · 수업이 끝난 뒤(8교시 뒤) 학생 저장소에 올립니다. 그 전에는 올리지 않습니다. 요청서는 [VIBE-REQ-TBENCH.md](VIBE-REQ-TBENCH.md), 문제는 [VIBE-Q-TBENCH.md](VIBE-Q-TBENCH.md).
> 68일차부터 바이브 코딩 프로그램은 **수업 준비 때 미리 만들어 보지 않습니다.** 아래 TODO · SPEC · IMP-PLAN · 요청문과 확인 기준은 예시이고, 걸린 시간은 8교시 강사 바이브 코딩에서 재어 기록합니다.
> **10/26 추가:** 강사 요청으로 R1~R14를 모두 넣은 본을 [tbench/](tbench/)에 직접 만들어 봤습니다 (7절). 요청문으로 CLI 에이전트에 시킨 것이 아니라 Claude Code가 SPEC · IMP-PLAN을 보고 쓴 것이라, 8교시 걸린 시간 표와는 따로 봅니다.

## 1. `Doc/TODO.md` 예

```markdown
# tbench TODO

## 만들고 싶은 것
어느 폴더에서나 `tbench`로 웹훅을 여러 번 불러, 보통 · 느린 쪽 시간과 실패를 보여 주고,
바꾸기 전 · 후를 같은 조건으로 비교하는 터미널 도구. 나중에는 기준을 주면 통과 · 실패만 알려 줌.

## 요청의 말 → 할 일
| # | 요청의 말 (짧게) | 할 일 (내 말) | 꼭 · 나중 |
| --- | --- | --- | --- |
| ① | 여러 번 · 몇 번 실패 · 보통 · 느린 쪽 | N번 부르고 한 번마다 상태 · 시간, 끝에 p50 · p95 · max · 실패 | 꼭 |
| ② | 기다리기 싫음 · 모양 | 오는 대로 표에 한 줄씩, 스파크라인 | 꼭 |
| ③ | 숫자로 비교 · 다른 질문 비교 망신 | 결과 저장, 두 결과 비교, 조건이 다르면 경고 | 꼭 |
| ④ | 한꺼번에 | 동시에 k개 | 나중 |
| ⑤ | 만들어 둔 요청 고르기 | requests 폴더에서 고르기 (turl은 형식 확인 뒤) | 나중 |
| ⑥ | 첫 번만 느림 | 첫 호출 표시, 빼고도 p50, 미리 불러 두기 | 꼭 |
| ⑦ | 왜 실패했는지 | 연결 · 시간 초과 · 서버 오류를 따로 셈 | 꼭 |
| ⑧ | 단계별 시간 평균 | 응답의 timings를 모아 단계 평균 | 나중 |
| ⑨ | 화면 없이 통과 · 실패 | 기준을 넘으면 실패, 종료 코드 | 나중 |
| ⑩ | 줄줄이 기록 | 한 번마다 한 줄 파일 | 나중 |
| ⑪ | 설정 저장 · 이름으로 | 설정 파일, 이름으로 실행 | 나중 |
| ⑫ | 잰 것 목록 | 저장한 결과 목록 | 나중 |
| 끝 | 키가 찍히면 안 됨 | 저장 · 기록에서 키 가리기 | 꼭 |
| 끝 | 진짜 헬프데스크 두드리지 않기 | 시험은 가짜 서버로 | 꼭 |
| 첫 문단 | 어느 폴더에서나 | uv tool install | 꼭 |

## 요청에 없지만 걱정되는 것
- 시간을 어디서부터 어디까지 재나, 끝없이 기다리면?
- p95를 어떻게 계산하나 (사람마다 다르면 비교가 안 됨)
- 저장 폴더 · 설정 파일을 어디에 (어느 폴더에서 실행해도 같은 곳)

## 오늘 50분 안에 못 할 것 같은 것
④ ⑤ ⑧ ⑨ ⑩ ⑪ ⑫ — IMP-PLAN의 다음 단계로
```

## 2. `Doc/SPEC.md` 예 (요구 표는 VIBE-Q와 같음, 확인 기준을 구체적으로)

| 요구 | 확인 기준 |
| --- | --- |
| R1 | 가짜 서버(지연 0.1초, 3번째마다 500)로 n=6 → 실패 2, 시간 6개. `stats.py` 테스트: 1~10초 → p50 5 · p95 10 (nearest-rank, 자리 = 올림(p × n)) |
| R2 | worker로 부름, 결과마다 표 한 줄 · 스파크라인 · 요약 갱신 (가짜 서버 지연 0.5초 × 6에서 3초 동안 한 줄씩 늘어남) |
| R3 | 저장 JSON: `{url, method, body_sha256, n, concurrency, warmup, started, seconds:[...], statuses:[...], errors:[...]}`. compare에서 url · body_sha256 · n이 다르면 `WARNING: different ...` 줄 |
| R4 | 가짜 서버 지연 0.3초 × 6번: `--concurrency 1` 약 1.8초, `3` 약 0.6초 안팎 |
| R5 | `requests/*.json` 목록을 TUI `OptionList`로, 고르면 그 본문으로 실행 |
| R6 | 가짜 서버 첫 응답만 2초 → 1번 줄 note `first call`, "p50 excl. first" 따로. `--warmup 1` → 시간 목록 n개(warmup 제외) |
| R7 | 없는 포트 → `connect` 1, 지연 3초 + `--timeout 1` → `timeout` 1, 500 → `http_5xx` 1, 404 → `http_4xx` 1 |
| R8 | `--header "Authorization: Bearer sk-test"` → 저장 · 기록 파일 `grep -c sk-test` 0, 대신 `"Authorization": "***"` |
| R9 | 응답 JSON의 `timings`(숫자 칸만)를 칸마다 평균. 내 헬프데스크 → `classify_ms … total_ms` 평균 한 줄. `timings`가 없으면 표 없음 |
| R10 | `--max-p95 2.5 --max-failures 0`: 넘으면 마지막 줄 `FAIL p95 3.1 > 2.5`, 종료 코드 1. 아니면 `PASS`, 0 |
| R11 | `--log runs.jsonl`: 줄마다 `{"t", "i", "status", "seconds", "error_kind"}`, 줄 수 = N(+ warmup은 `"warmup": true`) |
| R12 | `~/.tbench/profiles.toml`, `tbench profile save/list`, `tbench run <이름>`: 다른 폴더에서도 같은 결과 파일 조건 |
| R13 | 기본 저장 폴더 `~/.tbench/results/`, `tbench history` → 최신이 위, 날짜 · URL · N · p50 · p95 · 실패 |
| R14 | `uv tool install --editable .` 뒤 `cd /tmp && tbench --help` 성공, `uv tool list`에 `tbench` |

숨은 요구 · 범위 밖은 VIBE-Q 표와 같습니다.

## 3. `Doc/IMP-PLAN.md` 예

```markdown
# tbench IMP-PLAN

## 엔진 1단계 · 부르고 재기 (R1 · R6 · R7 · R8)  ← 7교시
- [ ] src/tbench/runner.py: call_once(url, method, body, headers, timeout) → {i, status, seconds, error_kind}
- [ ] src/tbench/stats.py: percentile(nearest-rank), summarize(results) → p50 · p95 · max · failures · by_kind · p50_excl_first
- [ ] tests/conftest.py: 가짜 서버 (지연 · N번째마다 500 · 첫 응답만 느림 · 404)
- [ ] cli.py: tbench <url> --body-file --n --method --timeout --header --warmup --plain
- 확인: uv run pytest -q · uv run tbench <url> -n 5 --plain

## TUI 1단계 · 오는 대로 보이기 (R2)  ← 7교시
- [ ] app.py: Sparkline · 요약 Static · DataTable, worker 가 runner 를 돌리며 결과마다 call_from_thread 로 갱신
- 확인: uv run tbench <url> -n 20 (가짜 서버 지연 0.5초)

## 설치 (R14)  ← 7교시 끝
- [ ] pyproject [project.scripts] tbench = "tbench.cli:main", uv tool install --editable .

## 엔진 2단계 · 남기고 비교 (R3 · R13 · R11)
- [ ] save(result, path=None) 기본 ~/.tbench/results/<시각>.json, compare(a, b), history()
- [ ] --log runs.jsonl
## 엔진 3단계 · 동시 · 기준 · 응답 분석 · 설정 (R4 · R10 · R9 · R12)
## TUI 2단계 · 고르기 · 비교 · 기록 화면 (R5 · R3 · R13)
```

## 4. 단계별 요청문 예

### 엔진 1단계 · 부르고 재기

```text
Doc/SPEC.md 와 Doc/IMP-PLAN.md 를 읽고 "엔진 1단계"만 만들어 줘. uv 프로젝트(src/tbench), 명령 이름 tbench, 코드와 화면 글자는 영어.
tbench <url> [--body-file f.json] [-n 10] [--method POST] [--timeout 30] [--header "K: V" ...] [--warmup 0] --plain
- 한 번마다 "#i status seconds note", 끝에 p50 · p95 · max · failures(종류별: connect · timeout · http_5xx · http_4xx), p50 excl. first.
  시간은 보내기 직전 ~ 본문을 다 받을 때까지. 실패도 한 번으로 셈. 1번 줄 note 는 "first call". warmup 은 재지 않고 버림.
- 백분위: 정렬 후 nearest-rank (ceil(p*n) 번째). stats.py 로 분리하고 pytest 로 1..10 → p50 5, p95 10.
- 엔진은 결과를 하나씩 돌려주는 제너레이터로 (나중에 TUI가 받음). 화면 코드는 아직 쓰지 않는다.
- 테스트는 pytest 안에서 http.server 로 가짜 서버(지연, N번째마다 500, 첫 응답만 느림, 404)를 띄워서. 진짜 n8n 을 부르지 않는다.
- Authorization 등 키 머리글은 출력 · 저장에서 "***".
끝나면 IMP-PLAN 의 엔진 1단계 체크를 표시하고 확인 명령을 알려 줘.
```

### TUI 1단계 · 오는 대로 보이기

```text
IMP-PLAN 의 "TUI 1단계"만 해 줘. tbench <url> ... (--plain 없이) 는 Textual 앱:
위 Sparkline(시간 목록), 요약 줄(완료/전체, 실패, p50, p95, max, p50 excl. first), 아래 DataTable(#, status, seconds, note).
엔진 제너레이터를 worker(thread)에서 돌리고 결과마다 call_from_thread 로 표 · 스파크라인 · 요약을 갱신. 엔진 코드는 바꾸지 않는다.
키: q 끝. 확인: 가짜 서버 지연 0.5초 × 6 에서 한 줄씩 늘어나는지.
```

### 설치

```text
pyproject.toml 에 [project.scripts] tbench = "tbench.cli:main" 이 있는지 보고, 없으면 넣어 줘.
그리고 내가 실행할 명령만 알려 줘: uv tool install --editable . , uv tool list, cd /tmp && tbench --help
```

### 엔진 2단계 · 남기고 비교

```text
IMP-PLAN 의 "엔진 2단계"만: --save [path] (없으면 ~/.tbench/results/<YYYYMMDD-HHMMSS>.json) 에
{url, method, body_sha256, n, concurrency, warmup, started, seconds, statuses, errors} 저장 (키 머리글은 "***").
tbench compare a.json b.json: p50 · p95 · max · failures 와 변화(%) 표, url · body_sha256 · n 이 다르면 WARNING 줄.
tbench history: ~/.tbench/results 의 파일을 최신부터 날짜 · url · n · p50 · p95 · failures 표. --log runs.jsonl: 한 번마다 한 줄.
테스트: 다른 본문 두 결과 → WARNING, 저장 파일에 sk- 없음.
```

### 엔진 3단계 · 동시 · 기준 · 응답 분석 · 설정

```text
IMP-PLAN 의 "엔진 3단계"만: --concurrency k (스레드 풀, 결과는 끝난 순서로 내보내되 번호 유지),
--max-p95 초 · --max-failures 수 → 마지막 줄 PASS/FAIL, 종료 코드 0/1,
응답 JSON 에 timings 가 있으면 숫자 칸마다 평균 (요약 아래 한 줄),
~/.tbench/profiles.toml: tbench profile save <name> <url> [옵션], tbench profile list, tbench run <name> [-n ...].
가짜 서버 테스트: 지연 0.3초 × 6 에서 k=3 이 k=1 보다 빠름, 기준을 넘으면 종료 코드 1.
```

## 5. 7교시에 볼 것

| 볼 것 | 막혔을 때 한마디 |
| --- | --- |
| TODO · SPEC 없이 에이전트부터 | "요청서로 Doc/TODO.md부터. 확인 방법이 없으면 됐는지 모릅니다" |
| IMP-PLAN이 한 단계짜리 | "엔진과 화면을 나누고, 엔진도 1 · 2 · 3으로. 단계마다 commit" |
| 첫 요청에 14개를 다 넣음 | "IMP-PLAN의 엔진 1단계만" |
| 다 끝난 뒤에야 화면이 나옴 | "worker로 부르고 결과마다 표에 더하게" |
| p95가 max와 늘 같음 | "n이 작으면 그럴 수 있어요. 계산 방법을 테스트로 고정" |
| 테스트가 진짜 n8n을 부름 | "pytest 안에서 가짜 서버" |
| 비교가 다른 요청끼리 | "저장할 때 url · 본문 해시를 같이" |
| `tbench`를 못 찾음 | `uv tool update-shell` 뒤 새 터미널, `uv tool list` |
| 설치한 `tbench`가 예전 코드 | `--editable`로 다시, 또는 `uv tool install --force .` |

### 자주 빠뜨리는 것 (수업 준비 때 예상)

| 빠뜨린 것 | 생기는 일 |
| --- | --- |
| 백분위 계산 방법 | 사람마다 · 실행마다 p95가 달라 비교가 흔들림 |
| 실패도 한 번으로 셈 · 실패 종류 | 연결이 안 되면 프로그램이 멈추거나, 실패가 시간 목록에서 빠져 p95가 좋아 보임 |
| 저장 파일에 조건(url · 본문 해시 · N) | 다른 질문으로 잰 것끼리 비교 (요청서의 "망신") |
| 엔진과 화면 나누기 | `--plain` · `compare` · 종료 코드를 화면 없이 못 씀, 테스트가 어려움 |
| 가짜 서버 | 테스트할 때마다 진짜 헬프데스크 · OpenAI 호출 |
| `[project.scripts]` | `uv tool install`은 되는데 `tbench` 명령이 없음 |
| 저장 · 설정 위치를 집 폴더에 | 다른 폴더에서 실행하면 history · profile이 비어 보임 |

## 6. 강사 바이브 코딩 (8교시, 15분 · 시간 기록)

| 할 것 | 걸린 시간 | 메모 |
| --- | --- | --- |
| 엔진 1단계 + TUI 1단계 + 설치를 위 요청문으로 | (8교시에 잼) | |
| R10 `--max-p95` 종료 코드 (74일차 배포 전 검사의 씨앗) | (8교시에 잼) | |

## 7. 수업 준비 때 직접 만들어 본 본 (10/26, `tbench/`)

| 확인 | 결과 |
| --- | --- |
| `uv run pytest -q` (가짜 서버) | **12 passed** (18.8초): 백분위 · 실패 2/6 · 첫 호출 · warmup · 실패 종류 4가지 · 키 가리기 · compare WARNING · history · log · 동시 · 종료 코드 · timings · profile · TUI 한 줄씩 · `--pick` |
| `uv tool install --editable .` → `cd /tmp && tbench --help` | 됨, `uv tool list`에 `tbench v0.1.0` |
| 진짜 헬프데스크 `my-helpdesk` + `requests/faq-vpn-nocache.json` `-n 5 --plain --save --max-p95 4` | 3.947 · 1.579 · 1.532 · 1.824 · 1.429초, 1번 줄 `first call`. **p50 1.579 · p95 3.947 · max 3.947 · p50 excl. first 1.532**, `PASS` |
| 같은 때 `flow.py bench my-helpdesk requests/faq-vpn-nocache.json -n 5` | p50 1.38 · p95 1.83 · max 1.83초 (바로 앞 tbench가 데워 둠) |

(강사 Mac의 n8n에 올라가 있던 `my-helpdesk`는 규칙 분류 · 코드 검사가 들어간 판이라 `llm_calls` 1, `timings`에 `classify_ms`가 없음.)

만들며 알게 된 것 (학생이 막힐 만한 곳):

| 알게 된 것 | 정한 방법 |
| --- | --- |
| n이 작으면 p95 = max (위 실측: 5번이면 p95는 5번째 = 첫 호출 3.9초) | nearest-rank 그대로 두고, 첫 호출 제외 p50과 `--warmup`으로 따로 봄 (⑥) |
| `profile save`에 키를 넣으면 "남기는 파일에 키가 찍히면 안 돼요"와 부딪힘 | 키 머리글은 `$MY_KEY`처럼 환경 변수로만 저장, 글자 키는 `***`로 바꾸고 안내 (숨은 요구) |
| 응답마다 `timings` 칸이 다름 (규칙 길은 `classify_ms` 없음) | 칸마다 그 칸이 있는 응답끼리 평균 |
| 동시(`--concurrency`)면 결과가 끝난 순서로 옴 | 번호(`i`)는 보낸 순서로 유지, 저장은 번호순 |
| 본문 해시를 JSON을 다시 쓴 글자로 내면 같은 파일도 해시가 달라질 수 있음 | 파일 글자 그대로 보내고 그 글자로 해시 |
| TUI 테스트 | Textual `run_test()` + 가짜 서버 지연 0.5초: 1.3초 뒤 1~5줄, 끝나면 6줄 |

