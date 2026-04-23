# Lab 16 Benchmark Report

## Metadata
- Dataset: hotpot_100.json
- Mode: openai
- Records: 200
- Agents: react, reflexion

## Summary
| Metric | ReAct | Reflexion | Delta |
|---|---:|---:|---:|
| EM | 0.63 | 0.85 | 0.22 |
| Avg attempts | 1 | 1.35 | 0.35 |
| Avg token estimate | 1334.06 | 2209.67 | 875.61 |
| Avg latency (ms) | 2807 | 5448.82 | 2641.82 |

## Failure modes
```json
{
  "react": {
    "wrong_final_answer": 33,
    "none": 63,
    "incomplete_multi_hop": 4
  },
  "reflexion": {
    "wrong_final_answer": 13,
    "none": 85,
    "looping": 1,
    "incomplete_multi_hop": 1
  },
  "overall": {
    "wrong_final_answer": 46,
    "none": 148,
    "incomplete_multi_hop": 5,
    "looping": 1
  }
}
```

## Extensions implemented
- structured_evaluator
- reflection_memory
- benchmark_report_json
- adaptive_max_attempts

## Discussion
This benchmark compares a one-shot ReAct baseline against a multi-attempt Reflexion agent. The Reflexion loop stores concise lessons from failed attempts and feeds those lessons into the next actor call, which usually improves exact-match on questions that require multi-hop grounding. The tradeoff is increased attempts, higher token usage, and higher latency. Remaining failures typically come from incomplete evidence tracing or choosing a plausible entity without final verification against the provided context.
