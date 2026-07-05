"""Regression guards for false-positive cascades in analysis phase."""

import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from analysis_engine.counterparties import _account_like_numeric_candidates, _is_weaker_numeric_resolution, Resolution
from analysis_engine.models import Finding
from analysis_engine.scoring import finding_tier


def test_numeric_reference_tokens_are_not_treated_as_accounts():
    assert _account_like_numeric_candidates("NEFT/N29095242018/PRIYA REDDY/BKID0692937") == []
    assert _account_like_numeric_candidates("SALARY-S1775764550027/NEFT/Bajaj Auto Ltd") == []
    assert _account_like_numeric_candidates("ATM CASH WITHDRAWAL/18949/LUCKNOW") == []
    assert _account_like_numeric_candidates("TO A/C 123456789012 BENEFICIARY") == ["123456789012"]


def test_low_confidence_numeric_resolution_can_be_overridden_by_mirror_match():
    resolution = Resolution(
        counterparty_account="29095242018",
        counterparty_resolution_method="narration_similarity_match",
        counterparty_resolution_confidence=0.65,
    )
    assert _is_weaker_numeric_resolution(resolution, {"acct_004", "acct_006"}) is True


def test_high_confidence_first_contact_scores_as_independent_evidence():
    finding = Finding(
        19,
        "first_contact_large_transfer",
        ["acct_004", "acct_006"],
        ["acct_004_003542", "acct_006_005696"],
        "large observed-observed first contact",
        "",
        details={
            "amount": 152856.12,
            "counterparty_resolution_methods": ["amount_date_mirror_match"],
            "runtime_thresholds": {"large_transfer_min": 110387.64},
            "confidence_score": 0.85,
        },
    )
    assert finding_tier(finding) == 2


def test_generic_first_contact_remains_weak_context():
    finding = Finding(
        19,
        "first_contact_large_transfer",
        ["acct_001", "merchant@upi"],
        ["txn_1"],
        "large first contact to external endpoint",
        "",
        details={
            "amount": 20000.0,
            "counterparty_resolution_methods": ["exact_reference_or_upi_match"],
            "runtime_thresholds": {"large_transfer_min": 110387.64},
            "confidence_score": 1.0,
        },
    )
    assert finding_tier(finding) == 3
