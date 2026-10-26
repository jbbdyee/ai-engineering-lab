# 테스트 보고서 · 사내 IT 규정 Q&A

- 이름:
- 사용한 CLI 에이전트: codex
- 워크플로우 파일: `my-work/index.json`, `my-work/search.json`, `my-work/policy-qa.json`
- 상태: 워크플로우 정적 검사 완료. n8n push 및 실행 테스트 결과는 미측정.

## 1. 내가 쓴 테스트 (`cases/my-cases.json`)

| 케이스 | 기대 문서 | 근거가 있는 규정 |
| --- | --- | --- |
| 챗GPT에 고객 자료 | `software-usage` | 3. 생성형 AI 서비스 |
| 폰으로 업무 메일 | `device-issue-return` | 4. 개인 장비 사용 |
| 비번 길이 | `password-policy` | 1. 비밀번호 만들기 |
| 퇴직 후 랩탑 반납 | `device-issue-return` | 3. 반납 |
| 사내망 원격 접속 | `remote-work-vpn` | 1. 접속 원칙 |
| 수상한 이메일 링크 | `security-incident` | 1. 피싱 메일 |

## 2. 실패와 고친 내용

| 실패한 케이스 | 처음 결과 | 원인 | 고친 곳 | 고친 뒤 |
| --- | --- | --- | --- | --- |
| 실행 후 기록 | 미측정 | 미측정 | `search.json`의 `Expand query` | 미측정 |

## 3. 최종 결과

| 테스트 파일 | 결과 |
| --- | --- |
| `cases/lab02.json` | 미측정 /6 |
| `cases/lab02-challenge.json` | 미측정 /8 |
| `cases/retrieval-doc.json` | 미측정 /24 |
| `cases/retrieval-answer.json` | 미측정 /24 |
| `cases/retrieval-answer3.json` | 미측정 /24 |
| `cases/lab03-threshold.json` | 미측정 /10 |
| `cases/my-cases.json` | 미측정 /6 |

## 4. 남은 문제 · 배운 점

- 개선 전후 검색 점수와 실행 시간을 같은 색인 설정에서 비교해야 한다.
- 200자·400자 청크 측정 후 섹션 청크로 다시 색인해야 한다.
