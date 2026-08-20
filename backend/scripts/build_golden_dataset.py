"""Build the structured agent golden dataset from the review-friendly CSV."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = PROJECT_ROOT / "eval" / "data"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "eval" / "golden"
JSON_COLUMNS: dict[str, type] = {
    "turns_json": list,
    "ui_context_json": dict,
    "expected_arguments_json": dict,
    "expected_db_assertions_json": list,
    "response_must_contain_json": list,
    "forbidden_json": list,
    "tags_json": list,
}
TOOL_ALIASES = {"verify_booking_access_otp": "verify_booking_access"}
ACTIVE_AGENT_TOOLS = {
    "confirm_test_drive_booking",
    "get_booking_details",
    "get_booking_draft",
    "hold_test_drive_slot",
    "request_booking_access",
    "search_knowledge",
    "search_test_drive_options",
    "update_booking_draft",
    "verify_booking_access",
}
KNOWN_GAPS = {
    "cancel_booking": "Booking cancellation exists in the service/API but is not exposed as an agent tool.",
    "reschedule_booking": "Booking rescheduling is not exposed as an agent tool.",
}


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description="Build the tracked eval/golden JSON datasets.")
    command.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    command.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    command.add_argument("--check", action="store_true", help="Fail if either generated JSON file is not current.")
    return command


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _parse_json(case_id: str, column: str, value: str, expected_type: type) -> Any:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as error:
        raise SystemExit(f"{case_id}: invalid {column}: {error}") from error
    if not isinstance(parsed, expected_type):
        raise SystemExit(f"{case_id}: {column} must contain a JSON {expected_type.__name__}")
    return parsed


def _current_showroom_id(public_source_id: str) -> str:
    match = re.fullmatch(r"VFVN_(\d+)", public_source_id.strip())
    if not match:
        raise SystemExit(f"Invalid public showroom id: {public_source_id!r}")
    return str(int(match.group(1)))


def _showroom_context(data_dir: Path) -> tuple[dict[str, str], dict[str, str], set[str]]:
    hanoi_rows = _read_csv(data_dir / "reference" / "showrooms_hanoi_demo_47.csv")
    hanoi_mapping = {row["id"]: _current_showroom_id(row["public_source_id"]) for row in hanoi_rows}
    hanoi_names = {row["id"]: row["name"] for row in hanoi_rows}
    active_showroom_ids = {
        row["id"] for row in _read_csv(data_dir / "seed" / "04_showrooms.csv") if row["is_active"] == "1"
    }
    return hanoi_mapping, hanoi_names, active_showroom_ids


def _replace_showroom_ids(value: Any, mapping: dict[str, str]) -> Any:
    if isinstance(value, dict):
        return {
            key: mapping.get(item, item) if key == "showroom_id" and isinstance(item, str) else _replace_showroom_ids(item, mapping)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_replace_showroom_ids(item, mapping) for item in value]
    return value


def _replace_showroom_aliases(value: Any, names: dict[str, str]) -> Any:
    if isinstance(value, dict):
        return {key: _replace_showroom_aliases(item, names) for key, item in value.items()}
    if isinstance(value, list):
        return [_replace_showroom_aliases(item, names) for item in value]
    if isinstance(value, str):
        return re.sub(r"\bHN\d{3}\b", lambda match: names.get(match.group(0), match.group(0)), value)
    return value


def _normalize_arguments(tool: str | None, arguments: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(arguments)
    if tool == "verify_booking_access" and "otp" in normalized:
        normalized["otp_code"] = normalized.pop("otp")
    return normalized


def _validate_case(case: dict[str, Any], active_showroom_ids: set[str]) -> None:
    case_id = case["case_id"]
    turns = case["turns"]
    if not turns:
        raise SystemExit(f"{case_id}: at least one conversation turn is required")
    for turn in turns:
        if not isinstance(turn, dict) or turn.get("role") not in {"user", "assistant"} or not turn.get("content"):
            raise SystemExit(f"{case_id}: invalid conversation turn: {turn!r}")

    expected = case["expected"]
    if not expected["intent"] or not expected["skill"]:
        raise SystemExit(f"{case_id}: expected intent and skill are required")
    if expected["tool"] is None and expected["intent"] != "guardrail":
        raise SystemExit(f"{case_id}: only guardrail cases may omit the expected tool")
    if case["evaluation_status"] == "active" and expected["tool"] not in ACTIVE_AGENT_TOOLS | {None}:
        raise SystemExit(f"{case_id}: active case references unavailable tool {expected['tool']!r}")
    if case["evaluation_status"] == "known_gap" and expected["tool"] not in KNOWN_GAPS:
        raise SystemExit(f"{case_id}: known gap has no explanation for tool {expected['tool']!r}")
    showroom_id = expected["arguments"].get("showroom_id")
    if showroom_id and showroom_id not in active_showroom_ids:
        raise SystemExit(f"{case_id}: showroom {showroom_id!r} is not active in the PostgreSQL baseline")


def build(data_dir: Path) -> dict[str, Any]:
    fixtures_dir = data_dir / "fixtures"
    source_rows = _read_csv(fixtures_dir / "golden_agent_cases.csv")
    if not source_rows:
        raise SystemExit("Golden dataset source CSV is empty")
    hanoi_mapping, hanoi_names, active_showroom_ids = _showroom_context(data_dir)
    seen: set[str] = set()
    cases: list[dict[str, Any]] = []
    case_by_semantics: dict[str, dict[str, Any]] = {}

    for row in source_rows:
        case_id = row["case_id"].strip()
        if not case_id or case_id in seen:
            raise SystemExit(f"Golden case id is empty or duplicated: {case_id!r}")
        seen.add(case_id)
        parsed = {
            column: _parse_json(case_id, column, row[column], expected_type)
            for column, expected_type in JSON_COLUMNS.items()
        }
        tool = TOOL_ALIASES.get(row["expected_tool"].strip(), row["expected_tool"].strip()) or None
        arguments = _normalize_arguments(
            tool,
            _replace_showroom_ids(parsed["expected_arguments_json"], hanoi_mapping),
        )
        evaluation_status = "known_gap" if tool in KNOWN_GAPS else "active"
        case = {
            "case_id": case_id,
            "source_case_ids": [case_id],
            "turns": _replace_showroom_aliases(parsed["turns_json"], hanoi_names),
            "ui_context": parsed["ui_context_json"],
            "expected": {
                "intent": row["expected_intent"].strip(),
                "skill": row["expected_skill"].strip(),
                "tool": tool,
                "arguments": arguments,
                "database_assertions": parsed["expected_db_assertions_json"],
                "response": {
                    "must_contain": parsed["response_must_contain_json"],
                    "forbidden_behaviors": parsed["forbidden_json"],
                },
            },
            "tags": parsed["tags_json"],
            "review_status": row["review_status"].strip(),
            "evaluation_status": evaluation_status,
            "known_gap": KNOWN_GAPS.get(tool),
        }
        _validate_case(case, active_showroom_ids)
        semantic_value = {key: value for key, value in case.items() if key not in {"case_id", "source_case_ids"}}
        semantic_key = json.dumps(semantic_value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        if semantic_key in case_by_semantics:
            case_by_semantics[semantic_key]["source_case_ids"].append(case_id)
        else:
            case_by_semantics[semantic_key] = case
            cases.append(case)

    metadata = json.loads((data_dir / "GENERATION_METADATA.json").read_text(encoding="utf-8"))
    review_summary = Counter(case["review_status"] for case in cases)
    evaluation_summary = Counter(case["evaluation_status"] for case in cases)
    return {
        "schema_version": "1.0",
        "dataset_name": "vinfast_booking_agent_golden",
        "dataset_version": metadata["dataset_version"],
        "language": "vi-VN",
        "case_count": len(cases),
        "source_case_count": len(source_rows),
        "deduplicated_source_case_count": len(source_rows) - len(cases),
        "review_status_summary": dict(sorted(review_summary.items())),
        "evaluation_status_summary": dict(sorted(evaluation_summary.items())),
        "human_review_required": any("NOT_HUMAN_REVIEWED" in case["review_status"] for case in cases),
        "baseline": {
            "source_of_truth": metadata["source_of_truth"],
            "showroom_count": metadata["showroom_count"],
            "active_staff_count": metadata["active_staff_count"],
            "booking_count": metadata["booking_count"],
        },
        "provenance": {
            "source_file": "eval/data/fixtures/golden_agent_cases.csv",
            "showroom_aliases": "eval/data/reference/showrooms_hanoi_demo_47.csv",
            "note": "Semantic duplicates are collapsed and retained in source_case_ids; this is not operational seed data.",
        },
        "cases": cases,
    }


def build_negative_cases(data_dir: Path) -> dict[str, Any]:
    source_rows = _read_csv(data_dir / "fixtures" / "negative_cases.csv")
    case_ids = [row["case_id"].strip() for row in source_rows]
    if not source_rows or any(not case_id for case_id in case_ids) or len(case_ids) != len(set(case_ids)):
        raise SystemExit("Negative case ids must be present and unique")
    return {
        "schema_version": "1.0",
        "dataset_name": "vinfast_booking_negative_cases",
        "case_count": len(source_rows),
        "human_review_required": True,
        "provenance": {
            "source_file": "eval/data/fixtures/negative_cases.csv",
            "note": "Security and consistency regression cases; not operational seed data.",
        },
        "cases": [
            {
                "case_id": row["case_id"].strip(),
                "scenario": row["case"].strip(),
                "expected_outcome": row["expected"].strip(),
                "review_status": "MIGRATED_WITHOUT_REVIEW_STATUS",
            }
            for row in source_rows
        ],
    }


def main() -> int:
    args = parser().parse_args()
    data_dir = args.data_dir.resolve()
    output_dir = args.output_dir.resolve()
    rendered_files = {
        output_dir / "agent_cases.json": json.dumps(build(data_dir), ensure_ascii=False, indent=2) + "\n",
        output_dir / "negative_cases.json": json.dumps(build_negative_cases(data_dir), ensure_ascii=False, indent=2)
        + "\n",
    }
    if args.check:
        stale = [
            str(path)
            for path, rendered in rendered_files.items()
            if not path.is_file() or path.read_text(encoding="utf-8") != rendered
        ]
        if stale:
            raise SystemExit(f"Golden JSON is missing or stale: {', '.join(stale)}")
        print(f"Golden JSON files are current: {output_dir}")
        return 0
    output_dir.mkdir(parents=True, exist_ok=True)
    for path, rendered in rendered_files.items():
        path.write_text(rendered, encoding="utf-8")
        print(f"Built {path} with {len(json.loads(rendered)['cases'])} cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
