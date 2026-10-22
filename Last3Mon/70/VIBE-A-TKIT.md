# 7교시 바이브 코딩 · `tkit` 만들기

> **강사용 정답본** · 학생 저장소에 올리지 않습니다. 학생용 문제는 [VIBE-Q-TKIT.md](VIBE-Q-TKIT.md).
> 68일차부터 바이브 코딩 프로그램은 **수업 준비 때 미리 만들어 보지 않습니다.** 아래 요청문과 확인 기준은 예시이고, 걸린 시간은 8교시 강사 바이브 코딩에서 재어 기록합니다.

## 확인 기준

| 요구 | 기준 |
| --- | --- |
| R1 | 가짜 템플릿 테스트: `{{ name }}`은 바뀌고 `{{ $json.body.facts }}`는 그대로. 파일 이름 `{{ name }}.json` → `training-mail.json` |
| R1 | 숫자 변수 `max_length: 400`이 JSON에서 `400`(숫자) |
| R2 | `max_length=abc` → 오류, 필수 `webhook_path` 빈칸 → 오류, `webhook_path=my mail` → 오류(빈칸) |
| R3 | 두 번째 만들기에서 "이미 있음" 목록, 아무 파일도 바뀌지 않음 |
| R5 | 만든 JSON `json.loads` 성공. Lab 폴더의 `flow.py check` 통과 |

## 단계별 요청문 예

### 1. 글자 모드

```text
~/vibe/tkit 에 Python 프로젝트를 만들어 줘. uv 사용, 명령 이름 tkit, 코드와 화면 글자는 영어.
이번 단계는 TUI 없이 `tkit render <template_dir> --set k=v ... --out <dir>` 만.
- 템플릿 = 폴더. template.yaml: variables: [{name, description, default, type: str|int|path_slug, required}].
- 템플릿 변수 표시는 [[ name ]] 로 한다 (n8n 표현식 {{ }} 와 겹치지 않게). 파일 내용과 파일·폴더 이름 모두.
  정의되지 않은 [[ x ]] 가 남으면 오류.
- int 변수는 따옴표 없이 들어갈 자리에 쓰도록 템플릿에서 정한다 (예: "max_length": [[ max_length ]]).
- tkit/template.py: 읽기·검사·채우기 (파일 쓰기 없이 {경로: 내용} 돌려줌). tkit/cli.py: 쓰기.
- pytest: tests/data/fake-template 으로 변수 치환, {{ $json }} 보존, 파일 이름 치환, int, 정의 안 된 변수 오류.
```

### 2. 미리 보기 · 덮어쓰기 · 검사

```text
- tkit render 에 --dry-run: 만들 파일 목록과 내용 앞 20줄만 출력.
- out 폴더에 같은 파일이 있으면 만들지 않고 목록을 보여 주고 끝 (--force 일 때만 덮어씀).
- 변수 검사: int 는 숫자, path_slug 는 [a-z0-9-]+, required 는 비면 안 됨. 모든 오류를 한 번에 보여 줌.
- 만든 .json 은 json.loads 로 확인. --check-cmd "uv run tools/flow.py check {file}" 를 주면 그 명령을 out 폴더 기준으로 실행해 결과를 보여 줌.
```

### 3. TUI

```text
Textual TUI: 왼쪽 템플릿 목록(인자로 준 폴더의 하위 폴더), 오른쪽 template.yaml 변수마다 Input(설명은 placeholder, 기본값 채움).
[미리 보기] 는 --dry-run 과 같은 내용을 아래 패널에, [만들기] 는 render. 오류는 칸 옆에 빨간 글자.
template.py 를 그대로 다시 써. 화면 테스트는 run_test 로 하나.
```

## 템플릿 예 (`~/vibe/templates/n8n-notice-kit/template.yaml`)

```yaml
variables:
  - {name: name, description: "file name", type: path_slug, required: true}
  - {name: webhook_path, description: "n8n webhook path", type: path_slug, required: true}
  - {name: prefix, description: "title prefix", type: str, default: "[안내]"}
  - {name: max_length, description: "max characters", type: int, default: 600}
```

## 7교시에 볼 것

| 볼 것 | 막혔을 때 한마디 |
| --- | --- |
| n8n 표현식까지 바뀌어 JSON이 깨짐 | "템플릿 변수 표시를 다른 모양으로" |
| 숫자가 "400"(글자)으로 들어감 | "int 변수는 따옴표 없는 자리에" |
| 만들 때마다 덮어씀 | "있으면 멈추고 알려 주게" |
| 화면 코드에 변수 이름이 박힘 | "template.yaml 에서 입력칸을 만들게" |
