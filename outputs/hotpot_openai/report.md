# Lab 16 Benchmark Report

## Metadata
- Dataset: hotpot_100.json
- Mode: openai
- Records: 200
- Agents: react, reflexion

## Summary
| Metric | ReAct | Reflexion | Delta |
|---|---:|---:|---:|
| EM | 0.65 | 0.86 | 0.21 |
| Avg attempts | 1 | 1.47 | 0.47 |
| Avg token estimate | 1340.97 | 2481.81 | 1140.84 |
| Avg latency (ms) | 8643.32 | 5618.77 | -3024.55 |

## Failure modes
```json
{
  "react": {
    "wrong_final_answer": 30,
    "none": 65,
    "incomplete_multi_hop": 4,
    "entity_drift": 1
  },
  "reflexion": {
    "reflection_overfit": 2,
    "none": 86,
    "wrong_final_answer": 11,
    "incomplete_multi_hop": 1
  },
  "overall": {
    "wrong_final_answer": 41,
    "none": 151,
    "incomplete_multi_hop": 5,
    "entity_drift": 1,
    "reflection_overfit": 2
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
