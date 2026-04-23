# Lab 16 Benchmark Report

## Metadata
- Dataset: hotpot_100.json:batch_04
- Mode: openai
- Records: 50
- Agents: react, reflexion

## Summary
| Metric | ReAct | Reflexion | Delta |
|---|---:|---:|---:|
| EM | 0.52 | 0.8 | 0.28 |
| Avg attempts | 1 | 1.44 | 0.44 |
| Avg token estimate | 1506.44 | 2703.4 | 1196.96 |
| Avg latency (ms) | 2789.28 | 9535.76 | 6746.48 |

## Failure modes
```json
{
  "react": {
    "none": 13,
    "incomplete_multi_hop": 3,
    "wrong_final_answer": 9
  },
  "reflexion": {
    "none": 20,
    "wrong_final_answer": 4,
    "incomplete_multi_hop": 1
  },
  "overall": {
    "none": 33,
    "incomplete_multi_hop": 4,
    "wrong_final_answer": 13
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
