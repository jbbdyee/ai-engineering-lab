# Lab 02 · 작성 → 검토 → 고쳐 쓰기, 정리자 Fork-Join

> **강사용 정답본** · 학생 저장소에 올리지 않습니다. 학생용 문제는 [LAB-02-Q-COLLABORATION.md](LAB-02-Q-COLLABORATION.md).
> 요청문은 예시이며 CLI 에이전트로 보내 재지는 않았습니다. 결과 숫자는 정답 워크플로우를 2026-10-18에 1회씩 실행한 값입니다 (gpt-4.1-mini).

## 예제 2 · 요청문 예

```text
my-work/notice.json 에 공지 팀 워크플로우를 만들어 줘. 계약은 AGENTS.md 3절 공지 팀. facts가 비면 400.
1. Write draft: HTTP POST http://localhost:5678/webhook/my-writer {request, facts} (웹훅 본문 그대로)
2. Review draft: HTTP POST .../my-reviewer {facts: 웹훅 본문의 facts, draft}
3. passed가 true면 route "게시 가능", published true, rounds 1, notice=첫 초안, codes [].
4. 아니면 한 번만 고쳐 쓴다: Revise draft = my-writer {request, facts, previous_draft: 첫 초안, feedback: issues를 "code: detail" 줄로}
   → Review again (facts는 웹훅 본문) → 통과면 "수정 후 게시 가능"(rounds 2, first_codes: 첫 검토 codes), 아니면 "담당자 확인"(published false, codes: 두 번째 검토 codes).
5. 고리로 되돌리지 말고 노드를 따로 둔다. 기대 결과 cases/lab02.json.
```

정답: [reference/lab02-example2-pipeline.json](reference/lab02-example2-pipeline.json) — 일부러 `neverError`와 `steps`(기록)가 없습니다 (Lab 03).

| 수업 준비 때 결과 | |
| --- | --- |
| 처음 | `lab02` 3/4. 연락처 공지: 첫 검토 `personal_info` → 고쳐 쓴 초안에서 번호는 빠졌으나 두 번째 검토가 "문의: IT팀 김민지"(사실에 있는 내용)를 `unsupported_claim`으로 잡아 `담당자 확인` = **LLM 검토자의 거짓 경보** |
| 검토자 지시문 보강 뒤 | 4/4 (메일 2.0초 · VPN 2.4초 · 연락처 고쳐 쓰기 4.1초) |
| 같은 날 다른 실행 (Lab 03 준비 중) | 고쳐 쓴 작성자가 번호 대신 **"(내선 1234)"를 지어냄** → 검토자가 `unsupported_claim`으로 잡아 `담당자 확인`. 작성자 지시문에 "고칠 때 새 번호·내선을 넣지 않는다" 추가 |
| 그 뒤에도 거짓 경보 1번 | 검토자 Code에서 LLM 판단을 다시 확인하도록 고침 (Lab 01 A 참고) → 이후 `lab02` 4/4, `lab03` 3/3 |

풀이 포인트 (실제로 일어난 일 그대로 보여 주기):

- 협업이 실패하는 곳은 **역할 사이**: 작성자가 고치면서 새 정보를 만들고, 검토자는 맞는 문장을 의심했다. 둘 다 Executions에서 역할별 실행을 열어 찾았다.
- 역할이 나뉘어 있어서 **어느 역할을 고칠지** 분명했다 (작성자 지시문 한 줄, 검토자 Code 한 줄).

## 과제 · 요청문 예

```text
my-work/notice.json 을 고쳐 줘. 통과한 두 길(게시 가능, 수정 후 게시 가능)을 Code "Final notice" 하나로 모은 뒤,
그 노드에서 두 AI Agent로 함께 보낸다 (각자 chat model 노드).
- Make title: 메일 제목 한 줄, 40자 이내, 괄호 없이, 공지에 없는 정보 금지.
- Make chat message: 메신저 글 2줄·120자 이내, 날짜·시간 그대로, 공지에 없는 정보 금지.
- Merge(입력 2)로 모으고 Code "Combine"에서 공지 결과에 title, chat 을 더한다. 담당자 확인 길은 그대로.
- cases/lab02-challenge.json 과 cases/lab02.json 둘 다 통과.
```

정답: [answers/69-lab02-challenge-editor.json](answers/69-lab02-challenge-editor.json)

| 수업 준비 때 결과 | |
| --- | --- |
| `lab02-challenge` | 4/4 (두 번 실행, 두 번 모두) · 메일 5.2초 · VPN 4.1초 · 연락처 고쳐 쓰기 5.9초 |
| 예 (메일 점검) | title "10월 23일 메일 서버 점검 안내드립니다" · chat "10월 23일(목) 22:00~24:00 메일 서버 점검으로 송수신 불가, 종료 후 프로그램 재실행 바랍니다." |

풀이 포인트:

- **정리자 두 갈래는 동시에 돌지 않았습니다 (차례로).** 수업 준비 때 실행 기록(n8n Executions, 2026-10-18 01:07)의 노드 시작 시각:

| 실행 | `Make title` 시작 · 걸린 시간 | `Make chat message` 시작 · 걸린 시간 | 정리자 둘 합 |
| --- | --- | --- | --- |
| 메일 점검 (게시 가능) | +3.390초 · 0.737초 | **+4.130초** · 0.998초 | 1.74초 |
| 연락처 공지 (수정 후 게시 가능) | +4.305초 · 0.703초 | **+5.013초** · 0.851초 | 1.55초 |

  `Make chat message`는 `Make title`이 **끝난 시각**(3.390 + 0.737 = 4.127)에 시작했습니다. n8n의 실행 순서 v1은 갈래를 하나씩 끝까지 실행합니다. 그래서 늘어난 시간은 두 정리자 시간의 **합**(약 1.5~1.7초)입니다. 68일차의 "같은 HTTP 노드에 온 항목들은 함께, 갈래는 차례로"와 같습니다.
- 짚을 것: 설계의 Fork-Join(서로 기다릴 필요 없음)과 실행 엔진의 동시 실행은 다른 이야기입니다. 그림에서 갈래로 나눈 것은 **"서로 의존하지 않는다"는 설계 정보**이고, n8n은 한 실행 안의 갈래를 차례로 돌립니다. 정말 동시에 하려면 실행 구조를 따로 설계해야 합니다 (오늘 범위 밖, 수업 준비 때 시험하지 않음). 지금은 정리자 둘이 1.5~1.7초라 차례로 돌아도 문제가 크지 않다는 것도 함께 말합니다. 학생이 Executions에서 찾은 시각으로 이 결론을 함께 냅니다.
- 정리자를 붙이면 보고서 기준으로 요청 하나가 약 2초 늘었다 (정리자가 없을 때 2.0~4.1초, 있을 때 4.1~6.5초). 실행 기록에서 정리자 둘이 차지한 시간은 1.5~1.7초 (나머지는 작성 · 검토 LLM 답 시간의 차이). 정리자 결과는 다시 검토하지 않았다 → 정리자도 "새 정보 금지"를 지켰는지는 테스트(`not_contains`)로만 확인. 운영이라면 검토자를 한 번 더 둘지 토론.
