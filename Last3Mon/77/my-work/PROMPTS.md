# 오늘 실습에 사용한 에이전트 요청문 모음 (PROMPTS.md)

## Lab 01 · 실행 기록을 읽고, 지표로 만들기

### 예제 2 · 지표 보고서 (`my-work/log-report.json`)
```text
my-work/log-report.json 을 새로 만들어 줘. 웹훅 POST my-log-report, 이름 "77 Log report (my)".
Get logs(HTTP POST http://data-api:8800/logs/query) 에 웹훅 본문의 from · to · tag · source 를 넘기고, source 가 없으면 all.
Compute metrics(Code) 하나에서 AGENTS.md 3절 정의대로 total · errors · error_rate · p50_ms · p95_ms · by_route 를 계산해 줘.
error_rate 는 errors / total 을 소수 4자리 반올림, 0건이면 0.
p50 · p95 는 duration_ms 를 오름차순으로 놓고 ceil(p × n)번째 값 (1부터 셈, 오류 실행도 포함). route 가 null 이면 by_route 의 "오류".
LLM 은 쓰지 않는다. 기대 결과 cases/lab01.json.
```

### 과제 1 · 날짜별 · 릴리스별 지표 추가
```text
my-work/log-report.json 의 Compute metrics 에 by_day 와 by_release 를 더해 줘.
by_day: started_at 앞 10자(날짜)로 묶어 {"2026-10-26": {total, errors, error_rate}}, 날짜순.
by_release: route 가 "자동 답변" 인 실행만 release 로 묶어 {answers, repeats, repeat_rate}.
repeats 는 repeat 가 true 인 수, repeat_rate = repeats / answers (소수 4자리).
앞의 지표는 그대로 둔다. 기대 결과 cases/lab01-challenge.json, cases/lab01.json 도.
```

### 과제 2 · 단계별 지연 및 비용 지표 추가
```text
my-work/log-report.json 의 Compute metrics 에 steps 와 비용을 더해 줘.
steps: faq_ms · answer_ms 마다, steps 의 그 값이 0보다 큰 실행만 모아 {runs, p50, p95} (백분위 정의는 앞과 같음, 없으면 runs 0 · p50 0 · p95 0).
cost_usd: 실행마다 cost_usd 의 합, 소수 5자리 반올림. cost_per_run: cost_usd / total, 소수 6자리 (0건이면 0).
llm_calls: 실행마다 llm_calls 의 합.
앞의 지표는 그대로. 기대 결과 cases/lab01-challenge2.json, lab01 · lab01-challenge 도 그대로 통과.
```

---

## Lab 02 · 문제를 숫자로 찾고, 요약하기

### 예제 1 · 실패 묶음 및 미답변 주제
```text
my-work/log-report.json 의 Compute metrics 에 failures 와 unanswered_topics 를 더해 줘.
failures: status 가 error 인 실행을 (error_node, error_message) 로 묶어 [{node, message, count}], 많은 순.
unanswered_topics: route 가 "담당자 연결" 인 실행을 topic 으로 묶어 [{topic, count}], 많은 순.
담당자 연결은 status 가 success 라 failures 에 넣지 않는다. 앞의 지표는 그대로. 기대 결과 cases/lab02.json 앞 세 케이스.
```

### 예제 2 · 이상 시간대 탐지
```text
my-work/log-report.json 의 Compute metrics 에 anomalies 를 더해 줘.
started_at 앞 13자(예 2026-10-26T09)로 시간마다 묶어 {hour, total, errors, error_rate}.
실행이 5건 이상이고, error_rate 가 그 기간 전체 error_rate 의 3배 이상이고, 오류가 1건 이상인 시간만 시간순으로.
앞의 지표는 그대로. 기대 결과 cases/lab02.json 전체.
```

### 과제 1 · 재문의 주제 분석
```text
my-work/log-report.json 의 Compute metrics 에 repeat_topics 를 더해 줘.
route 가 "자동 답변" 인 실행만 topic 으로 묶어 {topic, answers, repeats, repeat_rate}. repeats 가 0 인 주제는 뺀다.
정렬은 repeat_rate 가 높은 순, 같으면 repeats 가 많은 순. repeat_rate 는 repeats / answers, 소수 4자리.
앞의 지표는 그대로. 기대 결과 cases/lab02-challenge.json, cases/lab02.json 도.
```

### 과제 2 · 운영 요약 및 숫자 검증 (`my-work/log-summary.json`)
```text
my-work/log-summary.json 을 새로 만들어 줘. 웹훅 POST my-log-summary, 이름 "77 Log summary (my)".
Get report: 지표를 다시 계산하지 말고 HTTP POST http://localhost:5678/webhook/my-log-report 로 부른다 (본문 from · to · tag · source 그대로, timeout 30000).
Write summary(AI Agent + OpenAI gpt-4.1-mini, temperature 0): 통계 중 total · errors · error_rate · failures · unanswered_topics · anomalies 만 JSON 으로 주고, 한국어 3문장으로
가장 많은 답 못 한 주제와 수 · 가장 많은 실패(노드 · 메시지 · 수) · 가장 나쁜 시간대(10월 26일 09시처럼). 통계에 없는 숫자와 짐작한 원인은 쓰지 않는다.
Check numbers(Code): 요약 글의 숫자를 모두 뽑아, 통계의 값 · 비율의 ×100 · 키와 글자 속 숫자(날짜 · 시간)에 있는지 본다. 없는 숫자는 unknown_numbers 에, 하나도 없으면 numbers_ok true.
결과 {summary, numbers_ok, unknown_numbers, top_topic, worst_hour}. 기대 결과 cases/lab02-challenge2.json.
```

---

## Lab 03 · 고치고, 다시 돌려 재고, 보고하기

### 예제 1 · 헬프데스크 장애 복구 (`my-work/helpdesk.json`)
```text
my-work/helpdesk.json (제공 helpdesk-live 를 복사한 것) 의 Search FAQ 노드만 고쳐 줘.
options.timeout 을 1000 에서 3000 으로, 그리고 retryOnFail true, maxTries 2, waitBetweenTries 300 (parameters 밖, 노드 바로 아래).
그래도 실패하면 지금처럼 오류 출력(onError continueErrorOutput)으로 Failed → Log Failed 에 기록한다.
다른 노드와 로그 모양(steps 포함)은 그대로. 기대 결과 cases/replay-after.json (FAQ 가 1.2초 느린 동안 10/10), cases/lab03.json.
```

### 예제 2 · 미답변율 및 SLO 판정 추가
```text
my-work/log-report.json 의 Compute metrics 에 unanswered_rate 와 slo 를 더해 줘.
unanswered_rate = "담당자 연결" 수 / total (소수 4자리).
기준 limits 는 기본 error_rate 0.01 · p95_ms 3000 · unanswered_rate 0.02, 웹훅 본문에 slo 가 있으면 그 값으로 덮어쓴다 (본문은 $('Report webhook').first().json.body).
지표가 기준보다 크면 그 이름을 breaches 에 넣고, slo = {ok: breaches 가 비었으면 true, breaches, limits}.
앞의 지표는 그대로. 기대 결과 cases/lab03-slo.json.
```

### 과제 1 · 주간 운영 보고서 자동 생성 (`my-work/weekly.json`)
```text
my-work/weekly.json 을 새로 만들어 줘. 웹훅 POST my-weekly, 본문 from · to · prev_from · prev_to, 이름 "77 Weekly report (my)".
This week · Last week: my-log-report 를 두 번 부른다 (이번 주 from · to, 지난주 prev_from · prev_to). Summary: my-log-summary 를 이번 주로 부른다 (timeout 60000).
Write report(Code)가 마크다운을 만든다. ## 숫자: | 지표 | 지난주 | 이번 주 | 표 (요청 · 오류율 · p95 · 답 못 함 · SLO), 비율은 0.0588 을 5.88%처럼.
## 문제: 실패 · 답하지 못한 질문 · 이상 시간대("2026-10-26 09시"). ## 요약: LLM 요약과 숫자 확인 결과.
## 다음 할 일: LLM 이 아니라 규칙으로 — 답 못 한 주제가 있으면 "FAQ에 '<주제>' 항목 추가", Search FAQ 실패가 있으면 timeout 점검, 429 가 있으면 사용량 한도 점검.
결과 {markdown, total, error_rate, slo_ok, numbers_ok}. 기대 결과 cases/lab03-challenge.json.
```

### 과제 2 · SLO 위반 알림 및 폭주 억제 (`my-work/slo-alert.json`)
```text
my-work/slo-alert.json 을 새로 만들어 줘. 웹훅 POST my-slo-alert, 본문 from · to · tag · source · slo, 이름 "77 SLO alert (my)".
Get report: my-log-report 를 부른다 (본문 그대로). Recent alerts: POST http://data-api:8800/alerts/list {workflow: "slo", reason: "slo", within: 600}.
Decide(Code): breaches 가 없으면 alert "none", 있는데 10분 안의 같은 알림이 있으면 "suppressed", 아니면 "sent".
message 는 "SLO breach: error_rate 0.0588 > 0.01, …" 처럼 지표 · 값 · 기준. Send it?(If): sent 일 때만 POST /alerts {workflow: "slo", severity: "high", reason: "slo", breaches, message}.
두 갈래 모두 같은 결과 {ok, breaches, alert, message, total} 로 응답. 기대 결과 cases/lab03-challenge2.json.
```
