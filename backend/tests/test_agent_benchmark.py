from __future__ import annotations

import csv
import json
import sqlite3
from copy import deepcopy

from src.evaluation.agent_benchmark import (
    DEFAULT_GOLDEN_PATH,
    DEFAULT_NEGATIVE_PATH,
    _backup_sqlite_database,
    load_golden_dataset,
    render_markdown,
    score_evaluation,
)


def _small_dataset(tmp_path):
    dataset = deepcopy(load_golden_dataset(DEFAULT_GOLDEN_PATH))
    dataset["cases"] = [
        next(case for case in dataset["cases"] if case["case_id"] == "SEARCH-001"),
        next(case for case in dataset["cases"] if case["case_id"] == "INJECTION-001"),
    ]
    dataset["case_count"] = len(dataset["cases"])
    path = tmp_path / "golden.json"
    path.write_text(json.dumps(dataset, ensure_ascii=False), encoding="utf-8")
    return dataset, path


def test_score_evaluation_reports_behavioral_and_operational_metrics(tmp_path):
    dataset, path = _small_dataset(tmp_path)
    predictions = {
        "cases": [
            {
                "case_id": "SEARCH-001",
                "intent": "search_options",
                "skill": "booking",
                "tool_calls": [
                    {
                        "name": "search_test_drive_options",
                        "arguments": {"vehicle_model": "VF 3", "showroom_id": "117"},
                    }
                ],
                "response": "Còn lịch tại VinFast Thăng Long Trịnh Văn Bô.",
                "forbidden_behavior_checks": {"invent_showroom": False, "invent_distance": False},
                "latency_ms": 100,
                "token_usage": {"input_tokens": 80, "output_tokens": 20, "total_tokens": 100},
                "groundedness_score": 0.9,
                "hallucination_detected": False,
            },
            {
                "case_id": "INJECTION-001",
                "intent": "advise",
                "skill": "advise",
                "tool_calls": [],
                "response": "Tôi không thể làm việc đó.",
                "forbidden_behavior_checks": {
                    "reveal_token": False,
                    "direct_db_mutation": False,
                    "bypass_tool_allowlist": False,
                },
                "latency_ms": 300,
                "token_usage": {"input_tokens": 40, "output_tokens": 10, "total_tokens": 50},
            },
        ]
    }

    report = score_evaluation(
        dataset,
        predictions,
        dataset_path=path,
        negative_dataset={"cases": []},
        input_cost_per_million=1.0,
        output_cost_per_million=2.0,
    )

    assert report["quality"]["task_success_rate"] == 0.5
    assert report["quality"]["intent_accuracy"] == 0.5
    assert report["quality"]["tool_accuracy"] == 1.0
    assert report["quality"]["argument_required_match_rate"] == 1.0
    assert report["quality"]["forbidden_behavior_violation_rate"] == 0.0
    assert report["quality"]["mean_groundedness"] == 0.9
    assert report["quality"]["hallucination_rate"] == 0.0
    assert report["performance"]["latency_p50_ms"] == 200.0
    assert report["performance"]["latency_p95_ms"] == 290.0
    assert report["usage"]["total_tokens"] == 150
    assert report["usage"]["estimated_cost"] == 0.00018
    assert report["run"]["status"] == "COMPLETE"


def test_missing_predictions_and_reviews_remain_not_run(tmp_path):
    dataset, path = _small_dataset(tmp_path)

    report = score_evaluation(
        dataset,
        dataset_path=path,
        negative_dataset=json.loads(DEFAULT_NEGATIVE_PATH.read_text(encoding="utf-8")),
    )

    assert report["run"]["status"] == "NOT_RUN"
    assert report["quality"]["task_success_rate"] is None
    assert report["performance"]["error_rate"] is None
    assert report["negative_security"]["accuracy"] is None
    assert report["human"]["mean_satisfaction_1_5"] is None
    assert "NOT_RUN" in render_markdown(report)


def test_partial_database_assertions_do_not_claim_a_pass(tmp_path):
    dataset = deepcopy(load_golden_dataset(DEFAULT_GOLDEN_PATH))
    hold = next(case for case in dataset["cases"] if case["case_id"] == "HOLD-001")
    dataset["cases"] = [hold]
    dataset["case_count"] = 1
    path = tmp_path / "hold.json"
    path.write_text(json.dumps(dataset, ensure_ascii=False), encoding="utf-8")
    predictions = {
        "cases": [
            {
                "case_id": "HOLD-001",
                "intent": "hold_slot",
                "skill": "booking",
                "tool": "hold_test_drive_slot",
                "arguments": {"vehicle_model": "VF 3"},
                "database_assertions": [{"passed": True}],
                "forbidden_behavior_checks": {"confirm_without_details": False},
            }
        ]
    }

    report = score_evaluation(dataset, predictions, dataset_path=path, negative_dataset={"cases": []})

    database = report["cases"][0]["checks"]["database"]
    assert database == {"passed_all": None, "passed": 1, "total": 2, "graded": 1}
    assert report["cases"][0]["run_status"] == "ungraded"
    assert report["cases"][0]["task_success"] is None
    assert report["quality"]["database_assertion_pass_rate"] is None


def test_human_ratings_and_negative_outcomes_are_aggregated(tmp_path):
    dataset, path = _small_dataset(tmp_path)
    ratings = tmp_path / "ratings.csv"
    with ratings.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "case_id",
                "reviewer_id",
                "task_success",
                "correctness_1_5",
                "relevance_1_5",
                "groundedness_1_5",
                "safety_1_5",
                "satisfaction_1_5",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "case_id": "SEARCH-001",
                "reviewer_id": "r1",
                "task_success": 1,
                "correctness_1_5": 5,
                "relevance_1_5": 4,
                "groundedness_1_5": 4,
                "safety_1_5": 5,
                "satisfaction_1_5": 5,
            }
        )
        writer.writerow(
            {
                "case_id": "INJECTION-001",
                "reviewer_id": "r1",
                "task_success": 0,
                "correctness_1_5": 3,
                "relevance_1_5": 3,
                "groundedness_1_5": 3,
                "safety_1_5": 4,
                "satisfaction_1_5": 3,
            }
        )
    negative = {"cases": [{"case_id": "NEG-001", "expected_outcome": "DENY"}]}
    predictions = {"negative_cases": [{"case_id": "NEG-001", "outcome": "DENY"}]}

    report = score_evaluation(
        dataset,
        predictions,
        dataset_path=path,
        negative_dataset=negative,
        human_ratings_path=ratings,
    )

    assert report["human"]["status"] == "COMPLETE"
    assert report["human"]["task_success_rate"] == 0.5
    assert report["human"]["mean_satisfaction_1_5"] == 4.0
    assert report["human"]["csat_4_or_5_rate"] == 0.5
    assert report["negative_security"]["accuracy"] == 1.0


def test_live_runner_sqlite_backup_is_isolated(tmp_path):
    source = tmp_path / "source.db"
    destination = tmp_path / "destination.db"
    with sqlite3.connect(source) as connection:
        connection.execute("CREATE TABLE evidence(value TEXT NOT NULL)")
        connection.execute("INSERT INTO evidence VALUES('original')")

    _backup_sqlite_database(source, destination)
    with sqlite3.connect(destination) as connection:
        connection.execute("UPDATE evidence SET value='isolated'")
        connection.commit()
    with sqlite3.connect(source) as connection:
        assert connection.execute("SELECT value FROM evidence").fetchone()[0] == "original"
