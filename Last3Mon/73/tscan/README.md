# tscan · 강사가 수업 준비 때 직접 만든 본 (2026-10-26)

> **정답 자료** · 학생 저장소에는 수업 뒤 [VIBE-A-TSCAN.md](../VIBE-A-TSCAN.md)와 함께 올립니다.
> 이 본은 강사가 CLI 에이전트에 단계 요청문을 보내 만든 것이 아니라, Claude Code가 VIBE-A의 SPEC · IMP-PLAN을 보고 직접 썼습니다. 학생이 만든 것과 파일 구성이 달라도 됩니다. 요구 R1~R14의 **확인 방법**이 같으면 됩니다.

## 설치 · 실행

```bash
cd ~/aio-01d4-stu/Last3Mon/73/tscan
uv sync && uv run pytest -q              # 가짜 비밀 테스트 12개 (가짜 값은 테스트 안에서 만듦)
uv tool install --editable .             # 어느 폴더에서나 tscan (R14)
cd /tmp && tscan --help
```

| 하고 싶은 것 | 명령 |
| --- | --- |
| 폴더 검사 (글자) | `tscan scan <폴더> --plain` · 요약 `--summary` · 다른 프로그램용 `--json` |
| 화면(TUI) | `tscan <폴더>` (`[i]` 무시 목록에, `[r]` 다시, `[q]` 끝) |
| 커밋 전 검사 | `tscan staged` (찾으면 종료 코드 1) |
| 훅 | `tscan install-hook` · `tscan uninstall-hook` (남의 훅은 건드리지 않음) |
| 지난 커밋 | `tscan history --max 200` |
| 무시 | `.tscanignore`: `path:line` · `kind:glob` · `glob` |
| 사용자 모양 | `.tscan.toml` 또는 `~/.tscan/rules.toml`: `[[rule]] name = "employee_id"`, `pattern = 'E-\d{6}'` |

종료 코드: 0 없음, 1 찾음, 2 오류 (저장소가 아님, 남의 훅).

## 파일

| 파일 | 하는 일 |
| --- | --- |
| `src/tscan/scanner.py` | 종류별 정규식(경계), 가리기, 글자 정리(NFKC), 한 줄 가리기(미리 보기) |
| `src/tscan/files.py` | 폴더 훑기 · 건너뛰기, `.env` 값, 무시 목록, 사용자 모양 |
| `src/tscan/gitscan.py` | staged(index 내용), 훅 설치 · 해제, 지난 커밋 |
| `src/tscan/cli.py` | 명령줄, `--plain` · `--json` · `--summary`, 종료 코드 |
| `src/tscan/app.py` | Textual 화면 (worker, 가린 미리 보기, `[i]`) |
| `tests/conftest.py` | 가짜 비밀을 **테스트 안에서** 이어 붙여 임시 폴더 · 임시 저장소에 |
