# Copied from: analysis phase cidecode hackathon/analysis phase cidecode hackathon/analysis_engine/config.py
"""Configuration values that are universal safeguards, never dataset tuning."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AnalysisConfig:
    """Configurable universal limits; patterns 4–7 thresholds come from baseline."""

    balance_tolerance: float = 1.0
    money_epsilon: float = 0.01

    duplicate_date_window_days: int = 1
    duplicate_amount_relative_tolerance: float = 0.005
    duplicate_narration_similarity: float = 0.80
    duplicate_recurring_min_occurrences: int = 3
    duplicate_recurring_gap_tolerance_days: int = 4

    reversal_amount_relative_tolerance: float = 0.02
    reversal_narration_similarity: float = 0.45
    reversal_window_multiplier: float = 3.0

    default_round_trip_window_days: int = 30
    settlement_window_multiplier: float = 10.0
    max_round_trip_hops: int = 5
    max_cycle_length: int = 6
    # A laundering cycle is a strong (Tier-1) claim, so — like the round-trip detector —
    # every edge in the cycle must be CORROBORATED, not a coincidental name guess. A bare
    # narration name-similarity match (confidence 0.65) or an llm-inferred link (0.40) is
    # too weak to assert a closed loop; only reference / UPI / ledger-pair / amount-date
    # mirror matches (>= 0.85) qualify. This mirrors round-trip's guard so the two cycle
    # detectors share one evidence bar — evidence strengthens only through independent
    # confirmation, never through a weak link.
    circular_min_edge_confidence: float = 0.85

    upper_amount_quantile: float = 0.99
    high_volume_quantile: float = 0.75
    high_ratio_quantile: float = 0.75
    low_ratio_quantile: float = 0.25
    dense_activity_quantile: float = 0.95
    minimum_cluster_size: int = 3

    maximum_findings_per_pattern: int = 5_000
    finding_txn_id_report_limit: int = 200
    maximum_trace_debits: int = 10_000
    money_trail_auto_max_credits: int = 100
    money_trail_strong_account_credit_quantile: float = 0.90
    money_trail_strict_credit_quantile: float = 0.99
    money_trail_reported_txn_id_limit: int = 30
    money_trail_long_chain_debit_count: int = 25
    strong_counterparty_confidence_min: float = 0.65
    amount_common_frequency_quantile: float = 0.90
    amount_common_frequency_share: float = 0.01
    amount_match_strict_counterparty_confidence_min: float = 0.90
    narration_corrob_min_similarity: float = 0.45

    llm_model: str = "llama-3.3-70b-versatile"
    enable_llm_fallback: bool = True
    groq_api_keys_env: str = "GROQ_API_KEYS"
    groq_api_key_env: str = "GROQ_API_KEY"
    llm_role_a_max_calls: int = 500
    llm_role_b_auto_percentile: float = 0.95
    llm_role_b_max_auto_accounts: int = 15
    llm_role_b_max_manual_accounts: int = 10
    llm_run_max_calls: int = 25
    llm_key_retry_cooldown_seconds: int = 60
    llm_request_min_interval_seconds: float = 0.25
    llm_retry_base_seconds: float = 0.5
    llm_retry_max_seconds: float = 8.0
    llm_pattern22_max_transactions: int = 80

    sqlite_busy_timeout_ms: int = 30_000

    # ── New pattern thresholds (11–21) ──
    high_throughput_min_counterparties: int = 3
    high_throughput_retention_max: float = 0.10

    credit_to_cash_window_days: int = 3
    credit_to_cash_account_credit_quantile: float = 0.75
    credit_to_cash_recurring_min_occurrences: int = 3
    credit_to_cash_high_ratio_override: float = 0.70

    round_value_min_repeats: int = 3
    round_value_divisor: float = 1000.0

    low_value_test_max_amount: float = 100.0
    low_value_test_min_pairs: int = 2

    reversal_cluster_min_pairs: int = 3

    hub_ranking_min_degree: int = 3

    shared_upi_common_account_share: float = 0.50
    shared_upi_common_account_count: int = 3
    # A UPI handle used by a large FRACTION of the case's accounts is shared public
    # infrastructure (a biller / merchant / utility such as an electricity-board payment
    # handle), NOT a private shared identity: many people independently paying the same
    # payee is not evidence of common ownership. Suppress such broadly-shared handles.
    # Data-driven (a share of accounts), so it scales to any case size and is not tuned to
    # any dataset. A genuine shared-mule identity is used by a small ring (2-3 accounts).
    shared_upi_infrastructure_account_share: float = 0.10
    # ...but only treat a handle as infrastructure once it is shared by enough accounts
    # for "broadly shared" to be meaningful. A private mule ring is a SMALL set (2-3
    # accounts), so a handle shared by fewer than this is never suppressed regardless of
    # case size — this protects a genuine 2-account shared identity in a tiny case while
    # still removing electricity-board / merchant handles fanned across many payers.
    shared_upi_infrastructure_min_accounts: int = 4

    first_contact_recurring_min_events: int = 3
    first_contact_recurring_min_gap_days: int = 20
    first_contact_recurring_max_gap_days: int = 40
    first_contact_recurring_amount_tolerance: float = 0.25
    first_contact_recurring_day_tolerance: int = 5

    dormant_reactivation_outflow_window_days: int = 7
    dormant_reactivation_outflow_ratio_min: float = 0.70

    ml_lead_max_accounts: int = 20
