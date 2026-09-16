"""Prepare a labeled CSV downloaded from a documented dataset source.

This utility only renames selected columns and applies the shared text
normalizer. It never downloads data, creates labels, or maps labels silently.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.src.preprocessing import normalize_text


def prepare(input_path: Path, output_path: Path, text_column: str, label_column: str) -> None:
    frame = pd.read_csv(input_path)
    missing = {text_column, label_column} - set(frame.columns)
    if missing:
        raise ValueError(f"Input is missing required columns: {sorted(missing)}")
    prepared = frame[[text_column, label_column]].rename(
        columns={text_column: "text", label_column: "label"}
    )
    prepared["text"] = prepared["text"].map(normalize_text)
    prepared["label"] = prepared["label"].astype("string").str.strip()
    prepared = prepared[(prepared["text"] != "") & prepared["label"].notna()]
    if prepared["label"].nunique() < 2:
        raise ValueError("Prepared data must contain at least two distinct labels")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    prepared.to_csv(output_path, index=False)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--text-column", default="text")
    parser.add_argument("--label-column", default="label")
    args = parser.parse_args()
    prepare(args.input, args.output, args.text_column, args.label_column)


if __name__ == "__main__":
    main()
