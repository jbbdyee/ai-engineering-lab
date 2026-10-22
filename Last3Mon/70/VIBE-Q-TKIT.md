# 7교시 바이브 코딩 · `tkit` 만들기

- 시간: 16:00~16:50 (50분) · 발표와 정리는 8교시
- 도구: CLI 코딩 에이전트(codex / claude / agy), Python + uv + [Textual](https://textual.textualize.io/)
- 결과물: **템플릿 폴더**를 고르고 변수를 채우면 새 파일들을 만들어 주는 TUI (cookiecutter 방식). 오늘 만든 공지 키트·모듈을 템플릿으로 만들어, 새 업무(예: 교육 신청 확인 메일)의 n8n 워크플로우와 테스트 파일을 몇 초 만에 만듭니다.

```text
$ tkit ~/vibe/templates
┌ tkit ─────────────────────────────────────────────────────────┐
│ 템플릿         │ n8n-notice-kit                                │
│ ▸ n8n-notice-kit │ name        : [ training-mail          ]   │
│   python-tui   │ webhook_path: [ my-training-mail        ]   │
│                │ prefix      : [ [교육 신청 확인]         ]   │
│                │ max_length  : [ 400                     ]   │
│                │ 만들 파일: my-work/training-mail.json,        │
│                │           cases/training-mail.json            │
│                │ [미리 보기]  [만들기]                          │
└───────────────────────────────────────────────────────────────┘
```

> 요청문은 **직접** 씁니다. 단계마다 `▶` 를 펼치면 생각할 거리가 나옵니다. 정답 요청문은 없습니다.

## 요구 사항

| 번호 | 요구 | 확인 방법 |
| --- | --- | --- |
| R1 | 템플릿 = 폴더 하나. 안에 `template.yaml`(변수 이름 · 설명 · 기본값 · 종류)과 파일들. 파일 내용과 **파일 이름**의 `{{ 변수 }}`를 채운다 | `tkit render <템플릿> --set name=x ...` (글자 모드) |
| R2 | 변수 종류를 검사한다 (숫자 칸에 글자, 필수 칸 비움, 웹훅 경로에 빈칸) | 잘못된 값 넣기 |
| R3 | 만들기 전에 **미리 보기**: 만들 파일 목록과 내용. 이미 있는 파일은 덮어쓰지 않고 알린다 | 같은 이름으로 두 번 |
| R4 | TUI: 왼쪽 템플릿 목록, 오른쪽 변수 입력칸(`template.yaml`에서 자동), 미리 보기 · 만들기 | `tkit ~/vibe/templates` |
| R5 | n8n 템플릿으로 만든 JSON이 **유효한 JSON**인지 만든 뒤 확인한다 (가능하면 `flow.py check`도) | 만든 파일 |

알아 둘 것:

- 템플릿 재료: 오늘 `my-work/notice-kit.json`(또는 `reference/lab02-example2-kit-module.json`)과 `cases/lab01.json`. 바뀌어야 할 값(이름, 웹훅 경로, 머리말, 길이)을 `{{ name }}`처럼 바꿔 두면 템플릿이 됩니다.
- JSON 안에는 n8n 표현식 `{{ $json... }}`이 이미 들어 있습니다. 템플릿 변수와 **겹치면** 안 됩니다. 이 점이 오늘 가장 까다로운 곳입니다.
- LLM은 쓰지 않아도 됩니다 (키 없이 끝까지 가능).

## 진행 (50분)

```mermaid
flowchart LR
  S0["0. 준비 · 템플릿 폴더<br/>5분"] --> S1["1. 글자 모드로 채우기<br/>R1·R2 · 15분"] --> S2["2. 미리 보기 · 덮어쓰기 · 검사<br/>R3·R5 · 10분"] --> S3["3. TUI<br/>R4 · 13분"] --> S4["4. 정리<br/>7분"]
```

### 0. 준비와 템플릿 폴더 (5분)

```bash
mkdir -p ~/vibe/tkit ~/vibe/templates && cd ~/vibe/tkit
git init
codex        # 또는 claude, agy
```

템플릿 하나는 **직접** 만듭니다: `~/vibe/templates/n8n-notice-kit/`에 오늘 키트 JSON을 복사하고, 바뀔 값을 변수로 바꾸고, `template.yaml`에 변수 목록을 씁니다.

<details><summary>▶ 1단계 · 무엇을 변수로</summary>

Lab 01에서 찾은 "종류마다 다른 것"이 변수 후보입니다. 노드 이름, 노드 연결처럼 **흐름**을 바꾸는 값은 변수로 두지 않는 편이 안전합니다 (템플릿이 망가지기 쉬움).
</details>

### 1. 글자 모드로 채우기 (15분)

**목표**: `uv run tkit render ~/vibe/templates/n8n-notice-kit --set name=training-mail --set ... --out /tmp/x`가 파일을 만든다.

<details><summary>▶ 1단계 · `{{ }}`가 두 가지</summary>

템플릿 변수 `{{ name }}`과 n8n 표현식 `{{ $json.body.facts }}`가 한 파일에 섞입니다. 둘을 어떻게 구분하게 할까요? (변수 표시를 다른 모양으로 정하기, 정해진 변수 이름만 바꾸기, 템플릿 엔진의 escape 기능 등) 요청문에 **반드시** 이 문제를 적습니다.
</details>

<details><summary>▶ 2단계 · 테스트할 것</summary>

n8n 표현식이 그대로 남는지, 파일 이름의 변수도 바뀌는지, 숫자 변수가 JSON에서 숫자로 들어가는지. 작은 가짜 템플릿 폴더를 테스트용으로 만들게 합니다.
</details>

**확인**: 만든 JSON을 `python -m json.tool`로 열기, `uv run pytest -q`, `git commit`.

### 2. 미리 보기 · 덮어쓰기 · 검사 (10분)

<details><summary>▶ 1단계 · 덮어쓰기</summary>

내가 고쳐 둔 `my-work/notice-kit.json`을 템플릿이 덮어쓰면 오늘 작업이 사라집니다. 이미 있으면 어떻게 할지(멈춤, 다른 이름, `--force`일 때만) 정합니다.
</details>

<details><summary>▶ 2단계 · 만든 뒤 검사</summary>

만든 파일이 n8n 워크플로우라면 `uv run ~/aio-01d4-stu/Last3Mon/70/tools/flow.py check <파일>`을 부르게 할 수 있습니다 (그 폴더에서 실행해야 하는지 확인). 실패하면 화면에 그대로 보여 줍니다.
</details>

### 3. TUI (13분)

**목표**: 템플릿 목록, `template.yaml`에서 자동으로 만든 입력칸, 미리 보기와 만들기 버튼 (R4).

<details><summary>▶ 1단계 · 입력칸은 YAML에서</summary>

변수가 늘 때마다 화면 코드를 고치지 않으려면? `tflow`·`tcrew`에서 했던 "데이터 모양과 화면을 나누기"와 같습니다.
</details>

**확인**: TUI로 `training-mail`을 만들고, 그 파일을 `flow.py push`, `call` 해 봅니다 (Lab 폴더에서).

### 4. 정리 (7분)

| 발표 (3분) | 내용 |
| --- | --- |
| 요청문 | 가장 잘 먹힌 요청문 한 개, 안 먹힌 요청문 한 개 |
| 막힌 곳 | `{{ }}` 충돌, 숫자/글자, 덮어쓰기를 어떻게 알아챘고 고쳤나 |
| 시연 | 템플릿으로 새 워크플로우를 만들어 n8n에 올리고 호출 |

## 확인

- [ ] R1 템플릿 폴더 + `template.yaml`, 내용과 파일 이름의 변수를 채운다. n8n 표현식은 그대로.
- [ ] R2 잘못된 변수 값을 알려 준다.
- [ ] R3 미리 보기, 있는 파일은 덮어쓰지 않는다.
- [ ] R4 TUI 입력칸이 YAML에서 만들어진다.
- [ ] R5 만든 JSON이 유효하다 (가능하면 `flow.py check` 통과).
- [ ] `uv run pytest -q`, 단계마다 git commit, `PROMPTS.md`.
