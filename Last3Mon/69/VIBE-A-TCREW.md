# 7교시 바이브 코딩 · `tcrew` 만들기

> **정답본** · 수업이 끝난 뒤(8교시 뒤) 학생 저장소에 올립니다. 그 전에는 올리지 않습니다. 요청서는 [VIBE-REQ-TCREW.md](VIBE-REQ-TCREW.md), 문제는 [VIBE-Q-TCREW.md](VIBE-Q-TCREW.md).
> 68일차부터 바이브 코딩 프로그램은 **수업 준비 때 미리 만들어 보지 않습니다.** 아래 요청문과 확인 기준은 예시이고, 걸린 시간은 8교시 강사 바이브 코딩(2026-10-21)에서 재지 않아 기록이 없습니다.

- 요구 R1~R5는 학생용과 같습니다.

## 요청서 → 요구 도출 예 (`SPEC.md` 예)

요청서의 말을 **확인할 수 있는 요구**로 바꾼 예입니다. 정답이 하나는 아닙니다. "됐다 / 안 됐다"를 말할 수 있는지가 기준입니다.

### 1. 요구

| 번호 | 요구 | 요청서의 말 | 확인 방법 |
| --- | --- | --- | --- |
| R1 | `crew.yaml`의 `roles` 순서대로 LLM을 부르고, 역할마다 `input`(질문 · 앞 역할 이름)에 적힌 것을 넘긴다 | ① | 가짜 LLM: 호출 순서 `writer, reviewer, editor`, editor 입력에 writer 답 |
| R2 | 역할마다 탭, 탭 제목에 이름 · ✔/✘ · 초 | ② | 질문 하나 → 탭 3개 (고쳐 쓰면 `writer#2`까지 5개) |
| R3 | 검토 답 첫 줄 `PASS`면 다음, `FIX`면 작성자 1번 다시 + 다시 검토, 그래도 `FIX`면 `review_failed`로 멈춤. 첫 줄이 둘 다 아니면 `FIX` | ③ | 늘 FIX 가짜 LLM: 호출 4번(`writer, reviewer, writer#2, reviewer#2`) 뒤 멈춤, editor 없음. 이상한 답 가짜 LLM: 통과 안 함 |
| R4 | 역할 이름 · 개수를 코드에 쓰지 않음 | ④ | `translator`를 더한 YAML → 코드 수정 없이 탭 4개 |
| R5 | 실행마다 `runs/<시각>.json`: 역할마다 `role`, `input`, `output`, `seconds`, 전체 `status` | ⑤ | 한 번 돌리면 파일 1개, 역할 수만큼 항목 |

### 2. 숨은 요구

- 검토 답의 모양: 첫 줄 `PASS` / `FIX` (또는 JSON `{"passed": ...}`). 오늘 n8n 검토자의 `passed`와 같은 역할.
- 가짜 LLM: 역할 이름을 붙여 입력을 되돌려 주는 것, 늘 `FIX`, 이상한 답 세 가지. 테스트는 진짜 LLM을 부르지 않음.
- 고쳐 쓰기 입력: 처음 질문 + 이전 초안 + 검토 의견 (n8n `previous_draft`, `feedback`).
- `max_revisions`는 YAML, 코드는 그 숫자를 지킴.
- 키: `OPENAI_API_KEY` 환경 변수만. `runs` 파일에 환경 변수 · 헤더를 넣지 않음 (`grep -r sk- runs/` → 없음).
- 화면: LLM 호출은 worker에서, 끝난 역할부터 탭 채우기.

### 3. 범위 밖

n8n 웹훅 연결, 여러 질문 한꺼번에, 역할마다 다른 회사의 LLM. (강사 바이브 코딩에서 writer를 `my-writer` 웹훅으로 바꿔 끼우기를 보여 줌)

### 4. 순서와 이유

1. YAML → 역할 목록 + 가짜 LLM + 차례로 부르기 (`--plain`). 화면 · 기록 · 고쳐 쓰기가 **모두 이 실행 결과 목록을 씀**.
2. 검토 · 고쳐 쓰기 · 기록 (R3 · R5). 가장 틀리기 쉬운 규칙(멈춤, 모르면 FIX)을 화면 없이 테스트로 먼저 확인.
3. TUI 탭 (R2 · R4). 결과 목록을 탭으로 보여 주기만 하면 됨.

### 자주 빠뜨리는 것 (수업 준비 때 예상)

| 빠뜨린 것 | 생기는 일 |
| --- | --- |
| 검토 답의 모양 | 프로그램이 "고칠 것 있음"을 못 읽어 늘 통과 (가장 위험) |
| 모르면 FIX | 검토 LLM이 "좋습니다만 …"처럼 답하면 통과로 처리됨 |
| 확인 방법의 숫자 (호출 몇 번) | "한 번만 고쳐 쓰기"가 됐는지 확인할 방법이 없음 |
| 가짜 LLM | 테스트할 때마다 진짜 LLM 호출, 늘 FIX인 검토자를 만들 수 없음 |

## 확인 기준

| 요구 | 기준 |
| --- | --- |
| R1 | 가짜 LLM 테스트: 역할 3개 → 호출 순서 `writer, reviewer, editor`, editor 입력에 writer 답이 들어 있음 |
| R3 | 검토자 지시문을 "항상 FIX"로 바꾸면 호출 순서 `writer, reviewer, writer, reviewer` 다음 멈춤 (`editor` 없음), 화면에 "검토 실패" |
| R3 | 검토 답이 정해진 모양이 아니면 통과로 보지 않음 (fail-closed) |
| R4 | `translator` 역할 추가 → 코드 수정 없이 탭 4개 |
| R5 | `runs/<시각>.json`에 역할마다 `role`, `input`, `output`, `seconds` |
| 비밀 | `OPENAI_API_KEY` 환경 변수만, YAML·코드·runs 파일에 키 없음 |

## 단계별 요청문 예

### 1. YAML과 차례로 부르기

```text
~/vibe/tcrew 에 Python 프로젝트를 만들어 줘. uv 사용, 패키지·명령 이름 tcrew, 코드와 화면 글자는 영어.
이번 단계는 TUI 없이 --plain 글자 출력만.
- crew.yaml 예:
  model: gpt-4.1-mini
  max_revisions: 1
  roles:
    - name: writer
      prompt: "Write a short Korean IT notice from the user's facts only. Keep dates and times exactly."
      input: question
    - name: reviewer
      kind: review
      prompt: "Check the draft against the facts. First line PASS or FIX, then one issue per line."
      input: [question, writer]
    - name: editor
      prompt: "Rewrite the approved notice as a 2-line messenger message in Korean."
      input: writer
- tcrew/crew.py: YAML을 읽어 Role 목록으로 (pydantic 또는 dataclass), 잘못된 YAML은 알기 쉬운 오류.
- tcrew/llm.py: LLM 인터페이스 complete(system, user) -> str. OpenAI 구현(키는 OPENAI_API_KEY)과 테스트용 FakeLLM.
- tcrew/run.py: 역할 순서대로 부르고 결과 목록 [{role, input, output, seconds}].
- pytest: FakeLLM 으로 호출 순서와 입력 전달 확인.
```

### 2. 검토 · 고쳐 쓰기 · 기록

```text
run.py 에 검토를 더해 줘.
- kind: review 인 역할의 답 첫 줄이 PASS 면 다음 역할로, FIX 면 그 앞의 작성 역할을 한 번 더 부른다
  (입력: 처음 질문 + 이전 초안 + 검토 의견, 역할 이름은 writer#2). 그 뒤 다시 검토.
- 고쳐 쓰기는 crew.yaml 의 max_revisions 번까지. 그래도 FIX 면 멈추고 status "review_failed".
- 첫 줄이 PASS/FIX 가 아니면 FIX 로 본다 (통과로 보지 않음).
- 실행 기록을 runs/<YYYYmmdd-HHMMSS>.json 에 저장 (키 값은 넣지 않음).
- pytest: FakeLLM 으로 PASS 경로, FIX→PASS 경로, 항상 FIX 경로(호출 4번 후 멈춤), 이상한 답 경로.
```

### 3. TUI 탭

```text
Textual TUI 를 붙여 줘. run.py 는 그대로 다시 써.
- 위: TabbedContent, 역할마다 탭 (제목: 이름 ✔/✘ 시간). 고쳐 쓰기는 writer#2 탭.
- 아래: 질문 입력칸, Enter 로 실행. 실행은 worker 로, 끝난 역할부터 탭을 채운다.
- 명령줄: tcrew "질문" (TUI), tcrew "질문" --plain (글자), tcrew --crew other.yaml.
- 역할 이름을 코드에 박지 말고 YAML 에서만 읽는다. translator 역할을 더한 tests/data/crew4.yaml 로 탭 4개 테스트(run_test).
```

## 7교시에 볼 것

| 볼 것 | 막혔을 때 한마디 |
| --- | --- |
| 검토 답을 프로그램이 못 읽음 | "첫 줄을 PASS/FIX 로 정하고, 아니면 FIX 로 보게 하세요" |
| 끝없이 고쳐 씀 | "max_revisions 를 YAML 에, 코드가 지키게" |
| 역할 이름이 코드에 있음 | "translator 를 YAML 에만 넣고 돌려 보세요" |
| 테스트가 진짜 LLM 부름 | "FakeLLM 으로" |
| 키가 runs 파일에 들어감 | "기록에서 환경 변수는 빼라고" |
