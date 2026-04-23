# Lab 16 Benchmark Report

## Metadata
- Dataset: hotpot_100.json:batch_02
- Mode: openai
- Records: 50
- Agents: react, reflexion

## Summary
| Metric | ReAct | Reflexion | Delta |
|---|---:|---:|---:|
| EM | 0.76 | 0.88 | 0.12 |
| Avg attempts | 1 | 1.24 | 0.24 |
| Avg token estimate | 1192.44 | 1782.08 | 589.64 |
| Avg latency (ms) | 2283.32 | 4293.16 | 2009.84 |

## Failure modes
```json
{
  "react": {
    "none": 19,
    "wrong_final_answer": 6
  },
  "reflexion": {
    "none": 22,
    "wrong_final_answer": 2,
    "looping": 1
  },
  "overall": {
    "none": 41,
    "wrong_final_answer": 8,
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
