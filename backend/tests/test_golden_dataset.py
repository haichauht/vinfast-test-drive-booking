import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GOLDEN_ROOT = PROJECT_ROOT / "eval" / "golden"


def _read(name: str) -> dict:
    return json.loads((GOLDEN_ROOT / name).read_text(encoding="utf-8"))


def test_agent_golden_dataset_is_structured_and_deduplicated():
    dataset = _read("agent_cases.json")
    cases = dataset["cases"]

    assert dataset["schema_version"] == "1.2"
    assert dataset["case_count"] == len(cases) == 57
    assert dataset["source_case_count"] == 129
    assert dataset["excluded_source_case_count"] == 10
    assert dataset["deduplicated_source_case_count"] == 81
    assert dataset["generated_booking_funnel_case_count"] == 9
    assert dataset["evaluation_status_summary"] == {"active": 57}
    assert dataset["challenge_case_count"] == 12
    assert len({case["case_id"] for case in cases}) == len(cases)
    assert not any(str(case["expected"]["arguments"].get("showroom_id", "")).startswith("HN") for case in cases)
    assert not any(case["expected"]["tool"] == "verify_booking_access_otp" for case in cases)


def test_all_declared_agent_cases_are_active_and_negative_cases_are_unique():
    agent_cases = _read("agent_cases.json")["cases"]
    known_gaps = [case for case in agent_cases if case["evaluation_status"] == "known_gap"]
    negative = _read("negative_cases.json")

    assert known_gaps == []
    assert all(case["evaluation_status"] == "active" for case in agent_cases)
    assert negative["case_count"] == len(negative["cases"]) == 16
    assert len({case["case_id"] for case in negative["cases"]}) == 16
    assert negative["schema_version"] == "1.1"
    assert all(case["fixture_nodeid"] for case in negative["cases"])
    assert all(case["metric_groups"] for case in negative["cases"])
    assert all(case["review_status"] == "AUTOMATED_REGRESSION_NOT_HUMAN_REVIEWED" for case in negative["cases"])


def test_stateful_cases_declare_executable_setup_and_workflow_turns():
    cases = {case["case_id"]: case for case in _read("agent_cases.json")["cases"]}

    hold = cases["HOLD-001"]
    assert hold["evaluation_setup"]["kind"] == "available_slot"
    assert hold["expected"]["arguments"] == {"slot_id": "{{eval.slot_id}}"}
    assert hold["expected"]["allowed_extra_arguments"] == ["ui_action_id"]
    assert "{{eval.slot_time}}" in hold["turns"][0]["content"]

    search = cases["SEARCH-001"]
    assert search["expected"]["allowed_extra_arguments"] == [
        "address",
        "showroom_limit",
        "slot_limit",
    ]

    confirm_roles = [turn["role"] for turn in cases["CONFIRM-001"]["turns"]]
    expired_roles = [turn["role"] for turn in cases["HOLD_EXPIRED-001"]["turns"]]
    assert confirm_roles == ["action", "action", "action"]
    assert expired_roles == ["action", "fixture", "action"]
    assert cases["OTP_BAD-001"]["turns"][-1]["payload"]["otp_code"] == "{{invalid_mock_otp}}"
    assert [turn["role"] for turn in cases["CONFLICT-001"]["turns"]] == ["fixture", "action"]
    assert cases["CONFLICT-001"]["expected"]["database_assertions"] == [{"expect_error": "SLOT_NO_LONGER_AVAILABLE"}]
    assert cases["CANCEL-001"]["evaluation_setup"]["kind"] == "confirmed_booking"
    assert cases["RESCHEDULE-001"]["evaluation_setup"]["kind"] == "confirmed_booking_reschedule"
    assert cases["STAFF-CAPACITY-001"]["expected"]["database_assertions"] == [
        {"assertion": "offered_slots_within_staff_capacity"}
    ]


def test_groundedness_coverage_uses_active_tool_evidence_cases():
    cases = _read("agent_cases.json")["cases"]
    groundedness_cases = {
        case["case_id"] for case in cases if case["evaluation_status"] == "active" and "groundedness" in case["tags"]
    }

    assert groundedness_cases == {
        *(f"SEARCH-{index:03d}" for index in range(1, 11)),
        "ACCESS-DETAILS-MULTITURN-001",
        "HARD-BENIGN-QUOTE-001",
        "HARD-BENIGN-NEGATION-001",
        "HARD-SEARCH-TYPO-001",
        "HARD-SEARCH-CORRECTION-001",
        "HARD-SEARCH-DATETIME-001",
        "HARD-SEARCH-CODE-SWITCH-001",
        "HARD-MULTITURN-CORRECTION-001",
        "HARD-SHOWROOM-NOTFOUND-001",
    }


def test_readme_indexes_every_case_and_states_evaluation_limits():
    agent = _read("agent_cases.json")
    negative = _read("negative_cases.json")
    readme = (GOLDEN_ROOT / "README.md").read_text(encoding="utf-8")

    for case in [*agent["cases"], *negative["cases"]]:
        assert f"`{case['case_id']}`" in readme
    assert "public booking scope" in readme
    assert "challenge" in readme
    assert "57 active case" in readme
    assert "Human review" in readme
