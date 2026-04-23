from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from .llm_runtime import AgentRuntime, build_runtime
from .schemas import AttemptTrace, QAExample, ReflectionEntry, RunRecord


def infer_failure_mode(
    final_score: int,
    final_reason: str,
    traces: list[AttemptTrace],
    reflections: list[ReflectionEntry],
) -> Literal[
    "none",
    "entity_drift",
    "incomplete_multi_hop",
    "wrong_final_answer",
    "looping",
    "reflection_overfit",
]:
    if final_score == 1:
        return "none"

    reason = final_reason.lower()
    answers = [t.answer.strip().lower() for t in traces if t.answer.strip()]
    if len(answers) >= 2 and len(set(answers)) == 1:
        return "looping"
    if reflections and len(answers) >= 2 and len(set(answers[-2:])) == 1:
        return "reflection_overfit"
    if "hop" in reason or "missing" in reason or "evidence" in reason:
        return "incomplete_multi_hop"
    if "entity" in reason or "drift" in reason:
        return "entity_drift"
    return "wrong_final_answer"


@dataclass
class BaseAgent:
    agent_type: Literal["react", "reflexion"]
    max_attempts: int = 1
    runtime: AgentRuntime = field(default_factory=lambda: build_runtime("mock"))

    def _resolve_attempt_budget(self, example: QAExample) -> int:
        if self.agent_type == "react":
            return 1
        adaptive = {
            "easy": min(self.max_attempts, 2),
            "medium": min(self.max_attempts, 3),
            "hard": self.max_attempts,
        }
        return max(1, adaptive.get(example.difficulty, self.max_attempts))

    def run(self, example: QAExample) -> RunRecord:
        reflection_memory: list[str] = []
        reflections: list[ReflectionEntry] = []
        traces: list[AttemptTrace] = []
        final_answer = ""
        final_score = 0
        final_reason = "No attempts executed."

        for attempt_id in range(1, self._resolve_attempt_budget(example) + 1):
            actor_response = self.runtime.actor_answer(
                example=example,
                attempt_id=attempt_id,
                agent_type=self.agent_type,
                reflection_memory=reflection_memory,
            )
            answer = actor_response.text.strip()
            judge, eval_tokens, eval_latency = self.runtime.evaluator(example, answer)

            token_estimate = actor_response.token_usage + eval_tokens
            latency_ms = actor_response.latency_ms + eval_latency

            final_answer = answer
            final_score = int(judge.score)
            final_reason = judge.reason

            reflection: ReflectionEntry | None = None
            if final_score == 0 and self.agent_type == "reflexion":
                reflection, refl_tokens, refl_latency = self.runtime.reflector(
                    example=example,
                    attempt_id=attempt_id,
                    judge=judge,
                    answer=answer,
                )
                reflections.append(reflection)
                reflection_memory.append(
                    f"Lesson: {reflection.lesson} | Strategy: {reflection.next_strategy}"
                )
                token_estimate += refl_tokens
                latency_ms += refl_latency

            trace = AttemptTrace(
                attempt_id=attempt_id,
                answer=answer,
                score=judge.score,
                reason=judge.reason,
                reflection=reflection,
                token_estimate=token_estimate,
                latency_ms=latency_ms,
            )
            traces.append(trace)

            if final_score == 1:
                break

        total_tokens = sum(t.token_estimate for t in traces)
        total_latency = sum(t.latency_ms for t in traces)
        failure_mode = infer_failure_mode(final_score, final_reason, traces, reflections)

        return RunRecord(
            qid=example.qid,
            question=example.question,
            gold_answer=example.gold_answer,
            agent_type=self.agent_type,
            predicted_answer=final_answer,
            is_correct=bool(final_score),
            attempts=len(traces),
            token_estimate=total_tokens,
            latency_ms=total_latency,
            failure_mode=failure_mode,
            reflections=reflections,
            traces=traces,
        )


class ReActAgent(BaseAgent):
    def __init__(self, runtime: AgentRuntime) -> None:
        super().__init__(agent_type="react", max_attempts=1, runtime=runtime)


class ReflexionAgent(BaseAgent):
    def __init__(self, runtime: AgentRuntime, max_attempts: int = 3) -> None:
        super().__init__(agent_type="reflexion", max_attempts=max_attempts, runtime=runtime)
