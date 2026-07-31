"""Run deterministic checks for the AI Glossary Tutor golden set."""

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


REQUIRED_RESPONSE_FIELDS = {
    "term",
    "expanded_form",
    "meaning_in_context",
    "plain_explanation",
    "example",
    "related_concepts",
    "confidence",
    "evidence_span",
    "clarifying_question",
    "used_model",
}
CONFIDENCE_VALUES = {"high", "low", "insufficient"}
AUTOMATED_DIMENSIONS = {
    "acronym_expansion",
    "grounding",
    "schema_length",
    "calibration",
}


def normalize(value):
    if value is None:
        return ""
    return " ".join(str(value).casefold().split())


def word_count(value):
    return len(str(value or "").split())


def expected_confidence(test_case):
    behavior = normalize(test_case["expected_behavior"])
    failures = " ".join(test_case["hard_fail_conditions"])
    if "confidence insufficient" in behavior or "confidence là high" in normalize(failures):
        return "insufficient" if "confidence insufficient" in behavior else "high"
    return None


def check_response(test_case, response):
    failures = []
    warnings = []

    missing_fields = sorted(REQUIRED_RESPONSE_FIELDS - response.keys())
    if missing_fields:
        failures.append(f"schema_missing_fields:{','.join(missing_fields)}")

    if response.get("term") != test_case["selected_text"]:
        failures.append("term_does_not_match_selection")

    if response.get("confidence") not in CONFIDENCE_VALUES:
        failures.append("invalid_confidence")

    if not isinstance(response.get("related_concepts"), list):
        failures.append("related_concepts_not_list")
    elif len(response["related_concepts"]) > 3:
        failures.append("too_many_related_concepts")

    if word_count(response.get("plain_explanation")) > 80:
        failures.append("plain_explanation_too_long")
    if word_count(response.get("example")) > 50:
        failures.append("example_too_long")

    expected_expansion = test_case["expected_expansion"]
    if expected_expansion and normalize(response.get("expanded_form")) != normalize(expected_expansion):
        failures.append("acronym_expansion_mismatch")

    evidence_span = response.get("evidence_span")
    context = test_case["surrounding_context"]
    if evidence_span:
        if evidence_span not in context:
            failures.append("evidence_not_in_context")
    elif response.get("confidence") != "insufficient":
        failures.append("missing_evidence_for_non_insufficient_response")

    confidence = response.get("confidence")
    if confidence == "insufficient" and not response.get("clarifying_question"):
        failures.append("missing_clarifying_question")
    if confidence != "insufficient" and response.get("clarifying_question"):
        warnings.append("unexpected_clarifying_question")

    required_confidence = expected_confidence(test_case)
    if required_confidence and confidence != required_confidence:
        failures.append(f"unexpected_confidence:expected_{required_confidence}")

    manual_dimensions = [
        dimension
        for dimension in test_case["required_dimensions"]
        if dimension not in AUTOMATED_DIMENSIONS
    ]
    if manual_dimensions:
        warnings.append("semantic_review_required:" + ",".join(manual_dimensions))

    return {
        "passed_deterministic_checks": not failures,
        "failures": failures,
        "warnings": warnings,
        "manual_dimensions": manual_dimensions,
    }


def post_json(url, payload, timeout):
    body = json.dumps(payload).encode("utf-8")
    request = Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=timeout) as http_response:
        return http_response.status, json.loads(http_response.read().decode("utf-8"))


def call_explain(base_url, test_case, timeout):
    payload = {
        "selected_text": test_case["selected_text"],
        "surrounding_context": test_case["surrounding_context"],
        "learner_level": "coban" if test_case["learner_level"] == "beginner" else test_case["learner_level"],
    }
    started_at = time.perf_counter()
    try:
        status_code, response = post_json(f"{base_url}/api/explain", payload, timeout)
        return {
            "request": payload,
            "http_status": status_code,
            "latency_ms": round((time.perf_counter() - started_at) * 1000),
            "response": response,
            "request_error": None,
        }
    except HTTPError as error:
        return {
            "request": payload,
            "http_status": error.code,
            "latency_ms": round((time.perf_counter() - started_at) * 1000),
            "response": error.read().decode("utf-8", errors="replace"),
            "request_error": f"HTTPError: {error}",
        }
    except (URLError, TimeoutError, json.JSONDecodeError) as error:
        return {
            "request": payload,
            "http_status": None,
            "latency_ms": round((time.perf_counter() - started_at) * 1000),
            "response": None,
            "request_error": f"{type(error).__name__}: {error}",
        }


def write_summary(result, path):
    lines = [
        "# Golden Set Evaluation",
        "",
        f"- Run: `{result['run_id']}`",
        f"- Endpoint: `{result['endpoint']}`",
        f"- Cases: {result['summary']['total_cases']}",
        f"- Deterministic pass: {result['summary']['deterministic_passed']}/{result['summary']['total_cases']} ({result['summary']['deterministic_pass_rate']}%)",
        f"- Request errors: {result['summary']['request_errors']}",
        f"- Cases requiring semantic review: {result['summary']['semantic_review_required']}",
        "",
        "| Case | HTTP | Model | Deterministic | Failures | Semantic review |",
        "|---|---:|---|---|---|---|",
    ]
    for case in result["cases"]:
        check = case.get("checks", {})
        model = case.get("response", {}).get("used_model", "-") if isinstance(case.get("response"), dict) else "-"
        deterministic = "PASS" if check.get("passed_deterministic_checks") else "FAIL"
        failures = "; ".join(check.get("failures", [])) or "-"
        review = ", ".join(check.get("manual_dimensions", [])) or "-"
        lines.append(f"| `{case['id']}` | {case.get('http_status') or '-'} | {model} | {deterministic} | {failures} | {review} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Evaluate the glossary endpoint against eval/golden_set.json.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8001", help="Running backend URL")
    parser.add_argument("--golden-set", default="eval/golden_set.json", help="Golden set JSON path")
    parser.add_argument("--output-dir", default="eval/results", help="Directory for timestamped run artifacts")
    parser.add_argument("--timeout", type=int, default=30, help="Per-case HTTP timeout in seconds")
    parser.add_argument("--delay-seconds", type=float, default=2.5, help="Pause between cases to avoid API rate limits")
    parser.add_argument("--dry-run", action="store_true", help="Validate the golden set without calling the backend")
    args = parser.parse_args()

    golden_set_path = Path(args.golden_set)
    try:
        golden_set = json.loads(golden_set_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        sys.exit(f"Cannot read golden set: {error}")

    if not isinstance(golden_set, list) or not golden_set:
        sys.exit("Golden set must be a non-empty JSON array.")
    if args.delay_seconds < 0:
        sys.exit("--delay-seconds must be zero or greater.")
    ids = [test_case.get("id") for test_case in golden_set]
    if len(ids) != len(set(ids)) or any(not case_id for case_id in ids):
        sys.exit("Every golden-set case must have a unique, non-empty id.")

    if args.dry_run:
        print(f"Golden set valid: {len(golden_set)} cases, {sum(case['source_ref'].startswith('chatlog:') for case in golden_set)} chatlog-derived cases.")
        return

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    cases = []
    for index, test_case in enumerate(golden_set, start=1):
        print(f"[{index}/{len(golden_set)}] {test_case['id']}", flush=True)
        run_case = {"id": test_case["id"], "source_ref": test_case["source_ref"]}
        run_case.update(call_explain(args.base_url.rstrip("/"), test_case, args.timeout))
        if run_case["request_error"]:
            run_case["checks"] = {
                "passed_deterministic_checks": False,
                "failures": ["request_failed"],
                "warnings": [],
                "manual_dimensions": test_case["required_dimensions"],
            }
        else:
            run_case["checks"] = check_response(test_case, run_case["response"])
        cases.append(run_case)
        if index < len(golden_set) and args.delay_seconds:
            time.sleep(args.delay_seconds)

    total_cases = len(cases)
    deterministic_passed = sum(case["checks"]["passed_deterministic_checks"] for case in cases)
    result = {
        "run_id": timestamp,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "endpoint": args.base_url.rstrip("/"),
        "golden_set": str(golden_set_path),
        "summary": {
            "total_cases": total_cases,
            "deterministic_passed": deterministic_passed,
            "deterministic_pass_rate": round(deterministic_passed / total_cases * 100, 2),
            "request_errors": sum(case["request_error"] is not None for case in cases),
            "semantic_review_required": sum(bool(case["checks"]["manual_dimensions"]) for case in cases),
        },
        "cases": cases,
    }

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"run-{timestamp}.json"
    markdown_path = output_dir / f"run-{timestamp}-summary.md"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_summary(result, markdown_path)
    print(f"Saved raw results: {json_path}")
    print(f"Saved summary: {markdown_path}")


if __name__ == "__main__":
    main()
