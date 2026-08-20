from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import statistics
import sys
import time
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from langchain_core.messages import AIMessage

from src.config import Settings
from src.guardrails.pipeline import Guardrails
from src.guardrails.tool_guard import inspect_tool_calls

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATASET_PATH = PROJECT_ROOT / "eval" / "benchmarks" / "guardrails_cases.json"
SUPPORTED_KINDS = frozenset({"input", "output", "tool"})
BENCHMARK_SETTING_DEFAULTS: dict[str, Any] = {
    "app_env": "test",
    "guardrails_enabled": True,
    "guardrails_max_payload_bytes": 16_384,
    "guardrails_max_payload_depth": 6,
    "guardrails_max_payload_nodes": 256,
    "guardrails_max_payload_string_chars": 5_000,
    "guardrails_max_tool_calls_per_message": 3,
    "guardrails_max_output_chars": 8_000,
}


@dataclass(frozen=True, slots=True)
class CaseResult:
    case_id: str
    kind: str
    category: str
    passed: bool
    duration_ms: float
    expected: dict[str, Any]
    actual: dict[str, Any]
    failures: list[str]
    tags: list[str]


def load_dataset(path: Path = DEFAULT_DATASET_PATH) -> dict[str, Any]:
    """Load and strictly validate the version-controlled benchmark dataset."""
    try:
        dataset = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Benchmark dataset does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Benchmark dataset is not valid JSON: {exc}") from exc

    if not isinstance(dataset, dict):
        raise ValueError("Benchmark dataset root must be an object")
    if dataset.get("schema_version") != "1.0":
        raise ValueError("Unsupported benchmark schema_version")
    cases = dataset.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("Benchmark dataset must contain a non-empty cases list")
    if dataset.get("case_count") != len(cases):
        raise ValueError("case_count does not match the number of cases")

    seen: set[str] = set()
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            raise ValueError(f"Case at index {index} must be an object")
        case_id = case.get("case_id")
        if not isinstance(case_id, str) or not case_id:
            raise ValueError(f"Case at index {index} has an invalid case_id")
        if case_id in seen:
            raise ValueError(f"Duplicate benchmark case_id: {case_id}")
        seen.add(case_id)
        if case.get("kind") not in SUPPORTED_KINDS:
            raise ValueError(f"{case_id}: kind must be one of {sorted(SUPPORTED_KINDS)}")
        if not isinstance(case.get("category"), str) or not case["category"]:
            raise ValueError(f"{case_id}: category must be a non-empty string")
        if not isinstance(case.get("input"), dict):
            raise ValueError(f"{case_id}: input must be an object")
        if not isinstance(case.get("expected"), dict):
            raise ValueError(f"{case_id}: expected must be an object")
        tags = case.get("tags", [])
        if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
            raise ValueError(f"{case_id}: tags must be a string list")
        if case["kind"] in {"input", "tool"}:
            if not isinstance(case["expected"].get("allowed"), bool):
                raise ValueError(f"{case_id}: decision cases require expected.allowed")
            if not isinstance(case["expected"].get("code"), str):
                raise ValueError(f"{case_id}: decision cases require expected.code")
    return dataset


def _settings(case: Mapping[str, Any]) -> Settings:
    overrides = case.get("settings", {})
    if not isinstance(overrides, Mapping):
        raise ValueError(f"{case.get('case_id')}: settings must be an object")
    values = {**BENCHMARK_SETTING_DEFAULTS, **dict(overrides)}
    return Settings(_env_file=None, **values)


def _run_input_case(case: Mapping[str, Any]) -> dict[str, Any]:
    case_input = case["input"]
    guardrails = Guardrails(_settings(case))
    decision = guardrails.inspect_input(
        message=str(case_input.get("message", "Tôi muốn xem thông tin VF8")),
        conversation_id=str(case_input.get("conversation_id", "benchmark-conversation")),
        context=dict(case_input.get("context", {})),
        action=case_input.get("action"),
        action_payload=dict(case_input.get("action_payload", {})),
    )
    return asdict(decision)


def _run_output_case(case: Mapping[str, Any]) -> dict[str, Any]:
    case_input = case["input"]
    guardrails = Guardrails(_settings(case))
    result = case_input.get("result", {})
    if not isinstance(result, dict):
        raise ValueError(f"{case.get('case_id')}: output result must be an object")
    return asdict(guardrails.protect_output(result))


def _run_tool_case(case: Mapping[str, Any]) -> dict[str, Any]:
    case_input = case["input"]
    calls = case_input.get("calls")
    messages: list[AIMessage] = []
    if calls is not None:
        if not isinstance(calls, list):
            raise ValueError(f"{case.get('case_id')}: calls must be a list or null")
        messages = [AIMessage(content="", tool_calls=calls)]
    state: dict[str, Any] = {
        "messages": messages,
        "query": str(case_input.get("query", "Tìm thông tin VF8")),
    }
    if "requested_action" in case_input:
        state["requested_action"] = case_input["requested_action"]
    allowed_tool_names = case_input.get("allowed_tool_names", [])
    if not isinstance(allowed_tool_names, list):
        raise ValueError(f"{case.get('case_id')}: allowed_tool_names must be a list")
    decision = inspect_tool_calls(
        state,
        allowed_tool_names=allowed_tool_names,
        settings=_settings(case),
    )
    return asdict(decision)


def _read_path(value: Any, path: str) -> Any:
    current = value
    for segment in path.split("."):
        if isinstance(current, Mapping):
            if segment not in current:
                raise KeyError(path)
            current = current[segment]
        elif isinstance(current, Sequence) and not isinstance(current, (str, bytes, bytearray)):
            current = current[int(segment)]
        else:
            raise KeyError(path)
    return current


def _evaluate_expected(actual: Mapping[str, Any], expected: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    for field in ("allowed", "code"):
        if field in expected and actual.get(field) != expected[field]:
            failures.append(f"{field}: expected {expected[field]!r}, got {actual.get(field)!r}")

    for path, expected_value in expected.get("equals", {}).items():
        try:
            actual_value = _read_path(actual, path)
        except (KeyError, IndexError, ValueError):
            failures.append(f"{path}: field is missing")
            continue
        if actual_value != expected_value:
            failures.append(f"{path}: expected {expected_value!r}, got {actual_value!r}")

    for operation in ("contains", "not_contains", "ends_with"):
        for path, expectation in expected.get(operation, {}).items():
            try:
                actual_value = str(_read_path(actual, path))
            except (KeyError, IndexError, ValueError):
                failures.append(f"{path}: field is missing")
                continue
            values = expectation if isinstance(expectation, list) else [expectation]
            for item in map(str, values):
                if operation == "contains" and item not in actual_value:
                    failures.append(f"{path}: expected to contain {item!r}")
                elif operation == "not_contains" and item in actual_value:
                    failures.append(f"{path}: must not contain {item!r}")
                elif operation == "ends_with" and not actual_value.endswith(item):
                    failures.append(f"{path}: expected to end with {item!r}")
    return failures


def run_case(case: Mapping[str, Any]) -> CaseResult:
    started = time.perf_counter_ns()
    failures: list[str] = []
    actual: dict[str, Any]
    try:
        kind = str(case["kind"])
        if kind == "input":
            actual = _run_input_case(case)
        elif kind == "output":
            actual = _run_output_case(case)
        elif kind == "tool":
            actual = _run_tool_case(case)
        else:  # load_dataset prevents this; retain a fail-closed runtime guard.
            raise ValueError(f"Unsupported case kind: {kind}")
        failures.extend(_evaluate_expected(actual, case["expected"]))
    except Exception as exc:
        actual = {"exception": f"{type(exc).__name__}: {exc}"}
        failures.append(actual["exception"])
    duration_ms = (time.perf_counter_ns() - started) / 1_000_000
    return CaseResult(
        case_id=str(case["case_id"]),
        kind=str(case["kind"]),
        category=str(case["category"]),
        passed=not failures,
        duration_ms=round(duration_ms, 4),
        expected=dict(case["expected"]),
        actual=actual,
        failures=failures,
        tags=list(case.get("tags", [])),
    )


def _rate(passed: int, total: int) -> float | None:
    return round(passed / total, 6) if total else None


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, math.ceil(percentile * len(ordered)) - 1)
    return round(ordered[index], 4)


def _group_summary(results: list[CaseResult], attribute: str) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[CaseResult]] = defaultdict(list)
    for result in results:
        grouped[str(getattr(result, attribute))].append(result)
    return {
        key: {
            "total": len(items),
            "passed": sum(item.passed for item in items),
            "failed": sum(not item.passed for item in items),
            "pass_rate": _rate(sum(item.passed for item in items), len(items)),
        }
        for key, items in sorted(grouped.items())
    }


def run_benchmark(
    dataset: Mapping[str, Any],
    *,
    kinds: set[str] | None = None,
    categories: set[str] | None = None,
    tags: set[str] | None = None,
) -> dict[str, Any]:
    """Execute selected deterministic cases and return a machine-readable report."""
    selected: list[dict[str, Any]] = []
    for case in dataset["cases"]:
        if kinds and case["kind"] not in kinds:
            continue
        if categories and case["category"] not in categories:
            continue
        case_tags = set(case.get("tags", []))
        if tags and not tags.issubset(case_tags):
            continue
        selected.append(case)
    if not selected:
        raise ValueError("No benchmark cases matched the requested filters")

    started = time.perf_counter()
    results = [run_case(case) for case in selected]
    elapsed_ms = round((time.perf_counter() - started) * 1000, 4)
    passed = sum(result.passed for result in results)
    attack_results = [
        result
        for result in results
        if result.kind in {"input", "tool"} and result.expected.get("allowed") is False
    ]
    benign_results = [
        result
        for result in results
        if result.kind in {"input", "tool"} and result.expected.get("allowed") is True
    ]
    output_results = [result for result in results if result.kind == "output"]
    durations = [result.duration_ms for result in results]
    dataset_bytes = json.dumps(dataset, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()

    return {
        "schema_version": "1.0",
        "benchmark_name": dataset.get("benchmark_name", "guardrails"),
        "dataset_schema_version": dataset.get("schema_version"),
        "dataset_sha256": hashlib.sha256(dataset_bytes).hexdigest(),
        "generated_at": datetime.now(UTC).isoformat(),
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "filters": {
            "kinds": sorted(kinds or []),
            "categories": sorted(categories or []),
            "tags": sorted(tags or []),
        },
        "summary": {
            "total": len(results),
            "passed": passed,
            "failed": len(results) - passed,
            "pass_rate": _rate(passed, len(results)),
            "elapsed_ms": elapsed_ms,
        },
        "quality_metrics": {
            "attack_block_accuracy": _rate(sum(item.passed for item in attack_results), len(attack_results)),
            "benign_allow_accuracy": _rate(sum(item.passed for item in benign_results), len(benign_results)),
            "output_protection_accuracy": _rate(sum(item.passed for item in output_results), len(output_results)),
            "latency_median_ms": round(statistics.median(durations), 4),
            "latency_p95_ms": _percentile(durations, 0.95),
        },
        "case_distribution": dict(sorted(Counter(result.kind for result in results).items())),
        "by_kind": _group_summary(results, "kind"),
        "by_category": _group_summary(results, "category"),
        "cases": [asdict(result) for result in results],
    }


def render_markdown(report: Mapping[str, Any]) -> str:
    summary = report["summary"]
    metrics = report["quality_metrics"]
    lines = [
        "# Guardrail Benchmark Report",
        "",
        f"- Generated: `{report['generated_at']}`",
        f"- Dataset SHA-256: `{report['dataset_sha256']}`",
        f"- Result: **{summary['passed']}/{summary['total']} PASS** ({summary['pass_rate']:.2%})",
        f"- Runtime: `{summary['elapsed_ms']:.4f} ms`",
        "",
        "## Quality Metrics",
        "",
        "| Metric | Value |",
        "|---|---:|",
    ]
    for label, key in (
        ("Attack-block accuracy", "attack_block_accuracy"),
        ("Benign-allow accuracy", "benign_allow_accuracy"),
        ("Output-protection accuracy", "output_protection_accuracy"),
    ):
        value = metrics[key]
        lines.append(f"| {label} | {'N/A' if value is None else f'{value:.2%}'} |")
    lines.extend(
        [
            f"| Median latency | {metrics['latency_median_ms']:.4f} ms |",
            f"| p95 latency | {metrics['latency_p95_ms']:.4f} ms |",
            "",
            "## Results By Category",
            "",
            "| Category | Passed | Total | Pass rate |",
            "|---|---:|---:|---:|",
        ]
    )
    for category, category_summary in report["by_category"].items():
        lines.append(
            f"| `{category}` | {category_summary['passed']} | {category_summary['total']} | "
            f"{category_summary['pass_rate']:.2%} |"
        )
    failures = [case for case in report["cases"] if not case["passed"]]
    lines.extend(["", "## Failures", ""])
    if not failures:
        lines.append("No failed cases.")
    else:
        for case in failures:
            lines.append(f"### `{case['case_id']}`")
            lines.append("")
            lines.extend(f"- {failure}" for failure in case["failures"])
            lines.append("")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This is a deterministic, offline policy benchmark. A pass demonstrates regression stability for the "
            "curated cases; it does not prove that every prompt injection or data-leak technique is covered. "
            "Authorization, rate limiting, domain validation and live-agent behavioral evaluation remain separate gates.",
            "",
        ]
    )
    return "\n".join(lines)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the deterministic VinFast guardrail benchmark.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument("--kind", action="append", choices=sorted(SUPPORTED_KINDS))
    parser.add_argument("--category", action="append")
    parser.add_argument("--tag", action="append")
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--fail-under", type=float, default=1.0)
    parser.add_argument("--max-p95-ms", type=float)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not 0 <= args.fail_under <= 1:
        raise SystemExit("--fail-under must be between 0 and 1")
    dataset = load_dataset(args.dataset)
    report = run_benchmark(
        dataset,
        kinds=set(args.kind or []),
        categories=set(args.category or []),
        tags=set(args.tag or []),
    )
    markdown = render_markdown(report)
    if args.json_output:
        _write(args.json_output, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    if args.markdown_output:
        _write(args.markdown_output, markdown)
    print(
        f"guardrails: {report['summary']['passed']}/{report['summary']['total']} passed "
        f"({report['summary']['pass_rate']:.2%}); p95={report['quality_metrics']['latency_p95_ms']:.4f}ms"
    )
    failed = report["summary"]["pass_rate"] < args.fail_under
    if args.max_p95_ms is not None:
        failed = failed or report["quality_metrics"]["latency_p95_ms"] > args.max_p95_ms
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
