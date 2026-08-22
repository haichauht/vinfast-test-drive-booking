import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GOLDEN_ROOT = PROJECT_ROOT / "eval" / "golden"


def _read(name: str) -> dict:
    return json.loads((GOLDEN_ROOT / name).read_text(encoding="utf-8"))


def test_agent_golden_dataset_is_structured_and_deduplicated():
    dataset = _read("agent_cases.json")
    cases = dataset["cases"]

    assert dataset["schema_version"] == "1.0"
    assert dataset["case_count"] == len(cases) == 39
    assert dataset["source_case_count"] == 124
    assert dataset["deduplicated_source_case_count"] == 85
    assert dataset["evaluation_status_summary"] == {"active": 37, "known_gap": 2}
    assert len({case["case_id"] for case in cases}) == len(cases)
    assert not any(
        str(case["expected"]["arguments"].get("showroom_id", "")).startswith("HN") for case in cases
    )
    assert not any(case["expected"]["tool"] == "verify_booking_access_otp" for case in cases)


def test_known_gaps_are_explicit_and_negative_cases_are_unique():
    agent_cases = _read("agent_cases.json")["cases"]
    known_gaps = [case for case in agent_cases if case["evaluation_status"] == "known_gap"]
    negative = _read("negative_cases.json")

    assert {case["expected"]["tool"] for case in known_gaps} == {"cancel_booking", "reschedule_booking"}
    assert all(case["known_gap"] for case in known_gaps)
    assert negative["case_count"] == len(negative["cases"]) == 12
    assert len({case["case_id"] for case in negative["cases"]}) == 12


def test_readme_indexes_every_case_and_states_evaluation_limits():
    agent = _read("agent_cases.json")
    negative = _read("negative_cases.json")
    readme = (GOLDEN_ROOT / "README.md").read_text(encoding="utf-8")

    for case in [*agent["cases"], *negative["cases"]]:
        assert f"`{case['case_id']}`" in readme
    assert "behavioral golden evaluation chưa chạy" in readme
    assert "KNOWN_GAP" in readme
    assert "Human review" in readme
