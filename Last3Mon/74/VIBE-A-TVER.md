# 7교시 바이브 코딩 · `tver` 정답본

> **강사용 정답본** · 학생 저장소에는 수업 뒤에 올립니다. 학생용은 [VIBE-REQ-TVER.md](VIBE-REQ-TVER.md)(요청서) → [VIBE-Q-TVER.md](VIBE-Q-TVER.md).
> 강사가 직접 만든 본: [tver/](tver/README.md) (2026-10-27, Claude Code가 아래 SPEC · IMP-PLAN을 보고 직접 씀, 테스트 11개). CLI 에이전트에 아래 요청문을 보내 재지는 않았습니다. 강사 바이브 코딩 시간은 6절에 수업 때 적습니다.

## 1. `Doc/TODO.md` 예

```markdown
# tver TODO

## 만들고 싶은 것
어느 폴더에서나 `tver`로 n8n 워크플로우를 git에 버전으로 남기고, 두 버전을 노드 단위로 비교해
바뀐 것을 모델 · 지시문 · 흐름으로 나눠 보여 주는 도구. 화면(TUI)도, 다른 프로그램용 결과도.

## 요청의 말 → 할 일
| # | 요청의 말 | 할 일 | 꼭 · 나중 |
| --- | --- | --- | --- |
| ① | 노드 단위 비교 | 이름으로 짝지어 더함 · 뺌 · 바뀐 설정 · 연결 | 꼭 |
| ② | 뜻 없는 차이 빼기 | 위치 · id · 순서는 비교에서도 저장에서도 뺌 | 꼭 |
| ③ | 어느 문장이 | 긴 글은 줄 단위 | 꼭 |
| ④ | 셋으로 나눠 한 줄 | 모델 · 지시문 · 흐름 개수 | 꼭 |
| ⑤ | 버전으로, 같으면 저장 X | git 커밋, 요약을 메시지로 | 꼭 |
| ⑥ | 목록 · 두 버전 비교 | log, 두 커밋 비교 | 꼭 |
| ⑦ | 키가 있으면 저장 X | 키 모양을 찾으면 거부, 메시지도 가려서 | 나중 |
| ⑧ | 화면에서 | 목록 · 트리 · 자세히 | 꼭 |
| ⑨ | n8n에서 바로 | 컨테이너에서 내보내 모두 저장 (읽기만) | 나중 |
| ⑩ | 예전 버전을 파일로 | 꺼내기만, 올리는 건 사람 | 나중 |
| ⑪ | 다른 프로그램이 읽게 | JSON, 종료 코드 | 나중 |
| ⑫ | 이름만 바뀐 것 | renamed | 나중 |
| 끝 | 폴더 → 워크플로우만 | nodes · connections가 있는 것만 | 나중 |
| 끝 | n8n을 망가뜨리지 않기 | 저장소는 따로, n8n에 쓰지 않음 | 꼭 |

## 걱정되는 것
- 저장할 때도 정리해야 "같다"를 알 수 있다
- 이름에 공백 · 한글 · `/`가 있는 워크플로우의 파일 이름
- 키를 거부할 때 메시지에 키가 그대로 나오면 안 됨
```

## 2. `Doc/SPEC.md` 요점

VIBE-Q의 요구 표(R1~R14)와 같습니다. 학생 SPEC과 비교할 때 자주 빠지는 것:

| 자주 빠지는 것 | 왜 필요한가 |
| --- | --- |
| R2를 **저장에도** 적용 (정리한 글로 저장) | 그래야 R5 "같으면 저장 안 함"이 글자 비교로 되고 저장소의 git diff도 읽힘 |
| 분류 규칙을 글로 정해 둠 | 정해 두지 않으면 에이전트가 웹훅 경로를 "모델"로 세기도 함 |
| R10 꺼내기가 저장소를 바꾸지 않음 | 꺼낼 때마다 버전이 생기면 목록이 엉킴 |
| 테스트 저장소는 `tmp_path` | 진짜 `~/.tver/store`가 테스트로 더러워짐 |
| 종료 코드 (diff 0 · 1, 오류 2) | 배포 전 검사(게이트)에서 씀 |

## 3. `Doc/IMP-PLAN.md`

[tver/Doc/IMP-PLAN.md](tver/Doc/IMP-PLAN.md) — 엔진 1단계(R1~R4) → 엔진 2단계(R5 · R6) → TUI 1단계(R8) → 설치(R14) → 엔진 3단계(R7 · R11 · R13) → 엔진 4단계(R9 · R10 · R12).

## 4. 단계별 요청문 예

### 엔진 1단계

```text
Doc/SPEC.md 와 Doc/IMP-PLAN.md 를 읽고 "엔진 1단계"만 만들어 줘. uv 프로젝트, 명령 이름 tver, 코드와 화면 글자는 영어.
- workflow.clean(): 노드에서 id, position, webhookId 와 내보내기 도장(versionId, updatedAt ...)을 빼고 노드를 name 순으로. dumps() 는 키 정렬 JSON.
- diff.compare(old, new): 노드를 name 으로 짝지어 +node, -node, ~set(점 경로 key, before, after), +link, -link.
  80자 넘거나 여러 줄인 값은 difflib 줄 diff 를 lines 에.
- category: Chat model 노드의 parameters.model.value 는 model, systemMessage · text · jsCode 는 prompt, 나머지와 연결은 flow.
  summary 한 줄 "N change(s) · model N · prompt N · flow N".
- tver diff a.json b.json. tests: tests/data 의 helpdesk-v1 → v2 가 7개 · model 1 · prompt 1 · flow 5,
  위치 · id 를 바꾸고 노드 순서를 뒤집은 파일은 0개, systemMessage 의 lines 에 "[FAQ-003]" 이 있는 + 줄.
끝나면 IMP-PLAN 체크를 표시하고 확인 명령을 알려 줘.
```

### 엔진 2단계

```text
엔진 2단계만: Store(repo, 기본 ~/.tver/store, --repo, $TVER_REPO).
- save(파일): dumps 한 글이 저장소의 같은 이름 파일과 같으면 "no change", 다르면 쓰고 git commit. 메시지 "<이름>: " + 바로 전 버전과의 summary 한 줄 (처음이면 new).
- log(이름): 커밋 · 시각 · 메시지. show(rev, 이름): git show rev:이름. tver diff <rev1> <rev2> <이름>.
- tests 는 tmp_path 저장소만: 두 번 저장 → 1개, v2 로 바꿔 저장 → 메시지에 "model 1 · prompt 1 · flow 5".
```

### TUI 1단계

```text
TUI 1단계만: tver <파일> 이면 Textual 화면. 왼쪽 ListView 버전 목록, 오른쪽 Tree(노드 → 바뀐 것, 고른 버전 vs 바로 전 버전, worker 로 비교),
트리의 잎을 고르면 아래 Static 에 줄 diff 또는 전 · 후. [s] 지금 파일을 버전으로 저장하고 목록을 다시, [q] 끝.
엔진(diff · store)은 고치지 말고 불러 쓰기만. pytest 로 [s] 뒤 목록이 하나 늘고 트리 제목에 요약이 나오는지.
```

## 5. 결과 확인 (강사 본, 2026-10-27)

| 요구 | 확인 | 결과 |
| --- | --- | --- |
| R1 · R3 · R4 | `tver diff reference/helpdesk-v1.json reference/helpdesk-v2.json` | 7줄 (`flow.py diff`와 같음), systemMessage 줄 diff, `model 1 · prompt 1 · flow 5` |
| R2 | 위치 · id · 순서만 바꾼 파일 (pytest) | 0개 |
| R5 · R6 | 같은 파일 두 번 save → `log` | 1개, 바꿔 저장 → 2개 |
| R7 | 가짜 키(테스트 안에서 만듦)를 넣고 save | 거부, 메시지에 원래 값 없음 |
| R8 | pytest `run_test` | `[s]` 뒤 목록 2개, 트리 제목 요약 |
| R9 | `tver pull` (강사 n8n) | 192 new version(s) |
| R10 | `restore` → 원본과 `diff` | 0 change(s), 버전 수 그대로 |
| R11 | `diff a a` · `a b` · 없는 파일 | 0 · 1 · 2 |
| R12 | `Search FAQ` → `Find FAQ` (pytest) | `renamed` 1개 |
| R13 | `tver save answers` | 5개 저장, golden 테스트 파일 skipped |
| R14 | `uv tool install --editable .`, `/tmp`에서 `tver --help` | 됨 |

오늘 Lab의 helpdesk 정답 여섯 단계를 차례로 저장했을 때의 `log` (위가 최신):

```text
87090f0  helpdesk.json: 1 change(s) · model 0 · prompt 1 · flow 0        ← Lab 03 예제 2 (카나리: Pick release의 jsCode)
9e2ac9a  helpdesk.json: 14 change(s) · model 0 · prompt 2 · flow 12      ← Lab 02 과제 2 (응답 코드 · 400)
e0dc13e  helpdesk.json: 15 change(s) · model 1 · prompt 1 · flow 13      ← Lab 02 예제 1 (릴리스를 밖에서)
b8461aa  helpdesk.json: 12 change(s) · model 0 · prompt 2 · flow 10      ← Lab 01 과제 2 (기본 지시문)
76c5e18  helpdesk.json: 6 change(s) · model 0 · prompt 2 · flow 4        ← Lab 01 과제 1 (지시문 저장소)
7c337b5  helpdesk.json: new                                               ← Lab 01 예제 2
```

- 풀이 거리: 카나리(87090f0)는 `Pick release`의 **Code** 한 칸이라 "prompt 1"로 셉니다. 규칙상 `jsCode`를 지시문으로 셌기 때문입니다. 코드와 지시문을 나눠 세고 싶으면 `code` 분류를 하나 더 두면 됩니다 — 분류 규칙은 **팀이 정하는 것**이라는 예.

## 6. 강사 바이브 코딩 (8교시, 수업 때 적음)

| 주제 | 요청문 요지 | 걸린 시간 · 결과 |
| --- | --- | --- |
| 게이트 붙이기 | "tver save 전에 지정한 테스트 파일로 flow.py gate 를 돌려 FAIL 이면 저장 안 함" | |
| 지시문만 따로 | "systemMessage 를 꺼내 prompts/<노드>.md 로 저장, 지시문 diff 만 보기" | |
| 코드 분류 | "jsCode 는 prompt 가 아니라 code 로 따로 세기" | |
