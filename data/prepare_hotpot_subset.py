from __future__ import annotations

import argparse
import json
import urllib.parse
import urllib.request
from pathlib import Path


def _coerce_difficulty(level: str | None) -> str:
    value = (level or "medium").lower().strip()
    if value not in {"easy", "medium", "hard"}:
        return "medium"
    return value


def _context_to_chunks(context_obj: object) -> list[dict[str, str]]:
    chunks: list[dict[str, str]] = []
    if isinstance(context_obj, dict):
        titles = context_obj.get("title", [])
        sentences = context_obj.get("sentences", [])
        if isinstance(titles, list) and isinstance(sentences, list):
            for title, sentence_list in zip(titles, sentences):
                if isinstance(sentence_list, list):
                    text = " ".join(str(s).strip() for s in sentence_list if str(s).strip())
                else:
                    text = str(sentence_list).strip()
                if str(title).strip() and text:
                    chunks.append({"title": str(title).strip(), "text": text})
    elif isinstance(context_obj, list):
        for item in context_obj:
            if isinstance(item, list) and len(item) >= 2:
                title = str(item[0]).strip()
                sentence_list = item[1]
                if isinstance(sentence_list, list):
                    text = " ".join(str(s).strip() for s in sentence_list if str(s).strip())
                else:
                    text = str(sentence_list).strip()
                if title and text:
                    chunks.append({"title": title, "text": text})

    return chunks[:4]


def fetch_rows(offset: int, length: int) -> list[dict]:
    params = urllib.parse.urlencode(
        {
            "dataset": "hotpotqa/hotpot_qa",
            "config": "distractor",
            "split": "train",
            "offset": offset,
            "length": length,
        }
    )
    url = f"https://datasets-server.huggingface.co/rows?{params}"
    with urllib.request.urlopen(url, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload.get("rows", [])


def build_examples(target_size: int) -> list[dict]:
    examples: list[dict] = []
    seen: set[str] = set()
    offset = 0
    page = 100

    while len(examples) < target_size:
        rows = fetch_rows(offset=offset, length=page)
        if not rows:
            break
        offset += len(rows)

        for item in rows:
            row = item.get("row", item)
            qid = str(row.get("id", "")).strip() or f"hotpot_{offset}_{len(examples)}"
            if qid in seen:
                continue

            question = str(row.get("question", "")).strip()
            answer = str(row.get("answer", "")).strip()
            chunks = _context_to_chunks(row.get("context"))
            if not question or not answer or len(chunks) < 2:
                continue

            level = _coerce_difficulty(str(row.get("level", "medium")))
            examples.append(
                {
                    "qid": qid,
                    "difficulty": level,
                    "question": question,
                    "gold_answer": answer,
                    "context": chunks,
                }
            )
            seen.add(qid)

            if len(examples) >= target_size:
                break

    return examples


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare a HotpotQA subset in lab format")
    parser.add_argument("--size", type=int, default=100, help="Number of examples")
    parser.add_argument(
        "--out",
        type=str,
        default="data/hotpot_100.json",
        help="Output JSON path",
    )
    args = parser.parse_args()

    data = build_examples(target_size=args.size)
    if len(data) < args.size:
        raise RuntimeError(f"Requested {args.size} examples but only built {len(data)}")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {len(data)} examples to {out_path}")


if __name__ == "__main__":
    main()
