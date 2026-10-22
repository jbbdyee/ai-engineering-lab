# 68 IT agent (from day 67)

- 노드: 14
- 연결: 14

```mermaid
flowchart TD
  n0["IT question webhook"]
  n1["Has question?"]
  n2["Has user?"]
  n3["Reject no user"]
  n4["Reject empty"]
  n5["IT help agent"]
  n6["OpenAI chat model"]
  n7["Search FAQ"]
  n8["Get ticket"]
  n9["Check answer"]
  n10["Passed?"]
  n11["Auto answer"]
  n12["Hand off"]
  n13["Send result"]
  n0 --> n1
  n1 -->|"true"| n2
  n1 -->|"false"| n4
  n5 --> n9
  n9 --> n10
  n10 -->|"true"| n11
  n10 -->|"false"| n12
  n11 --> n13
  n12 --> n13
  n2 -->|"true"| n5
  n2 -->|"false"| n3
```
