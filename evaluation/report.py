"""Render the evaluation result as a clean human-readable summary + machine JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def render_text(agg: dict[str, Any]) -> str:
    o = agg["overall"]
    lines: list[str] = []
    lines.append("=" * 60)
    lines.append("  FRAUD-DETECTION PIPELINE — EVALUATION RESULTS")
    lines.append("=" * 60)
    lines.append("")
    lines.append("## Overall Results")
    lines.append("")
    lines.append(f"Patterns Present : {o['patterns_present']}")
    lines.append(f"Detected         : {o['detected']}")
    lines.append(f"Missed           : {o['missed']}")
    lines.append(f"False Positives  : {o['false_positives']}")
    if o.get("not_evaluable"):
        lines.append(f"Not Evaluable    : {o['not_evaluable']}  (population-scale leads on tiny fixtures — see notes)")
    lines.append("")
    lines.append(f"Precision        : {o['precision'] * 100:.1f}%")
    lines.append(f"Recall           : {o['recall'] * 100:.1f}%")
    lines.append(f"F1 Score         : {o['f1'] * 100:.1f}%")
    lines.append("")
    lines.append("## Pattern Breakdown")
    lines.append("")
    lines.append(f"{'ID':>3}  {'Pattern':<30} {'Exp':>4} {'Det':>4} {'Miss':>4} {'FP':>4} {'Recall':>7}")
    lines.append("-" * 60)
    for row in agg["pattern_breakdown"]:
        recall = "-" if row["recall"] is None else f"{row['recall'] * 100:.0f}%"
        lines.append(
            f"{row['pattern_id']:>3}  {row['pattern_name']:<30} "
            f"{row['expected']:>4} {row['detected']:>4} {row['missed']:>4} "
            f"{row['false_positives']:>4} {recall:>7}"
        )
    lines.append("")

    # Honest gaps + misses + false positives per fixture, so nothing is hidden.
    misses = [(s["folder"], rec) for s in agg["fixtures"] for rec in s["fn"]]
    if misses:
        lines.append("## Misses (expected but not detected)")
        for folder, rec in misses:
            lines.append(f"  - {folder}: pattern {rec['pattern_id']} on {rec.get('expected_numbers') or '(unresolved)'}")
        lines.append("")
    fps = [(s["folder"], rec) for s in agg["fixtures"] for rec in s["fp"]]
    if fps:
        lines.append("## False positives (scored pattern on clean/non-finding)")
        for folder, rec in fps:
            lines.append(f"  - {folder}: pattern {rec['pattern_id']} on account {rec['account_number'] or '(any)'}")
        lines.append("")
    ne = [(s["folder"], rec) for s in agg["fixtures"] for rec in s["not_evaluable"]]
    if ne:
        lines.append("## Not evaluable (reported honestly, never scored)")
        for folder, rec in ne:
            lines.append(f"  - {folder}: {rec['reason']}")
        lines.append("")
    leads = [(s["folder"], rec) for s in agg["fixtures"] for rec in s.get("lead_on_clean", [])]
    if leads:
        lines.append("## Leads raised on clean accounts (informational — not counted as FP)")
        for folder, rec in leads:
            lines.append(f"  - {folder}: lead pattern {rec['pattern_id']} on {rec['accounts']}")
        lines.append("")
    return "\n".join(lines)


def write_outputs(agg: dict[str, Any], out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "evaluation_results.json"
    text_path = out_dir / "evaluation_summary.txt"
    # Drop the heavy per-fixture 'fixtures' detail from the compact JSON headline but keep it nested.
    json_path.write_text(json.dumps(agg, indent=2, default=str), encoding="utf-8")
    text_path.write_text(render_text(agg), encoding="utf-8")
    return json_path, text_path
