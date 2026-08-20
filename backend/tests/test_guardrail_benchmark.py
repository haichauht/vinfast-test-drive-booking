import json
from copy import deepcopy

import pytest
from src.evaluation.guardrail_benchmark import (
    DEFAULT_DATASET_PATH,
    load_dataset,
    render_markdown,
    run_benchmark,
)


def test_guardrail_benchmark_dataset_is_valid_unique_and_balanced():
    dataset = load_dataset(DEFAULT_DATASET_PATH)
    cases = dataset["cases"]

    assert dataset["case_count"] == len(cases) == 52
    assert len({case["case_id"] for case in cases}) == len(cases)
    assert {case["kind"] for case in cases} == {"input", "output", "tool"}
    assert sum(case["kind"] == "input" for case in cases) >= 25
    assert sum(case["kind"] == "output" for case in cases) >= 10
    assert sum(case["kind"] == "tool" for case in cases) >= 10
    assert any("false-positive" in case.get("tags", []) for case in cases)
    assert any("negation" in case.get("tags", []) for case in cases)


def test_every_guardrail_benchmark_case_passes_as_a_ci_regression_gate():
    report = run_benchmark(load_dataset(DEFAULT_DATASET_PATH))

    assert report["summary"]["total"] == 52
    assert report["summary"]["failed"] == 0
    assert report["summary"]["pass_rate"] == 1.0
    assert report["quality_metrics"]["attack_block_accuracy"] == 1.0
    assert report["quality_metrics"]["benign_allow_accuracy"] == 1.0
    assert report["quality_metrics"]["output_protection_accuracy"] == 1.0


def test_benchmark_filters_are_deterministic_and_report_is_reviewable():
    dataset = load_dataset(DEFAULT_DATASET_PATH)
    report = run_benchmark(dataset, kinds={"tool"}, tags={"confirmation"})
    markdown = render_markdown(report)

    assert report["summary"]["total"] == 5
    assert report["summary"]["failed"] == 0
    assert set(report["case_distribution"]) == {"tool"}
    assert "# Guardrail Benchmark Report" in markdown
    assert "No failed cases." in markdown
    assert "deterministic, offline policy benchmark" in markdown


def test_benchmark_pins_test_settings_instead_of_inheriting_production_env(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("GUARDRAILS_ENABLED", "false")
    dataset = load_dataset(DEFAULT_DATASET_PATH)

    report = run_benchmark(dataset, categories={"prompt_injection"})

    assert report["summary"]["total"] == 2
    assert report["summary"]["failed"] == 0


def test_benchmark_dataset_validation_rejects_duplicate_ids(tmp_path):
    dataset = deepcopy(load_dataset(DEFAULT_DATASET_PATH))
    dataset["cases"][1]["case_id"] = dataset["cases"][0]["case_id"]
    path = tmp_path / "duplicate.json"
    path.write_text(json.dumps(dataset, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(ValueError, match="Duplicate benchmark case_id"):
        load_dataset(path)
