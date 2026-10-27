# 릴리스 점검표 · IT 헬프데스크

- 이 파일을 `my-work/RELEASE.md`로 복사해 채웁니다.

## 1. 게이트 결과 (Lab 02)

| 릴리스 | 약한 golden (`cases/golden.json`) | 내가 고친 golden | p95 | 판단 |
| --- | --- | --- | --- | --- |
| 1.0.0 |  |  |  |  |
| 1.1.0 |  |  |  |  |
| 1.2.0 |  |  |  |  |
| 2.0.0 |  |  |  |  |

| 2.1.0 (Lab 02 과제 2) | | 고치기 전 · 뒤 |  |  |

- 기준선 (Lab 02 예제 3): 1.0.0 VPN p50 ___ · p95 ___, 2.0.0 p50 ___ · p95 ___, golden 1.0.0 × 3 ___/___ → `--max-p95` 기준: ___ (까닭: ___)
- 2.0.0 판단 한 줄:

## 2. 배포 순서 (Lab 03)

- [ ] 후보를 고정(`--set release=`)으로 게이트 → PASS
- [ ] 카나리 (`flow.py release helpdesk --canary <후보> --percent <N>`) → 카나리 사용자 답 확인
- [ ] 릴리스 점검 (`my-release-check`) → `promote`, `/gates/helpdesk`에 기록 (`recorded: true`)
- [ ] 배포 정책을 켠 상태에서 (`--require-gate on`) 점검을 지난 것만 배포되는지
- [ ] 배포 (`flow.py release helpdesk <후보>`) → 답의 `version` 확인
- [ ] 문제가 생기면 되돌리기 (`flow.py release helpdesk <이전>`, `--no-canary`) → 확인
- [ ] `CHANGELOG.md`에 한 줄

## 3. 되돌리기 연습 기록

| 상황 | 한 일 | 걸린 시간 | 확인 방법 |
| --- | --- | --- | --- |
| 1.1.0 배포 → 되돌리기 (Lab 03 예제 1) |  |  |  |
| 나쁜 카나리 1.2.0 50% (Lab 03 예제 3): 영향 받은 직원 ___/6 |  |  |  |
| 정책이 막은 배포 (Lab 03 과제 2) |  |  |  |
