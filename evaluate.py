#!/usr/bin/env python3
"""
evaluate.py — One-command evaluation of the fraud-detection pipeline against the
synthetic validation suite.

    python evaluate.py                      # score every fixture that has a ground_truth.json
    python evaluate.py --folders pattern_17_round_trip pattern_08_money_trail
    python evaluate.py --force              # re-run extraction + analysis (ignore caches)
    python evaluate.py --dataset-root <dir> # point at any suite laid out the same way

Reads each fixture's `ground_truth.json` GENERICALLY — no dataset value is hardcoded and no
production module depends on this script. Analysis runs deterministically (no LLM), so the
numbers are reproducible and free. Honest by construction: expectations that cannot be
faithfully exercised (population-scale leads on tiny fixtures) are reported as `not_evaluable`,
never faked.

Team: Survey Corps | CIDECODE Hackathon 2026 | CID Karnataka
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.report import render_text, write_outputs  # noqa: E402
from evaluation.runner import run_fixture  # noqa: E402
from evaluation.scorer import aggregate, score_fixture  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Evaluate the pipeline against a synthetic validation suite.")
    ap.add_argument("--dataset-root", type=Path, default=ROOT / "synthetic_test_data")
    ap.add_argument("--folders", nargs="*", help="Specific fixture folder names (default: all with ground_truth.json).")
    ap.add_argument("--session-prefix", default="eval")
    ap.add_argument("--force", action="store_true", help="Re-run extraction + analysis, ignoring cached outputs.")
    ap.add_argument("--out-dir", type=Path, default=ROOT / "outputs" / "evaluation")
    args = ap.parse_args()

    dataset_root = args.dataset_root.resolve()
    folders = [p for p in sorted(dataset_root.iterdir()) if (p / "ground_truth.json").exists()]
    if args.folders:
        wanted = set(args.folders)
        folders = [p for p in folders if p.name in wanted]
    if not folders:
        print(f"No fixtures with ground_truth.json found under {dataset_root}", file=sys.stderr)
        return 2

    fixture_scores = []
    for folder in folders:
        started = time.perf_counter()
        try:
            bundle = run_fixture(folder, args.session_prefix, args.force)
            score = score_fixture(bundle)
        except Exception as exc:  # never let one fixture abort the whole evaluation
            print(f"ERROR {folder.name}: {exc}", file=sys.stderr)
            continue
        fixture_scores.append(score)
        c = score["counts"]
        print(
            f"{folder.name:<45} tp={c['tp']} fn={c['fn']} fp={c['fp']} "
            f"ne={c['not_evaluable']}  ({time.perf_counter() - started:.1f}s)"
        )

    agg = aggregate(fixture_scores)
    json_path, text_path = write_outputs(agg, args.out_dir)
    print()
    print(render_text(agg))
    print(f"[evaluate] wrote {json_path}")
    print(f"[evaluate] wrote {text_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
