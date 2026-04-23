# Lab 16 Benchmark Report

## Metadata
- Dataset: hotpot_100.json:batch_01
- Mode: openai
- Records: 50
- Agents: react, reflexion

## Summary
| Metric | ReAct | Reflexion | Delta |
|---|---:|---:|---:|
| EM | 0.36 | 0.8 | 0.44 |
| Avg attempts | 1 | 1.6 | 0.6 |
| Avg token estimate | 1411.04 | 2853.64 | 1442.6 |
| Avg latency (ms) | 4185.48 | 5438.24 | 1252.76 |

## Failure modes
```json
{
  "react": {
    "wrong_final_answer": 15,
    "none": 9,
    "incomplete_multi_hop": 1
  },
  "reflexion": {
    "wrong_final_answer": 5,
    "none": 20
  },
  "overall": {
    "wrong_final_answer": 20,
    "none": 29,
    "incomplete_multi_hop": 1
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
