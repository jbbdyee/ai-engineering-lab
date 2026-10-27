# tscan IMP-PLAN (강사가 직접 만든 기록)

## 엔진 1단계 · 찾고 가리기 (R1 · R2 · R3 · R4 · R13)
- [x] scanner.py: 종류 7개(키 4 · 주민번호 · 전화 · 이메일) + 경계, mask, scan_text → Finding(가린 값만)
- [x] files.py: 건너뛰기(.git · node_modules · .venv · 1MB · NUL), .env 값 → env_value
- [x] tests: 가짜 비밀을 테스트 안에서, 날짜 · 주문 번호 · 버전은 0건
## 엔진 2단계 · 커밋 전에 막기 (R5 · R6)
- [x] staged = git show :<path>, 훅 설치 · 해제(표시 줄), 종료 코드 0 · 1 · 2
## TUI 1단계 (R8)
- [x] DataTable · 가린 미리 보기(mask_line) · worker
## 설치 (R14)
- [x] [project.scripts] tscan = "tscan.cli:main", uv tool install --editable .
## 엔진 3단계 (R7 · R10 · R12)
- [x] .tscanignore, --json, --summary
## 엔진 4단계 (R9 · R11)
- [x] history (git log -p 의 + 줄), .tscan.toml · ~/.tscan/rules.toml
## TUI 2단계
- [x] [i] 무시 목록에 더하고 다시 검사, [r]
