"""
Case discovery helpers for the investigator chatbot.

The preferred layout is project_root/cases/<case_id>/..., with one complete
extraction output per case. This module also recognizes the current legacy
demo layout where the sample case files live directly inside chatbot/.
"""

from pathlib import Path


CASES_ROOT = Path(__file__).parent.parent / "cases"
EXTRACTIONS_ROOT = Path(__file__).parent.parent / "outputs" / "extractions"
LEGACY_CASE_ID = "demo_case"
LEGACY_CASE_DIR = Path(__file__).parent
REQUIRED_FILES = [
    "clean_transactions.csv",
    "flagged_transactions.csv",
    "duplicates.csv",
    "metadata.json",
]


def _case_dir_for_validation(case_id: str) -> Path:
    case_dir = CASES_ROOT / case_id
    if case_dir.exists():
        return case_dir
    extraction_dir = EXTRACTIONS_ROOT / case_id
    if extraction_dir.exists():
        return extraction_dir
    if case_id == LEGACY_CASE_ID:
        return LEGACY_CASE_DIR
    return case_dir


def validate_case(case_id: str) -> tuple[bool, str]:
    """
    Validate that a case directory has all files needed for chatbot loading.

    Returns (True, "") when valid, otherwise (False, reason).
    """
    case_dir = _case_dir_for_validation(case_id)
    if not case_dir.exists():
        return False, f"Case directory does not exist: {case_dir}"
    if not case_dir.is_dir():
        return False, f"Case path is not a directory: {case_dir}"

    missing = [name for name in REQUIRED_FILES if not (case_dir / name).exists()]
    if missing:
        return False, "Missing required file(s): " + ", ".join(missing)

    account_jsons = [
        path
        for path in case_dir.glob("*.json")
        if path.name != "metadata.json"
    ]
    statements_dir = case_dir / "statements"
    if statements_dir.exists():
        account_jsons.extend(statements_dir.glob("*.json"))

    if not account_jsons:
        return False, "Missing per-account JSON file(s)"

    return True, ""


def list_available_cases() -> list[str]:
    """Return valid case IDs from cases/, extraction outputs, or the legacy demo."""
    valid_cases = []
    seen = set()
    for root in (CASES_ROOT, EXTRACTIONS_ROOT):
        if not root.exists():
            continue
        for path in sorted(root.iterdir()):
            if not path.is_dir():
                continue
            if path.name in seen:
                continue
            ok, _ = validate_case(path.name)
            if ok:
                valid_cases.append(path.name)
                seen.add(path.name)

    legacy_ok, _ = validate_case(LEGACY_CASE_ID)
    if not valid_cases and legacy_ok:
        valid_cases.append(LEGACY_CASE_ID)

    return valid_cases


def get_case_dir(case_id: str) -> Path:
    """
    Resolve a case ID to its directory, raising an actionable error if invalid.
    """
    ok, reason = validate_case(case_id)
    if ok:
        return _case_dir_for_validation(case_id)

    valid_cases = list_available_cases()
    available = ", ".join(valid_cases) if valid_cases else "none"
    raise FileNotFoundError(
        f"Invalid case '{case_id}': {reason}. Valid case(s): {available}. "
        f"Expected complete cases under {CASES_ROOT} or {EXTRACTIONS_ROOT}."
    )


def pick_case_interactively() -> str:
    """
    CLI helper for selecting a case. Auto-selects when only one valid case exists.
    """
    cases = list_available_cases()
    if not cases:
        raise FileNotFoundError(
            f"No valid chatbot cases found under {CASES_ROOT}. "
            f"Also checked extraction outputs under {EXTRACTIONS_ROOT}. "
            "Run the extraction pipeline first, or place a complete case folder "
            "with clean_transactions.csv, flagged_transactions.csv, "
            "duplicates.csv, metadata.json, and per-account JSON files."
        )

    if len(cases) == 1:
        case_id = cases[0]
        case_dir = get_case_dir(case_id)
        source = "legacy chatbot folder" if case_id == LEGACY_CASE_ID else case_dir.parent.name
        print(f"[case_registry] Auto-selected case '{case_id}' from {source}.")
        return case_id

    print("Available cases:")
    for index, case_id in enumerate(cases, start=1):
        print(f"  {index}. {case_id}")

    while True:
        choice = input("Select case by number or ID: ").strip()
        if choice.isdigit():
            index = int(choice)
            if 1 <= index <= len(cases):
                return cases[index - 1]
        if choice in cases:
            return choice
        print("Invalid selection. Try again.")
