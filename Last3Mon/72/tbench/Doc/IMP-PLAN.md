# tbench IMP-PLAN (강사가 직접 만든 기록)

## 엔진 1단계 · 부르고 재기 (R1 · R6 · R7 · R8)
- [x] runner.py: call_once → {status, seconds, error_kind, timings}, run() 제너레이터
- [x] stats.py: nearest-rank (1~10 → p50 5 · p95 10), 실패는 세고 시간 목록에서 뺌, p50 excl. first
- [x] tests/conftest.py 가짜 서버, --plain · --warmup · --header (가리기)
## TUI 1단계 (R2)
- [x] app.py: Sparkline · 요약 · DataTable, worker(thread) + call_from_thread. 테스트: 지연 0.5초 × 6, 1.3초 뒤 1~5줄 → 끝에 6줄
## 설치 (R14)
- [x] [project.scripts] tbench = "tbench.cli:main", uv tool install --editable ., /tmp 에서 tbench --help
## 엔진 2단계 (R3 · R13 · R11)
- [x] --save (기본 ~/.tbench/results/), compare (url · method · body_sha256 · n · concurrency · warmup 다르면 WARNING), history (최신 위), --log
## 엔진 3단계 (R4 · R10 · R9 · R12)
- [x] --concurrency (0.3초 × 6: k=1 1.8초대, k=3 1초 안), --max-p95 · --max-failures 종료 코드 0 · 1, timings 평균, profile save/list · run
## TUI 2단계 (R5)
- [x] --pick DIR: OptionList, Enter 로 그 본문 실행
