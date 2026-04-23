from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Literal, Protocol

from dotenv import load_dotenv
from openai import OpenAI

from .mock_runtime import actor_answer as mock_actor_answer
from .mock_runtime import evaluator as mock_evaluator
from .mock_runtime import reflector as mock_reflector
from .prompts import ACTOR_SYSTEM, EVALUATOR_SYSTEM, REFLECTOR_SYSTEM
from .schemas import JudgeResult, QAExample, ReflectionEntry
from .utils import normalize_answer


@dataclass
class RuntimeResponse:
    text: str
    token_usage: int
    latency_ms: int


class AgentRuntime(Protocol):
    def actor_answer(
        self,
        example: QAExample,
        attempt_id: int,
        agent_type: str,
        reflection_memory: list[str],
    ) -> RuntimeResponse: ...

    def evaluator(self, example: QAExample, answer: str) -> tuple[JudgeResult, int, int]: ...

    def reflector(
        self, example: QAExample, attempt_id: int, judge: JudgeResult, answer: str
    ) -> tuple[ReflectionEntry, int, int]: ...


class MockRuntime:
    def actor_answer(
        self,
        example: QAExample,
        attempt_id: int,
        agent_type: str,
        reflection_memory: list[str],
    ) -> RuntimeResponse:
        answer = mock_actor_answer(example, attempt_id, agent_type, reflection_memory)
        return RuntimeResponse(text=answer, token_usage=0, latency_ms=0)

    def evaluator(self, example: QAExample, answer: str) -> tuple[JudgeResult, int, int]:
        return mock_evaluator(example, answer), 0, 0

    def reflector(
        self, example: QAExample, attempt_id: int, judge: JudgeResult, answer: str
    ) -> tuple[ReflectionEntry, int, int]:
        return mock_reflector(example, attempt_id, judge), 0, 0


class OpenAIRuntime:
    def __init__(
        self,
        model: str = "gpt-4.1-mini",
        base_url: str | None = None,
        temperature: float = 0.1,
    ) -> None:
        load_dotenv()
        self.model = model
        self.temperature = temperature
        self.client = OpenAI(base_url=base_url)

    @staticmethod
    def _context_to_text(example: QAExample) -> str:
        chunks: list[str] = []
        for idx, chunk in enumerate(example.context, start=1):
            chunks.append(f"[{idx}] {chunk.title}: {chunk.text}")
        return "\n".join(chunks)

    def _chat(self, system: str, user: str, max_tokens: int = 220) -> RuntimeResponse:
        start = time.perf_counter()
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        latency_ms = int((time.perf_counter() - start) * 1000)
        text = response.choices[0].message.content or ""
        usage = response.usage
        total_tokens = (
            int(getattr(usage, "total_tokens", 0))
            if usage is not None
            else 0
        )
        return RuntimeResponse(text=text.strip(), token_usage=total_tokens, latency_ms=latency_ms)

    @staticmethod
    def _extract_json(text: str) -> dict:
        text = text.strip()
        if text.startswith("{") and text.endswith("}"):
            return json.loads(text)
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("No JSON object found in model output")
        return json.loads(text[start : end + 1])

    def actor_answer(
        self,
        example: QAExample,
        attempt_id: int,
        agent_type: str,
        reflection_memory: list[str],
    ) -> RuntimeResponse:
        memory_text = "\n".join(f"- {m}" for m in reflection_memory[-3:]) or "- (none)"
        user = (
            f"Question:\n{example.question}\n\n"
            f"Context:\n{self._context_to_text(example)}\n\n"
            f"Agent type: {agent_type}\n"
            f"Attempt: {attempt_id}\n"
            f"Reflection memory:\n{memory_text}\n\n"
            "Return only the final answer string."
        )
        return self._chat(ACTOR_SYSTEM, user, max_tokens=64)

    def evaluator(self, example: QAExample, answer: str) -> tuple[JudgeResult, int, int]:
        if normalize_answer(example.gold_answer) == normalize_answer(answer):
            return (
                JudgeResult(
                    score=1,
                    reason="Final answer matches the gold answer after normalization.",
                    missing_evidence=[],
                    spurious_claims=[],
                ),
                0,
                0,
            )

        user = (
            f"Question: {example.question}\n"
            f"Gold answer: {example.gold_answer}\n"
            f"Predicted answer: {answer}\n"
            f"Context:\n{self._context_to_text(example)}"
        )
        raw = self._chat(EVALUATOR_SYSTEM, user, max_tokens=200)
        try:
            parsed = self._extract_json(raw.text)
            judge = JudgeResult.model_validate(parsed)
        except Exception:
            judge = JudgeResult(
                score=0,
                reason="Predicted answer does not match the gold answer.",
                missing_evidence=["Need tighter grounding in provided context."],
                spurious_claims=[answer],
            )
        return judge, raw.token_usage, raw.latency_ms

    def reflector(
        self, example: QAExample, attempt_id: int, judge: JudgeResult, answer: str
    ) -> tuple[ReflectionEntry, int, int]:
        user = (
            f"Question: {example.question}\n"
            f"Wrong answer: {answer}\n"
            f"Evaluator reason: {judge.reason}\n"
            f"Missing evidence: {judge.missing_evidence}\n"
            f"Spurious claims: {judge.spurious_claims}\n"
            f"Context:\n{self._context_to_text(example)}"
        )
        raw = self._chat(REFLECTOR_SYSTEM, user, max_tokens=180)
        try:
            parsed = self._extract_json(raw.text)
            lesson = str(parsed.get("lesson", "Need to align answer with context evidence.")).strip()
            next_strategy = str(
                parsed.get("next_strategy", "Re-read context and verify the final entity before answering.")
            ).strip()
        except Exception:
            lesson = "The prior answer was weakly grounded and missed required evidence."
            next_strategy = "Explicitly verify each reasoning hop against context before finalizing."

        reflection = ReflectionEntry(
            attempt_id=attempt_id,
            failure_reason=judge.reason,
            lesson=lesson,
            next_strategy=next_strategy,
        )
        return reflection, raw.token_usage, raw.latency_ms


def build_runtime(
    mode: Literal["mock", "openai"] = "openai",
    model: str = "gpt-4.1-mini",
    base_url: str | None = None,
) -> AgentRuntime:
    if mode == "mock":
        return MockRuntime()
    return OpenAIRuntime(model=model, base_url=base_url)
