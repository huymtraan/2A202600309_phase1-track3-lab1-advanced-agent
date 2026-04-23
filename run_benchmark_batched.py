from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
from rich import print

from src.reflexion_lab.agents import ReActAgent, ReflexionAgent
from src.reflexion_lab.llm_runtime import build_runtime
from src.reflexion_lab.reporting import build_report, save_report
from src.reflexion_lab.schemas import QAExample, RunRecord
from src.reflexion_lab.utils import load_dataset, save_jsonl

app = typer.Typer(add_completion=False)


def _detect_anomalies(summary: dict[str, Any], exceptions: int) -> list[str]:
    issues: list[str] = []
    react = summary.get("react", {})
    reflexion = summary.get("reflexion", {})

    if exceptions > 0:
        issues.append(f"exceptions_detected:{exceptions}")
    if react and reflexion and reflexion.get("em", 0) < react.get("em", 0):
        issues.append("reflexion_em_below_react")
    if reflexion and reflexion.get("avg_attempts", 0) <= 1:
        issues.append("low_reflexion_retry_activity")
    if react and react.get("avg_token_estimate", 0) == 0:
        issues.append("zero_tokens_react")
    if reflexion and reflexion.get("avg_token_estimate", 0) == 0:
        issues.append("zero_tokens_reflexion")
    return issues


@app.command()
def main(
    dataset: str = "data/hotpot_100.json",
    out_dir: str = "outputs/hotpot_openai_batched",
    batch_size: int = 25,
    max_examples: int = 100,
    reflexion_attempts: int = 2,
    runtime_mode: str = "openai",
    model: str = "gpt-4.1-mini",
) -> None:
    examples = load_dataset(dataset)
    if max_examples > 0:
        examples = examples[:max_examples]

    if not examples:
        raise typer.BadParameter("Dataset is empty after slicing")
    if batch_size <= 0:
        raise typer.BadParameter("batch_size must be > 0")

    runtime = build_runtime(mode=runtime_mode, model=model)
    react = ReActAgent(runtime=runtime)
    reflexion = ReflexionAgent(runtime=runtime, max_attempts=reflexion_attempts)

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    all_react_records: list[RunRecord] = []
    all_reflexion_records: list[RunRecord] = []
    monitor_rows: list[dict[str, Any]] = []

    total_batches = (len(examples) + batch_size - 1) // batch_size

    for batch_idx in range(total_batches):
        start = batch_idx * batch_size
        end = min(start + batch_size, len(examples))
        batch_examples: list[QAExample] = examples[start:end]
        batch_name = f"batch_{batch_idx + 1:02d}"
        batch_dir = out_path / batch_name
        batch_dir.mkdir(parents=True, exist_ok=True)

        print(f"[cyan]Running[/cyan] {batch_name} with examples [{start}:{end})")

        batch_react: list[RunRecord] = []
        batch_reflexion: list[RunRecord] = []
        exceptions = 0

        for ex in batch_examples:
            try:
                batch_react.append(react.run(ex))
            except Exception as exc:
                exceptions += 1
                print(f"[red]react error[/red] qid={ex.qid}: {exc}")

            try:
                batch_reflexion.append(reflexion.run(ex))
            except Exception as exc:
                exceptions += 1
                print(f"[red]reflexion error[/red] qid={ex.qid}: {exc}")

        all_react_records.extend(batch_react)
        all_reflexion_records.extend(batch_reflexion)

        save_jsonl(batch_dir / "react_runs.jsonl", batch_react)
        save_jsonl(batch_dir / "reflexion_runs.jsonl", batch_reflexion)

        batch_report = build_report(
            batch_react + batch_reflexion,
            dataset_name=f"{Path(dataset).name}:{batch_name}",
            mode=runtime_mode,
            extensions=[
                "structured_evaluator",
                "reflection_memory",
                "benchmark_report_json",
                "adaptive_max_attempts",
            ],
        )
        json_path, md_path = save_report(batch_report, batch_dir)
        anomalies = _detect_anomalies(batch_report.summary, exceptions)

        monitor_row = {
            "batch": batch_name,
            "start_idx": start,
            "end_idx": end,
            "num_examples": len(batch_examples),
            "react_count": len(batch_react),
            "reflexion_count": len(batch_reflexion),
            "exceptions": exceptions,
            "anomalies": anomalies,
            "summary": batch_report.summary,
            "report_json": str(json_path),
            "report_md": str(md_path),
        }
        monitor_rows.append(monitor_row)

        print(f"[green]Saved[/green] {json_path}")
        print(f"[green]Saved[/green] {md_path}")
        print(json.dumps({"batch": batch_name, "anomalies": anomalies}, ensure_ascii=False))

        monitor_path = out_path / "batch_monitor.jsonl"
        with monitor_path.open("w", encoding="utf-8") as f:
            for row in monitor_rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    save_jsonl(out_path / "react_runs.jsonl", all_react_records)
    save_jsonl(out_path / "reflexion_runs.jsonl", all_reflexion_records)

    final_records = all_react_records + all_reflexion_records
    final_report = build_report(
        final_records,
        dataset_name=Path(dataset).name,
        mode=runtime_mode,
        extensions=[
            "structured_evaluator",
            "reflection_memory",
            "benchmark_report_json",
            "adaptive_max_attempts",
        ],
    )
    final_json, final_md = save_report(final_report, out_path)

    print(f"[bold green]Final saved[/bold green] {final_json}")
    print(f"[bold green]Final saved[/bold green] {final_md}")
    print(json.dumps(final_report.summary, indent=2))


if __name__ == "__main__":
    app()
