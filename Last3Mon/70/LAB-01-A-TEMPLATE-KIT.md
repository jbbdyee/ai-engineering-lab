# Lab 01 · 복사본 3개를 공지 키트 하나로

> **강사용 정답본** · 학생 저장소에 올리지 않습니다. 학생용 문제는 [LAB-01-Q-TEMPLATE-KIT.md](LAB-01-Q-TEMPLATE-KIT.md).
> 요청문은 예시이며 CLI 에이전트로 보내 재지는 않았습니다. 결과 숫자는 정답 워크플로우를 2026-10-18에 1회씩 실행한 값입니다 (gpt-4.1-mini).
> 수업 전날(2026-10-21) 같은 정답으로 다시 돌린 명령 · `-v` 출력 전부와 codex 프롬프트: [answers/LAB-TEST-RESULT.md](answers/LAB-TEST-RESULT.md) (점수는 10/18과 같음).

## 예제 1 · 비교 정답

세 파일은 노드 9개가 모두 같은 이름이고, **4개 노드**가 다릅니다 (파일에서 비교한 값).

| 노드 | 다른 것 | 어디로 |
| --- | --- | --- |
| `Notice webhook` | 경로 `sample-maintenance` · `sample-security` · `sample-training` | 하나로 (`my-notice-kit`) + 입력 `kind` |
| `Writer agent` | 지시문 안의 머리말(`[점검 안내]` …), 꼭 넣을 문장, 종류별 주의 | 설정 표 (`prefix`, `required_phrases`, `extra`) |
| `Rule checks` | 코드 안의 `max_length` 600 · 500 · 800, `required_phrases` | 설정 표 (`max_length`, `required_phrases`) |
| `Build result` | 코드 안의 `kind` 글자 | 표에서 읽은 `kind` |

- 같은 값(꼭 넣을 문장)이 **두 노드**(지시문, 검사 코드)에 따로 들어 있다 → 한쪽만 고치면 작성자는 넣고 검사는 다른 문장을 찾는 버그.
- 보안 규칙 하나를 고치려면 지금은 **최소 2곳**(그 파일의 지시문과 검사), 공통 규칙이면 **6곳**(파일 3개 × 2).
- 수업 준비 때 세 샘플 호출: 모두 `published: true`, 1.3~2.6초.

요청문 예:

```text
samples/ 의 세 워크플로우를 노드 이름별로 비교해 표로 보여 줘. 파일은 고치지 마.
칸: 노드 이름, 세 파일에서 같은가, 다른 값(점검·보안·교육), 그 값이 업무에서 뜻하는 것.
position, id, webhookId 처럼 동작과 상관없는 차이는 빼.
```

## 예제 2 · 요청문 예

```text
samples/notice-security.json 을 바탕으로 my-work/notice-kit.json 을 새로 만들어 줘 (samples 는 그대로).
- 웹훅 my-notice-kit, 본문 kind, facts 필수(없으면 400), request.
- Code "Kind settings" 하나에 종류 표: maintenance / security / training 마다 label, prefix, max_length, required_phrases, extra.
  (값은 세 샘플에서 옮긴다)
- Writer agent 지시문은 종류와 상관없는 공통 문장만, 머리말·꼭 넣을 문장·주의는 표에서 읽어 text 에 넣는다.
- Rule checks 는 표의 max_length, required_phrases 를 읽는다.
- 결과 {kind, route, published, notice, codes}. 기대 결과 cases/lab01.json.
```

정답: [reference/lab01-example2-kit.json](reference/lab01-example2-kit.json)

| 수업 준비 때 결과 | |
| --- | --- |
| `cases/lab01.json` | 5/5 (1.4~3.8초) |
| `cases/lab01-challenge.json` (예제 상태) | 1/4. 설문은 표에 없어 머리말·익명 문장 없음 (그래도 `published: true`), `party`는 200으로 공지를 씀 |

> 예제 상태에서 설문 공지가 **검사를 통과하고 게시**됐다는 점이 중요합니다. 표에 없는 종류는 규칙도 없으니 막을 것이 없습니다 → 없는 종류는 멈춰야 하는 이유.

## 과제 · 요청문 예

```text
my-work/notice-kit.json 을 고쳐 줘.
1. Kind settings 표에 survey 한 줄: label 설문, prefix [설문 안내], max_length 500,
   required_phrases ["응답은 익명으로 처리됩니다."], extra "설문 목적, 마감일, 걸리는 시간".
2. 표에 없는 kind 면 Kind settings 가 {known: false, kinds: 표의 키 목록} 을 내고,
   다음 If "Known kind?" 에서 400 {"error": "unknown kind", "kinds": [...]}.
3. 바꾼 노드 이름을 보고해 줘. cases/lab01-challenge.json, cases/lab01.json 둘 다 통과.
```

정답: [answers/70-lab01-challenge-kit.json](answers/70-lab01-challenge-kit.json) (바뀐 곳: `Kind settings` 표 + `Known kind?` · `Reject unknown kind` 두 노드 추가)

| 수업 준비 때 결과 | |
| --- | --- |
| `cases/lab01-challenge.json` | 4/4 (없는 종류 0.2초, LLM을 부르지 않음) |
| `cases/lab01.json` | 5/5 |
