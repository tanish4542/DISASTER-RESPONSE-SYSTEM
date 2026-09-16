"""Run custom messages against a previously trained model."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.src.inference import Classifier


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("message", nargs="+")
    args = parser.parse_args()
    classifier = Classifier(args.model)
    for message in args.message:
        print(json.dumps({"message": message, **classifier.predict(message)}, indent=2))


if __name__ == "__main__":
    main()
