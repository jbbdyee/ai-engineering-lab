# 7교시 바이브 코딩 · `turl` 만들기

> **강사용 정답본** · 학생 저장소에 올리지 않습니다. 학생용 문제는 [VIBE-Q-TURL.md](VIBE-Q-TURL.md).
> 이 정답본의 요청문은 예시입니다. 수업 준비 때 미리 만들어 보지 않았고, 걸린 시간은 8교시 강사 바이브 코딩에서 재어 기록합니다.

## 확인 기준

| 요구 | 기준 |
| --- | --- |
| R1 | 테스트용 가짜 서버(httpx MockTransport 등)로 상태 · 시간 · 본문 확인. 실제 `my-meeting`에 `weekly.json` → 200, `count` 4 |
| R2 | `requests/empty.json` 불러와 보내면 400 `{"error": "notes are required"}` |
| R3 | `~/.local/share/turl/history.json`(예)에 저장, `Authorization` 같은 헤더 값은 가려서 저장 |
| R4 | 만든 curl 명령을 셸에서 실행해 같은 상태 코드 |
| R5 | 꺼진 주소 → "연결 실패", 시간 초과, HTML 응답 → 글자 그대로 |

## 단계별 요청문 예

### 1. 글자로 보내기

```text
~/vibe/turl 에 Python 프로젝트를 만들어 줘. uv 사용, 패키지·명령 이름 turl, 코드와 화면 글자는 영어. 이번 단계는 TUI 없이.
- turl/client.py: send(method, url, headers, body) -> Result(status, seconds, headers, text, json_or_none, error_or_none). httpx 사용, timeout 30초.
- turl send <METHOD> <URL> [--header K:V ...] [--body '<json>' | --body-file <path>]: 상태 · 시간 · 본문(JSON이면 들여쓰기) 출력.
- pytest: httpx.MockTransport 로 200 JSON, 400, 비 JSON, 연결 실패.
```

### 2. TUI

```text
Textual TUI 를 붙여 줘. client.py 는 그대로 다시 써.
- 위: 메서드 Select(GET POST PUT DELETE), URL Input, 보내기 Button.
- 왼쪽: TabbedContent (Body TextArea, Headers TextArea 'K: V' 줄), 오른쪽: 응답 패널 (제목에 상태 · 시간).
- 보내기는 worker 로 (화면이 멈추지 않게). [파일에서 Body 불러오기] 는 경로 입력 후 읽기.
- 화면 테스트는 run_test 로 하나 (가짜 client).
```

### 3. 기록 · curl · 오류

```text
- History 탭: 보낸 요청(메서드, URL, 헤더, Body, 상태, 시각)을 ~/.local/share/turl/history.json 에 최근 50개. 고르면 다시 불러옴.
  Authorization, Cookie, X-Api-Key 값은 '***' 로 바꿔 저장.
- [curl 명령으로 복사]: shlex.quote 로 따옴표 처리한 curl 명령을 만들고 클립보드(가능하면) + 화면에 표시.
- 오류(연결 실패, 시간 초과, 잘못된 URL)는 응답 패널에 빨간 글자로. 프로그램은 계속.
- pytest: curl 명령 만들기(한국어·따옴표·줄바꿈 Body), 기록에서 비밀 헤더 가리기.
```

## 7교시에 볼 것

| 볼 것 | 막혔을 때 한마디 |
| --- | --- |
| 한 번에 TUI까지 | "1단계는 글자로 보내기만" |
| 테스트가 진짜 서버를 부름 | "가짜 서버(MockTransport)로" |
| 보내는 동안 화면이 멈춤 | "worker 로 보내라고" |
| curl 명령이 한국어 Body에서 깨짐 | "만든 명령을 실제로 실행해 보게" |
| 비밀 헤더가 기록에 그대로 | "저장할 때 가리게" |
