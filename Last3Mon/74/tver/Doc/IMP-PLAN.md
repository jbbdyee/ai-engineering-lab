# tver IMP-PLAN

## 엔진 1단계 · 정리하고 비교하기 (R1 · R2 · R3 · R4)
- [x] `workflow.clean`: id · position · webhookId · 내보내기 도장 빼기, 노드 이름순 · `dumps`는 키 정렬
- [x] `diff.compare(old, new)` → `Change{op, node, category, key, before, after, lines}`
- [x] `diff.category`: Chat model의 model → model, systemMessage · text · jsCode → prompt, 나머지 → flow
- [x] 80자 넘거나 여러 줄이면 `difflib` 줄 diff
- [x] tests: v1 → v2 7개 · 1/1/5, 위치 · id · 순서만 바꾼 파일 0개, systemMessage에 `+ … [FAQ-003]`
- [x] cli: `tver diff a.json b.json`
- 확인: `uv run pytest -q`, `uv run tver diff tests/data/helpdesk-v1.json tests/data/helpdesk-v2.json`

## 엔진 2단계 · git에 저장 · 목록 (R5 · R6)
- [x] `Store.save_workflow`: 정리한 글이 같으면 "no change", 다르면 쓰고 커밋 (메시지 = 바로 전과의 요약)
- [x] `Store.log` · `Store.show`, `tver diff <rev1> <rev2> <name>`
- [x] tests: 두 번 저장 → 버전 1개, v2로 바꿔 저장 → 메시지에 "model 1 · prompt 1 · flow 5"
- 확인: `uv run tver --repo /tmp/s save tests/data/helpdesk-v1.json` 두 번, `log`

## TUI 1단계 · 버전 목록 · 바뀐 것 트리 · 자세히 (R8)
- [x] 왼쪽 ListView(버전), 오른쪽 Tree(노드 → 바뀐 것), 아래 자세히 (줄 diff 또는 전 · 후)
- [x] 고른 버전 vs 바로 전 버전 비교는 worker
- [x] `[s]` 지금 파일을 버전으로 저장
- [x] tests: 저장 1개 → `[s]` → 2개, 트리 제목에 "model 1 · prompt 1 · flow 5"

## 설치 (R14)
- [x] `[project.scripts] tver = "tver.cli:main"`, 저장소 기본 `~/.tver/store` (`--repo` · `$TVER_REPO`)
- 확인: `uv tool install --editable .`, `cd /tmp && tver --help`

## 엔진 3단계 · 키 거부 · JSON · 폴더 (R7 · R11 · R13)
- [x] `find_secrets`: `sk-…` · AWS · GitHub · Slack 토큰 모양, 메시지에는 앞 5자 + 끝 2자만
- [x] `--json`, 종료 코드 0 / 1 / 2
- [x] `save <폴더>`: `nodes` · `connections`가 있는 것만, 나머지 skipped

## 엔진 4단계 · n8n에서 가져오기 · 꺼내기 · 이름 바꿈 (R9 · R10 · R12)
- [x] `pull`: `docker exec <컨테이너> n8n export:workflow --all` → 이름별 저장 (n8n에는 쓰지 않음)
- [x] `restore <rev> <name> -o <파일>`: `git show`로 꺼내 파일로, 저장소는 그대로
- [x] 짝 없는 − · + 노드 중 종류 · 설정이 같은 한 쌍 → `renamed`, 연결도 새 이름으로 맞춰 비교
