# Lab 16 Benchmark Report

## Metadata
- Dataset: hotpot_100.json:batch_03
- Mode: openai
- Records: 50
- Agents: react, reflexion

## Summary
| Metric | ReAct | Reflexion | Delta |
|---|---:|---:|---:|
| EM | 0.88 | 0.92 | 0.04 |
| Avg attempts | 1 | 1.12 | 0.12 |
| Avg token estimate | 1226.32 | 1499.56 | 273.24 |
| Avg latency (ms) | 1969.92 | 2528.12 | 558.2 |

## Failure modes
```json
{
  "react": {
    "none": 22,
    "wrong_final_answer": 3
  },
  "reflexion": {
    "none": 23,
    "wrong_final_answer": 2
  },
  "overall": {
    "none": 45,
    "wrong_final_answer": 5
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
