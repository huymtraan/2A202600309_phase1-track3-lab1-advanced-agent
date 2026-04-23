from __future__ import annotations

import json
from pathlib import Path

import typer
from rich import print

from src.reflexion_lab.agents import ReActAgent, ReflexionAgent
from src.reflexion_lab.llm_runtime import build_runtime
from src.reflexion_lab.reporting import build_report, save_report
from src.reflexion_lab.utils import load_dataset, save_jsonl

app = typer.Typer(add_completion=False)


@app.command()
def main(
    dataset: str = "data/hotpot_mini.json",
    out_dir: str = "outputs/sample_run",
    reflexion_attempts: int = 3,
    runtime_mode: str = "openai",
    model: str = "gpt-4.1-mini",
    max_examples: int = 100,
) -> None:
    examples = load_dataset(dataset)
    if max_examples > 0:
        examples = examples[:max_examples]

    runtime = build_runtime(mode=runtime_mode, model=model)
    react = ReActAgent(runtime=runtime)
    reflexion = ReflexionAgent(runtime=runtime, max_attempts=reflexion_attempts)

    react_records = [react.run(example) for example in examples]
    reflexion_records = [reflexion.run(example) for example in examples]
    all_records = react_records + reflexion_records

    out_path = Path(out_dir)
    save_jsonl(out_path / "react_runs.jsonl", react_records)
    save_jsonl(out_path / "reflexion_runs.jsonl", reflexion_records)

    report = build_report(
        all_records,
        dataset_name=Path(dataset).name,
        mode=runtime_mode,
        extensions=[
            "structured_evaluator",
            "reflection_memory",
            "benchmark_report_json",
            "adaptive_max_attempts",
        ]
        + (["mock_mode_for_autograding"] if runtime_mode == "mock" else []),
    )
    json_path, md_path = save_report(report, out_path)

    print(f"[green]Saved[/green] {json_path}")
    print(f"[green]Saved[/green] {md_path}")
    print(json.dumps(report.summary, indent=2))


if __name__ == "__main__":
    app()
