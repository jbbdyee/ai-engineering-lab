# Lab 02 · 릴리스 고르기, 후보 시험, 배포 전 게이트

> **강사용 정답본** · 학생 저장소에 올리지 않습니다. 학생용 문제는 [LAB-02-Q-RELEASE-GATE.md](LAB-02-Q-RELEASE-GATE.md).
> 요청문은 예시이며 CLI 에이전트로 보내 재지는 않았습니다. 결과 숫자는 정답 워크플로우를 학생 순서대로 2026-10-27에 1회씩 실행한 값입니다 (강사 Mac, `gpt-4.1-mini` · `gpt-5.4-nano`, bench는 n=5). 명령 · 출력 전부: [answers/LAB-TEST-RESULT.md](answers/LAB-TEST-RESULT.md).

## 예제 1 · 요청문 예

```text
my-work/helpdesk.json 의 Release info(Set) 를 Get release(HTTP GET http://data-api:8800/releases/helpdesk) → Pick release(Code) → Known release?(If) 로 바꿔 줘.
Pick release: 본문 release 가 있으면 그 릴리스 · channel pinned , 없으면 active · channel stable . 고른 릴리스의 prompt_version · model 을 돌려준다.
releases 에 없으면 Known release? false → Reject release(400, {error: 'unknown release', release, known }).
Get prompt · Answer model · Build result 는 Release info 대신 Pick release 를 읽게. 기본 지시문(Fallback prompt)은 그대로.
기대 결과 cases/lab02.json, cases/lab01-challenge.json, cases/lab01-challenge2.json.
```

**빈칸 답** (Q 문서 ▶ 빈칸 채우기 `____①`~`____④`)

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `pinned` | 본문 `release`로 고정 |
| ② | `stable` | 운영 중인 `active` |
| ③ | `known` | 알려진 릴리스 목록 (`cases/lab02.json` "없는 릴리스" 기대) |
| ④ | `Pick release` | 릴리스를 고른 노드 |

정답: [reference/lab02-example1-release.json](reference/lab02-example1-release.json) (Lab 01 과제 1 · 2 포함)

| 10/27 결과 | 고치기 전 (Lab 01 과제 2 정답, `answers/13`) | 고친 뒤 (`answers/14` · `15`) |
| --- | --- | --- |
| `cases/lab02.json` | 1/5 (고정이 안 먹음, 9.9.9도 200, `channel` 없음) | **5/5** |
| `lab01-challenge` · `lab01-challenge2` | | 3/3 · 4/4 |

## 예제 2 · 결과 (에이전트 없이)

| 약한 golden (`answers/16`) | 결과 | p95 |
| --- | --- | --- |
| 1.0.0 | 6/6 PASS | 1.6초 |
| 1.1.0 | 6/6 PASS | 1.1초 |
| **1.2.0** | **6/6 PASS** | 1.5초 |
| 2.0.0 | 6/6 PASS | 2.0초 |

- 1.2.0 프린터 답 (`call -v`): **"IT 포털에서 프린터 문제 해결 방법을 확인해 주세요."** 내보내면 안 되는 답이 PASS.

## 예제 3 · 결과 (에이전트 없이)

| 재기 (`answers/17`) | 결과 |
| --- | --- |
| VPN `bench -n 5 --set release=1.0.0` | p50 **1.23초** · p95 1.42초 |
| VPN `bench -n 5 --set release=2.0.0` | p50 **1.12초** · p95 1.24초 |
| `gate golden --set release=1.0.0 --repeat 3` | **18/18** PASS, p95 1.5초 |

- 기준선 한 줄 예: "1.0.0 p95 1.4초 근처, 3번 반복에도 흔들림 없음 → `--max-p95 3`은 약 두 배 여유, 통과율 100%를 그대로 기준으로."
- 2.0.0은 1.1.0과 지시문이 같고 모델만 다릅니다. 빨라진 0.1초는 모델 때문이라고 말할 수 있습니다 (한 가지만 바꿨으니). 다만 5번이라 차이가 작으면 흔들림 안쪽일 수 있다고 짚습니다.

## 과제 1 · 요청문 예

```text
cases/golden.json 을 cases/my-golden.json 으로 복사해 expect 만 강하게 바꿔 줘. 워크플로우는 바꾸지 않는다 .
질문마다 답에 꼭 있어야 할 낱말을 contains 로 (아래는 내가 FAQ · 접수 건 데이터에서 정한 것):
VPN 인증서 / VPN 업데이트 · 최신 / 비밀번호 비밀번호 찾기 · 휴대폰 / 프린터 대기열 · 전원 / 메일함 보관함 · 삭제 /
T-1002 처리 중 / T-1002 10월 20일 · 20일 / T-1001 처리 완료 · 완료.
프린터 질문에는 " IT 포털을 확인 · 포털을 참고 " 같은 떠넘기기 말이 없어야 한다 (not_contains).
기대: gate --set release=1.0.0 · 1.1.0 PASS, release= 1.2.0 FAIL.
```

**빈칸 답** (Q 문서 ▶ 빈칸 채우기 `____①`~`____④`)

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | 바꾸지 않는다 | 과제 조건: 테스트만 고친다 |
| ② | `contains` | 목록 중 하나라도 있으면 통과 (AGENTS.md 8절) |
| ③ | `IT 포털을 확인` · `포털을 참고` (정답 파일) | 1.2.0 지시문(p3)이 "IT 포털을 보라"고 시킴. **실제 답 "포털에서 … 확인해 주세요"는 이 글자에 안 걸림** → 풀이 거리 |
| ④ | `1.2.0` | 막아야 할 릴리스 |

정답 (테스트 파일): [answers/74-lab02-challenge-golden.json](answers/74-lab02-challenge-golden.json) (9케이스)

| 10/27 결과 (`answers/18`) | 강한 golden | p95 |
| --- | --- | --- |
| 1.0.0 | **9/9 PASS** | 1.4초 |
| 1.1.0 | **9/9 PASS** | 1.7초 |
| 1.2.0 | **1/9 FAIL** | 1.3초 |
| 2.0.0 | **9/9 PASS** | 1.3초 |

- 1.2.0이 통과한 하나 = "포털로 떠넘기지 않기"(`not_contains`). 해결 낱말 8케이스가 막았습니다.
- 학생이 ③에 "포털"만 적으면: 프린터 케이스에만 걸면 1.2.0의 그 케이스도 ✘가 됩니다 (1.0.0 · 1.1.0의 프린터 답에는 "포털"이 없었음). 그런데 **모든 질문에** `not_contains "포털"`을 걸면 1.0.0 · 1.1.0도 FAIL — 비밀번호 답이 "**사내 포털** 로그인 화면의 '비밀번호 찾기'"라고 정상으로 씁니다 (`runs/74-lab02-challenge-golden-*.json`의 1.0.0 · 1.1.0 응답). 금지 낱말이 넓으면 지나치게 막는다는 73일차 이야기와 같습니다. 어느 쪽이든 1.2.0은 FAIL.
- 2.0.0 판단 예: "강한 golden PASS, p95 1.3초 → 카나리 10%로 먼저, 비용(75일차) 본 뒤 배포."

## 과제 2 · 요청문 예

```text
my-work/helpdesk.json 의 Get prompt 에 options.response.response 로 neverError true, fullResponse true 를 더해 줘 (timeout 2000 · onError 는 그대로).
성공 쪽 Registry prompt 를 Code 로 바꿔: statusCode 200 이면 {state: 'registry', text: body.text}, 404 이면 {state: 'broken'}, 그 밖이면 {state: 'fallback', text: 기본 지시문}.
Prompt broken?(If, state == 'broken') true → Reject broken(HTTP 400 , {error: 'release broken', release, prompt_version}), false → Search FAQ.
prompt_source 는 Registry prompt 의 state 가 'registry' 면 registry, 아니면 fallback. 실패 쪽(시간 초과) Fallback prompt 는 그대로 둔다 .
기대 결과 cases/lab02-challenge2.json, cases/lab02.json.
```

**빈칸 답** (Q 문서 ▶ 빈칸 채우기 `____①`~`____④`)

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `fullResponse` | 응답 코드 · 본문을 같이 받음 (`$json.statusCode`) |
| ② | `404` | `/prompts/helpdesk/p9` → 404 `prompt not found` |
| ③ | `400` | `cases/lab02-challenge2.json` 첫 케이스 `status` |
| ④ | 그대로 둔다 | 장애(시간 초과)는 지금처럼 견딤 |

정답: [answers/74-lab02-challenge2-broken.json](answers/74-lab02-challenge2-broken.json) (예제 1 정답 + `Get prompt` 응답 옵션, `Registry prompt`를 Code로, 노드 2개: `Prompt broken?` · `Reject broken`)

| 10/27 결과 | 고치기 전 (예제 1 정답, `answers/19`) | 고친 뒤 (`answers/20`) |
| --- | --- | --- |
| 망가진 릴리스 2.1.0 | ✘ **200** (기본 지시문 p1으로 답) | ✔ 400 `release broken` · `p9` |
| 평소 · 1.1.0 | ✔ | ✔ `registry` · `[FAQ-003]` |
| 저장소 고장 · 1.1.0 | ✔ `fallback` | ✔ `fallback` |
| 저장소 고장 · 9.9.9 | ✔ 400 | ✔ 400 |
| 운영 1.0.0 | ✔ | ✔ |
| 합계 | 4/5 | **5/5** |
| `gate my-golden --set release=2.1.0` | **9/9 PASS** (p95 1.5초) | **0/9 FAIL** |
| `lab02` · `lab01-challenge2` (`answers/21`) | | 5/5 · 4/4 |

- 풀이 핵심: **장애를 견디는 장치(Lab 01 과제 2)가 설정 오류를 숨겼고, 그래서 게이트도 PASS를 줬다.** 4xx는 크게 실패(fail fast), 5xx · 시간 초과만 견딘다 — 72일차 재시도 원칙과 같은 구분.
