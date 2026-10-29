# tver · 강사가 수업 준비 때 직접 만든 본 (2026-10-27)

> **정답 자료** · 학생 저장소에는 수업 뒤 [VIBE-A-TVER.md](../VIBE-A-TVER.md)와 함께 올립니다.
> 이 본은 강사가 CLI 에이전트에 단계 요청문을 보내 만든 것이 아니라, Claude Code가 VIBE-A의 SPEC · IMP-PLAN을 보고 직접 썼습니다. 학생이 만든 것과 파일 구성이 달라도 됩니다. 요구 R1~R14의 **확인 방법**이 같으면 됩니다.

## 설치 · 실행

```bash
cd ~/aio-01d4-stu/Last3Mon/74/tver
uv sync && uv run pytest -q              # 테스트 11개 (저장소는 tmp_path, 가짜 키는 테스트 안에서 만듦)
uv tool install --editable .             # 어느 폴더에서나 tver (R14)
cd /tmp && tver --help
```

| 하고 싶은 것 | 명령 |
| --- | --- |
| 두 파일 비교 | `tver diff a.json b.json` · 줄 diff 없이 `--short` · 다른 프로그램용 `--json` |
| 버전으로 저장 | `tver save my-work/helpdesk.json` · 폴더 `tver save my-work` (워크플로우만) |
| 버전 목록 · 비교 | `tver log helpdesk.json` · `tver diff <rev1> <rev2> helpdesk.json` |
| 한 버전 보기 · 꺼내기 | `tver show <rev> helpdesk.json` · `tver restore <rev> helpdesk.json -o my-work/helpdesk.json` |
| n8n에서 모두 가져오기 | `tver pull [--container day65-n8n-n8n-1]` (읽기만) |
| 화면(TUI) | `tver my-work/helpdesk.json` (`[s]` 지금 파일을 저장, `[q]` 끝) |

- 저장소: `~/.tver/store` (또는 `--repo <폴더>`, `$TVER_REPO`). 내 프로젝트 폴더 밖에 따로 둡니다.
- 종료 코드: `diff` 0 같음 · 1 다름, 모든 명령 2 오류 (파일이 없음 · 워크플로우가 아님 · 키가 있어 저장 거부).

## 파일

| 파일 | 하는 일 | 요구 |
| --- | --- | --- |
| `src/tver/workflow.py` | 읽기, 뜻 없는 칸 빼기(`clean`), 키 정렬 저장 글(`dumps`), 키 모양 찾기(가려서) | R2 · R7 |
| `src/tver/diff.py` | 노드 이름으로 짝짓기, 설정 · 연결 비교, 줄 diff, 모델 · 지시문 · 흐름 분류, 이름 바꿈 | R1 · R3 · R4 · R12 |
| `src/tver/store.py` | git 저장소: 저장(같으면 안 함) · 목록 · 꺼내기, 폴더 저장, n8n에서 내보내기 | R5 · R6 · R9 · R10 · R13 |
| `src/tver/cli.py` | 명령 · `--json` · 종료 코드 | R11 |
| `src/tver/app.py` | Textual 화면 | R8 |
| `tests/` | v1 · v2(`tests/data`, 비밀 없음)로 엔진 · 저장 · 화면 | |
| `Doc/IMP-PLAN.md` | 만든 순서 (엔진 1 → 2 → TUI 1 → 설치 → 엔진 3 · 4) | |

## 2026-10-27에 확인한 것

| 확인 | 결과 |
| --- | --- |
| `uv run pytest -q` | 11 passed |
| `tver diff reference/helpdesk-v1.json reference/helpdesk-v2.json --short` | `flow.py diff`와 같은 7줄, `7 change(s) · model 1 · prompt 1 · flow 5`, 종료 코드 1 |
| 오늘 Lab의 helpdesk 정답 여섯 단계를 차례로 `save` | 버전 6개, 메시지 예 "15 change(s) · model 1 · prompt 1 · flow 13" (Lab 01 과제 2 → Lab 02 예제 1) |
| `tver save answers` | 워크플로우 5개 저장, 테스트 파일 `74-lab02-challenge-golden.json`은 skipped |
| `tver pull` (강사 n8n) | 192 new version(s) — 강사 n8n에 있던 워크플로우 전부, n8n은 그대로 |
| `uv tool install --editable .` → `/tmp`에서 `tver restore` → 원본과 `tver diff` | `0 change(s)`, 종료 코드 0 |
