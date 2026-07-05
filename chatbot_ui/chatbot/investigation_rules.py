"""
investigation_rules.py
─────────────────────────────────────────────────────────────────────────────
CIDECODE 2026 — Multi-Accused Cross-Account Investigation Engine
Module: Reusable Investigation Rule Engine (Phase 3, Goals 4 & 5)

A rule is a pure function `rule(case) -> list[Finding]`. Each Finding is a
structured, evidence-backed record — NOT free text — so the same rule output
can drive a chatbot answer, a report section, or a risk table without
re-deriving anything. Findings are deterministic: every field comes from the
in-memory transaction data, so nothing here can hallucinate an amount, a date,
or a link (Goal 7's "do not fabricate explanations" applies here too).

Thresholds are module-level constants with a one-line rationale each, so an
investigator can see — and a reviewer can challenge — exactly what "large",
"rapid", or "structuring" means in this engine.

Reuses prepared_transactions()/add_counterparty() from frequency_analysis so
amount/direction normalisation and the counterparty heuristic have a single
definition shared with the rest of the Investigation Intelligence layer.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import pandas as pd

from chatbot.frequency_analysis import add_counterparty, prepared_transactions

# ── Tunable rule thresholds (each with its rationale) ────────────────────────
LARGE_CASH_AMOUNT = 100_000          # ₹1L+ cash movement is reportable-scale
RAPID_TRANSFER_DAYS = 2              # "immediately after" = same/next couple days
RAPID_TRANSFER_RATIO = 0.80          # ≥80% of an inbound credit moved straight out
RAPID_TRANSFER_UPPER = 1.20          # …and ≤120%, so it is the SAME money passing
                                     # through, not just a high-spending account
RAPID_TRANSFER_MIN_AMOUNT = 10_000   # ignore trivial credits (a ₹7 UPI cashback
                                     # followed by normal spending is not layering)
STRUCTURING_THRESHOLD = 50_000       # classic sub-₹50k "keep it under the radar"
STRUCTURING_MIN_COUNT = 3            # need a cluster, not a single deposit
STRUCTURING_WINDOW_DAYS = 7          # deposits bunched within a week
ROUND_AMOUNT_MODULUS = 10_000        # ₹10k-round amounts rarely occur naturally
ROUND_AMOUNT_MIN_COUNT = 3
REPEAT_BENEFICIARY_MIN = 4           # same payee this many times = a channel
SINGLE_LARGE_DEBIT_SHARE = 0.60      # one debit ≥60% of all outflow stands out
CASH_NARRATION_RE = re.compile(r"\b(?:cash|atm|withdrawal|deposit|cdm|cwdl)\b", re.IGNORECASE)
SALARY_NARRATION_PAT = r"\b(?:salary|sal|payroll|wages|stipend)\b"


@dataclass
class Finding:
    """One evidence-backed investigation finding produced by a rule."""

    rule: str
    account: str
    holder: str
    risk: str            # "High" | "Medium" | "Low"
    summary: str
    evidence: list[str] = field(default_factory=list)
    citations: list[dict] = field(default_factory=list)

    def render(self) -> str:
        """Human-readable block matching the spec's Finding layout."""
        arrow = "\n    ↓\n"
        evidence_block = arrow.join(f"    {line}" for line in self.evidence) if self.evidence else "    (see summary)"
        return (
            f"Finding — {self.rule}\n"
            f"  Account: {self.account} ({self.holder})\n"
            f"  Summary: {self.summary}\n"
            f"  Evidence:\n{evidence_block}\n"
            f"  Risk: {self.risk}"
        )


def _rupees(value: float) -> str:
    return f"₹{value:,.2f}"


def _date(row: pd.Series) -> str:
    d = row.get("Date")
    return d.strftime("%d/%m/%Y") if isinstance(d, pd.Timestamp) and pd.notna(d) else "?"


def _citation(row: pd.Series, account_id: str) -> dict:
    return {
        "type": "transaction",
        "ref": str(row.get("txn_id") or row.get("Transaction_ID") or "?"),
        "account": str(account_id),
        "date": _date(row),
    }


def _holder(case: dict, account_id: str, df: pd.DataFrame) -> str:
    acct_json = case.get("accounts", {}).get(str(account_id))
    if acct_json:
        holder = acct_json.get("account_details", {}).get("account_holder")
        if holder:
            return str(holder)
    if "account_holder" in df.columns and not df.empty:
        holder = df["account_holder"].dropna()
        if not holder.empty:
            return str(holder.iloc[0])
    return "(unidentified)"


# ─────────────────────────────────────────────────────────────────────────────
# INDIVIDUAL RULES — each returns a list[Finding] for the whole case.
# ─────────────────────────────────────────────────────────────────────────────

def _iter_accounts(case: dict):
    """Yield (account_id, holder, per-account prepared+counterparty DataFrame)."""
    df = case["clean"]
    if "account_number" not in df.columns:
        return
    for account_id in df["account_number"].astype(str).unique():
        adf = add_counterparty(prepared_transactions(case, account_id))
        yield account_id, _holder(case, account_id, adf), adf


def _rapid_passthrough(adf: pd.DataFrame, credit: pd.Series):
    """
    Given a credit row, return the first subsequent debit (within the rapid
    window) whose amount is close to the credit — i.e. the SAME money leaving
    again. Returns None when no such near-equal outflow exists. Matching a
    single near-equal debit (rather than summing every debit in the window)
    is what distinguishes genuine pass-through from an account that simply
    happens to spend a lot in the days after a small credit.
    """
    c_date = credit.get("Date")
    if not (isinstance(c_date, pd.Timestamp) and pd.notna(c_date)):
        return None
    credit_amt = float(credit["_amount"])
    window_end = c_date + pd.Timedelta(days=RAPID_TRANSFER_DAYS)
    debits = adf[(adf["_direction"] == "debit")
                 & (adf["Date"] >= c_date) & (adf["Date"] <= window_end)
                 & (adf["_amount"] >= RAPID_TRANSFER_RATIO * credit_amt)
                 & (adf["_amount"] <= RAPID_TRANSFER_UPPER * credit_amt)]
    return debits.sort_values("Date").iloc[0] if not debits.empty else None


def rule_rapid_outward_transfer(case: dict) -> list[Finding]:
    """
    A material credit followed within a couple of days by a single near-equal
    outbound debit — the classic pass-through / layering signature.
    """
    findings = []
    for account_id, holder, adf in _iter_accounts(case):
        credits = adf[(adf["_direction"] == "credit") & (adf["_amount"] >= RAPID_TRANSFER_MIN_AMOUNT)]
        for _, credit in credits.iterrows():
            debit = _rapid_passthrough(adf, credit)
            if debit is None:
                continue
            credit_amt = float(credit["_amount"])
            moved = float(debit["_amount"])
            pct = round(100 * moved / credit_amt)
            findings.append(Finding(
                rule="Rapid Outward Transfer",
                account=account_id, holder=holder, risk="High",
                summary=(f"{_rupees(credit_amt)} received on {_date(credit)} left again as "
                         f"{_rupees(moved)} ({pct}%) within {RAPID_TRANSFER_DAYS} day(s)."),
                evidence=[
                    f"Credit {_rupees(credit_amt)} on {_date(credit)}",
                    f"Debit {_rupees(moved)} on {_date(debit)}",
                    f"Within {RAPID_TRANSFER_DAYS} day(s) — {pct}% of the inbound amount",
                ],
                citations=[_citation(credit, account_id), _citation(debit, account_id)],
            ))
    return findings


def rule_large_cash_deposit(case: dict) -> list[Finding]:
    """Cash-flagged credit at or above the large-cash threshold."""
    findings = []
    for account_id, holder, adf in _iter_accounts(case):
        credits = adf[(adf["_direction"] == "credit") & (adf["_amount"] >= LARGE_CASH_AMOUNT)]
        for _, row in credits.iterrows():
            if CASH_NARRATION_RE.search(str(row.get("Narration") or "")):
                findings.append(Finding(
                    rule="Large Cash Deposit",
                    account=account_id, holder=holder, risk="High",
                    summary=f"Cash deposit of {_rupees(float(row['_amount']))} on {_date(row)}.",
                    evidence=[f"Cash credit {_rupees(float(row['_amount']))} on {_date(row)}",
                              f"Narration: {str(row.get('Narration') or '').strip()[:80]}"],
                    citations=[_citation(row, account_id)],
                ))
    return findings


def rule_structuring(case: dict) -> list[Finding]:
    """
    Structuring / smurfing: a cluster of just-under-threshold credits bunched
    into a short window whose total crosses the threshold they each stay below.
    """
    findings = []
    for account_id, holder, adf in _iter_accounts(case):
        credits = adf[(adf["_direction"] == "credit")
                      & (adf["_amount"] > 0)
                      & (adf["_amount"] < STRUCTURING_THRESHOLD)].dropna(subset=["Date"])
        if len(credits) < STRUCTURING_MIN_COUNT:
            continue
        credits = credits.sort_values("Date")
        # Sliding window over dates: any run of ≥N sub-threshold credits inside
        # STRUCTURING_WINDOW_DAYS that together exceed the threshold.
        dates = credits["Date"].tolist()
        for i in range(len(credits)):
            window_end = dates[i] + pd.Timedelta(days=STRUCTURING_WINDOW_DAYS)
            cluster = credits[(credits["Date"] >= dates[i]) & (credits["Date"] <= window_end)]
            total = float(cluster["_amount"].sum())
            if len(cluster) >= STRUCTURING_MIN_COUNT and total > STRUCTURING_THRESHOLD:
                findings.append(Finding(
                    rule="Structuring / Smurfing",
                    account=account_id, holder=holder, risk="High",
                    summary=(f"{len(cluster)} deposits each under {_rupees(STRUCTURING_THRESHOLD)} "
                             f"within {STRUCTURING_WINDOW_DAYS} days totalling {_rupees(total)}."),
                    evidence=[f"{len(cluster)} sub-{_rupees(STRUCTURING_THRESHOLD)} credits "
                              f"from {dates[i].strftime('%d/%m/%Y')}",
                              f"Combined {_rupees(total)} — exceeds the threshold each stayed below"],
                    citations=[_citation(r, account_id) for _, r in cluster.iterrows()],
                ))
                break  # one structuring finding per account is enough to flag
    return findings


def rule_round_amount_transactions(case: dict) -> list[Finding]:
    """Repeated perfectly-round amounts (multiples of ₹10,000)."""
    findings = []
    for account_id, holder, adf in _iter_accounts(case):
        round_txns = adf[(adf["_amount"] > 0) & (adf["_amount"] % ROUND_AMOUNT_MODULUS == 0)]
        if len(round_txns) >= ROUND_AMOUNT_MIN_COUNT:
            total = float(round_txns["_amount"].sum())
            findings.append(Finding(
                rule="Round Amount Transactions",
                account=account_id, holder=holder, risk="Medium",
                summary=(f"{len(round_txns)} transactions in exact multiples of "
                         f"{_rupees(ROUND_AMOUNT_MODULUS)} (total {_rupees(total)})."),
                evidence=[f"{len(round_txns)} round-number transactions",
                          f"Combined {_rupees(total)} — round amounts rarely arise from genuine trade"],
                citations=[_citation(r, account_id) for _, r in round_txns.head(10).iterrows()],
            ))
    return findings


def rule_repeated_beneficiary(case: dict) -> list[Finding]:
    """Same inferred beneficiary paid repeatedly (a dedicated payout channel)."""
    findings = []
    for account_id, holder, adf in _iter_accounts(case):
        debits = adf[(adf["_direction"] == "debit") & adf["_counterparty"].notna()]
        if debits.empty:
            continue
        counts = debits.groupby("_counterparty")["_amount"].agg(["count", "sum"])
        for beneficiary, row in counts[counts["count"] >= REPEAT_BENEFICIARY_MIN].iterrows():
            findings.append(Finding(
                rule="Repeated Transfers to Same Beneficiary",
                account=account_id, holder=holder, risk="Medium",
                summary=(f"{int(row['count'])} transfers to '{beneficiary}' "
                         f"totalling {_rupees(float(row['sum']))}."),
                evidence=[f"{int(row['count'])} debits to inferred beneficiary '{beneficiary}'",
                          f"Combined {_rupees(float(row['sum']))}"],
                citations=[_citation(r, account_id)
                           for _, r in debits[debits["_counterparty"] == beneficiary].head(10).iterrows()],
            ))
    return findings


def rule_salary_immediately_withdrawn(case: dict) -> list[Finding]:
    """Salary credit followed by an outbound debit within the rapid window."""
    findings = []
    for account_id, holder, adf in _iter_accounts(case):
        salary_credits = adf[(adf["_direction"] == "credit")
                             & adf["Narration"].astype(str).str.contains(
                                 SALARY_NARRATION_PAT, case=False, na=False, regex=True)]
        for _, credit in salary_credits.iterrows():
            debit = _rapid_passthrough(adf, credit)
            if debit is None:
                continue
            moved = float(debit["_amount"])
            findings.append(Finding(
                rule="Salary Immediately Withdrawn",
                account=account_id, holder=holder, risk="Medium",
                summary=(f"Salary of {_rupees(float(credit['_amount']))} on {_date(credit)} "
                         f"was moved out ({_rupees(moved)}) within {RAPID_TRANSFER_DAYS} day(s)."),
                evidence=[f"Salary credit {_rupees(float(credit['_amount']))} on {_date(credit)}",
                          f"Debit {_rupees(moved)} on {_date(debit)}"],
                citations=[_citation(credit, account_id), _citation(debit, account_id)],
            ))
    return findings


def rule_single_large_debit(case: dict) -> list[Finding]:
    """A single debit that dominates the account's entire outflow."""
    findings = []
    for account_id, holder, adf in _iter_accounts(case):
        debits = adf[adf["_direction"] == "debit"]
        total_out = float(debits["_amount"].sum())
        if total_out <= 0 or len(debits) < 3:
            continue
        largest = debits.loc[debits["_amount"].idxmax()]
        share = float(largest["_amount"]) / total_out
        if share >= SINGLE_LARGE_DEBIT_SHARE:
            findings.append(Finding(
                rule="Single Large Debit",
                account=account_id, holder=holder, risk="Medium",
                summary=(f"One debit of {_rupees(float(largest['_amount']))} on {_date(largest)} is "
                         f"{round(share * 100)}% of the account's total outflow."),
                evidence=[f"Debit {_rupees(float(largest['_amount']))} on {_date(largest)}",
                          f"{round(share * 100)}% of {_rupees(total_out)} total outflow"],
                citations=[_citation(largest, account_id)],
            ))
    return findings


# Registry — add new rules here; every consumer picks them up automatically.
_RULES = [
    rule_rapid_outward_transfer,
    rule_large_cash_deposit,
    rule_structuring,
    rule_round_amount_transactions,
    rule_repeated_beneficiary,
    rule_salary_immediately_withdrawn,
    rule_single_large_debit,
]

_RISK_ORDER = {"High": 0, "Medium": 1, "Low": 2}


def run_all_rules(case: dict, account_id: str | None = None) -> list[Finding]:
    """
    Run every rule across the case (or one account) and return findings sorted
    highest-risk first. This is the reusable entry point for both the chatbot
    and any report generator (Goal 4: "reusable across reports and answers").
    """
    findings: list[Finding] = []
    for rule in _RULES:
        findings.extend(rule(case))
    if account_id:
        findings = [f for f in findings if f.account == str(account_id)]
    findings.sort(key=lambda f: _RISK_ORDER.get(f.risk, 3))
    return findings


# ─────────────────────────────────────────────────────────────────────────────
# NATURAL-LANGUAGE HANDLER
# ─────────────────────────────────────────────────────────────────────────────

_RULES_RE = re.compile(
    r"\b(suspicious|suspicion|red[\s-]?flag|abnormal|unusual behaviou?r|"
    r"structuring|smurf|layering|rapid (transfer|outward|withdrawal)|"
    r"round[\s-]?amount|money launder|investigat\w* (finding|rule)|"
    r"apply rules|run rules|risk finding|which accounts? (are|look) suspicious|"
    r"flagged behaviou?r|find (suspicious|risky) account)\b",
    re.IGNORECASE,
)


def matches_rules_request(question: str) -> bool:
    """True when the question asks for rule-based suspicious-activity findings."""
    return bool(_RULES_RE.search(question))


def try_rules_answer(question: str, case: dict) -> dict | None:
    """Deterministic rule-engine findings for suspicious-activity questions."""
    if not matches_rules_request(question):
        return None

    from chatbot.structured_queries import _resolve_account

    account_id = _resolve_account(question, case)
    findings = run_all_rules(case, account_id=account_id)

    scope = f" for account {account_id}" if account_id else ""
    if not findings:
        return {
            "answer": f"No investigation rule triggered{scope} on the current case data.",
            "citations": [],
            "matched_pattern": "investigation_rules_empty",
        }

    blocks = [f.render() for f in findings[:12]]
    more = f"\n\n(+{len(findings) - 12} more finding(s) not shown)" if len(findings) > 12 else ""
    high = sum(1 for f in findings if f.risk == "High")
    answer = (
        f"{len(findings)} investigation finding(s){scope} "
        f"({high} High-risk):\n\n" + "\n\n".join(blocks) + more
    )
    citations = [c for f in findings[:12] for c in f.citations]
    return {"answer": answer, "citations": citations, "matched_pattern": "investigation_rules"}
