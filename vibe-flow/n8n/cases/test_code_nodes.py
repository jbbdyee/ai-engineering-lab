#!/usr/bin/env python3
"""Run Routine Scout's real Code-node JavaScript without starting an n8n workflow."""

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / "n8n/workflows/routine-scout.json"
CASES = ROOT / "n8n/cases/routine-scout.json"

# Node.js is already installed in the local n8n container. Only the small
# $input.first() surface used by this workflow is emulated. Unsupported n8n
# expressions or node settings are reported as "unable", never as passes.
HARNESS = r"""
const fs = require('node:fs');
const util = require('node:util');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const workflow = input.workflow;
const nodes = new Map(workflow.nodes.map(n => [n.name, n]));
const connections = workflow.connections;
class Unable extends Error {}

function onlyLink(name, branch = 0) {
  const links = connections[name]?.main?.[branch];
  if (!Array.isArray(links) || links.length !== 1 ||
      links[0].type !== 'main' || links[0].index !== 0 ||
      !nodes.has(links[0].node)) {
    throw new Unable('지원하지 않는 연결: ' + name + ' 출력 ' + branch);
  }
  return links[0].node;
}

function expression(value, data) {
  const match = typeof value === 'string' &&
    value.match(/^=\{\{ \$json\.([A-Za-z_][A-Za-z_0-9]*) \}\}$/);
  if (!match) throw new Unable('지원하지 않는 표현식: ' + JSON.stringify(value));
  return data[match[1]];
}

function runCase(test) {
  const hooks = workflow.nodes.filter(n => n.type === 'n8n-nodes-base.webhook');
  if (hooks.length !== 1 || hooks[0].parameters.httpMethod !== 'POST' ||
      hooks[0].parameters.responseMode !== 'responseNode' ||
      hooks[0].parameters.path !== input.cases.webhook) {
    throw new Unable('Webhook 설정이 현재 테스트 하네스의 계약과 다름');
  }
  let current = onlyLink(hooks[0].name);
  let data = {body: test.request};
  const visited = new Set([hooks[0].name]);
  while (true) {
    if (visited.has(current)) throw new Unable('순환 연결: ' + current);
    visited.add(current);
    const node = nodes.get(current);
    const type = node.type;
    if (type === 'n8n-nodes-base.code') {
      if (node.typeVersion !== 2 || typeof node.parameters.jsCode !== 'string')
        throw new Unable('지원하지 않는 Code 노드 설정: ' + current);
      // Execute the JavaScript stored in the workflow, not a copied algorithm.
      const output = new Function('$input', node.parameters.jsCode)(
        {first: () => ({json: data})}
      );
      if (!Array.isArray(output) || output.length !== 1 ||
          !output[0] || typeof output[0].json !== 'object' || output[0].json === null)
        throw new Unable('Code 노드의 단일 item 출력 형식 불일치: ' + current);
      data = output[0].json;
      current = onlyLink(current);
    } else if (type === 'n8n-nodes-base.if') {
      const group = node.parameters.conditions;
      if (node.typeVersion !== 2.2 || group?.combinator !== 'and' ||
          group.conditions?.length !== 1 ||
          group.options?.typeValidation !== 'strict')
        throw new Unable('지원하지 않는 IF 설정: ' + current);
      const condition = group.conditions[0];
      const left = expression(condition.leftValue, data);
      const op = condition.operator;
      let passed;
      if (op?.type === 'boolean' && op.operation === 'true') {
        if (typeof left !== 'boolean') throw new Unable('IF boolean 입력 자료형 불일치');
        passed = left === true;
      } else if (op?.type === 'number' && op.operation === 'gt') {
        if (typeof left !== 'number' || typeof condition.rightValue !== 'number')
          throw new Unable('IF number 입력 자료형 불일치');
        passed = left > condition.rightValue;
      } else throw new Unable('지원하지 않는 IF 연산자: ' + current);
      current = onlyLink(current, passed ? 0 : 1);
    } else if (type === 'n8n-nodes-base.respondToWebhook') {
      if (node.typeVersion !== 1.1 || node.parameters.respondWith !== 'json')
        throw new Unable('지원하지 않는 응답 노드 설정: ' + current);
      const status = node.parameters.options?.responseCode ?? 200;
      if (!Number.isInteger(status))
        throw new Unable('지원하지 않는 HTTP 상태 코드 설정: ' + current);
      return {status, json: expression(node.parameters.responseBody, data)};
    } else throw new Unable('지원하지 않는 노드: ' + current);
  }
}

function differences(expected, actual, path = '$') {
  if (util.isDeepStrictEqual(expected, actual)) return [];
  if (expected && actual && typeof expected === 'object' && typeof actual === 'object' &&
      Array.isArray(expected) === Array.isArray(actual)) {
    const keys = new Set([...Object.keys(expected), ...Object.keys(actual)]);
    return [...keys].flatMap(key => differences(expected[key], actual[key], path + '.' + key));
  }
  return [path + ': expected=' + JSON.stringify(expected) + ', actual=' + JSON.stringify(actual)];
}

const counts = {pass: 0, fail: 0, unable: 0};
for (const test of input.cases.cases) {
  try {
    const actual = runCase(test);
    const expected = test.expect;
    const diff = [
      ...differences(expected.status, actual.status, '$.httpStatus'),
      ...differences(expected.equals, actual.json, '$.json'),
    ];
    if (diff.length) {
      counts.fail++;
      console.log('FAIL ' + test.name + '\n  ' + diff.join('\n  '));
    } else {
      counts.pass++;
      console.log('PASS ' + test.name);
    }
  } catch (error) {
    const kind = error instanceof Unable ? 'unable' : 'fail';
    counts[kind]++;
    console.log(kind.toUpperCase() + ' ' + test.name + ': ' + error.message);
  }
}
console.log('SUMMARY total=' + input.cases.cases.length +
  ' pass=' + counts.pass + ' fail=' + counts.fail + ' unable=' + counts.unable);
process.exitCode = counts.fail || counts.unable ? 1 : 0;
"""


def main() -> int:
    workflow = json.loads(WORKFLOW.read_text(encoding="utf-8"))
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    total = len(cases["cases"])
    payload = json.dumps({"workflow": workflow, "cases": cases}, ensure_ascii=False)
    try:
        result = subprocess.run(
            ["docker", "exec", "-i", "n8n", "node", "-e", HARNESS],
            input=payload,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError as error:
        print(f"UNABLE: Node.js 실행 환경 접근 실패: {error}")
        print(f"SUMMARY total={total} pass=0 fail=0 unable={total}")
        return 1
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="")
    if not result.stdout or "SUMMARY total=" not in result.stdout:
        print(f"SUMMARY total={total} pass=0 fail=0 unable={total}")
        return 1
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
