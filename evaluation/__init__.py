"""Production-independent evaluation harness for the fraud-detection pipeline.

This package NEVER influences production logic. Extraction, analysis, and reporting
do not import it, and it hardcodes no dataset value: it reads each fixture's
`ground_truth.json` generically and scores whatever the pipeline produced.

Modules:
  runner  — run extraction + analysis for a fixture folder and load its outputs
  scorer  — compare produced findings to ground truth (TP / FP / FN, precision/recall/F1)
  report  — render the human-readable + JSON evaluation summary

Team: Survey Corps | CIDECODE Hackathon 2026 | CID Karnataka
"""
