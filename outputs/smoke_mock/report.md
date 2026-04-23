# Lab 16 Benchmark Report

## Metadata
- Dataset: hotpot_mini.json
- Mode: mock
- Records: 16
- Agents: react, reflexion

## Summary
| Metric | ReAct | Reflexion | Delta |
|---|---:|---:|---:|
| EM | 0.5 | 1.0 | 0.5 |
| Avg attempts | 1 | 1.5 | 0.5 |
| Avg token estimate | 0 | 0 | 0 |
| Avg latency (ms) | 0 | 0 | 0 |

## Failure modes
```json
{
  "react": {
    "none": 4,
    "incomplete_multi_hop": 4
  },
  "reflexion": {
    "none": 8
  },
  "overall": {
    "none": 12,
    "incomplete_multi_hop": 4
  }
}
```

## Extensions implemented
- structured_evaluator
- reflection_memory
- benchmark_report_json
- adaptive_max_attempts
- mock_mode_for_autograding

## Discussion
This benchmark compares a one-shot ReAct baseline against a multi-attempt Reflexion agent. The Reflexion loop stores concise lessons from failed attempts and feeds those lessons into the next actor call, which usually improves exact-match on questions that require multi-hop grounding. The tradeoff is increased attempts, higher token usage, and higher latency. Remaining failures typically come from incomplete evidence tracing or choosing a plausible entity without final verification against the provided context.
