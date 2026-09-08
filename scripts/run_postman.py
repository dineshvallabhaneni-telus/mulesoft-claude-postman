#!/usr/bin/env python3
"""Phase 5 - Postman Testing.

Runs the full Postman collection found in POSTMAN_COLLECTION_DIR (default
./postman_collection) with Newman, against the target environment. The
collection is already in the GitHub Actions workspace; nothing is cloned or
downloaded, and neither the collection nor the environment file is modified.

Emits <EXECUTION_DIRECTORY>/postman-results.json with a normalised, redacted
record of every request, assertion and response.

Exit codes:
    0  collection executed (individual test failures still produce 0; the
       report and the workflow gate decide the overall outcome)
    2  configuration or precondition error - collection could not be executed
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from framework_config import REPO_ROOT, load_config, resolve, redact

MAX_BODY_CHARS = 4000


def discover(directory: Path, config: dict, key: str, patterns: list[str],
             prefer: str | None = None) -> Path | None:
    """Resolve an explicitly configured file, else auto-discover by pattern.

    A configured value is tried relative to the collection directory first, then
    relative to the repository root / as an absolute path.
    """
    configured = config.get(key, "").strip()
    if configured:
        for candidate in (directory / configured, Path(configured), REPO_ROOT / configured):
            if candidate.is_file():
                return candidate
        return None

    matches: list[Path] = []
    for pattern in patterns:
        matches.extend(sorted(directory.rglob(pattern)))
    # De-duplicate while preserving discovery order.
    unique = list(dict.fromkeys(matches))
    if not unique:
        return None
    if prefer:
        preferred = [m for m in unique if prefer.lower() in m.name.lower()]
        if preferred:
            return preferred[0]
    return unique[0]


def folder_index(collection: dict) -> dict[str, str]:
    """Map request item id -> 'Folder / Subfolder' path within the collection."""
    index: dict[str, str] = {}

    def walk(items, trail):
        for item in items or []:
            name = item.get("name", "")
            if "item" in item:
                walk(item["item"], trail + [name])
            else:
                index[item.get("id") or name] = " / ".join(trail) if trail else "(root)"

    walk(collection.get("item", []), [])
    return index


def truncate(text: str | None) -> str:
    if not text:
        return ""
    if len(text) > MAX_BODY_CHARS:
        return text[:MAX_BODY_CHARS] + f"\n... truncated, {len(text) - MAX_BODY_CHARS} further characters omitted ..."
    return text


def header_list(headers) -> str:
    """Render request/response headers as redacted 'Name: value' lines."""
    if not headers:
        return ""
    if isinstance(headers, dict):
        pairs = headers.get("members") or headers.get("reference") or []
        if isinstance(pairs, dict):
            pairs = list(pairs.values())
    else:
        pairs = headers
    lines = []
    for header in pairs or []:
        if not isinstance(header, dict) or header.get("disabled"):
            continue
        lines.append(f"{header.get('key', '')}: {header.get('value', '')}")
    return redact("\n".join(lines))


def url_string(url) -> str:
    if isinstance(url, str):
        return redact(url)
    if not isinstance(url, dict):
        return ""
    raw = url.get("raw")
    if raw:
        return redact(raw)
    host = url.get("host")
    host = ".".join(host) if isinstance(host, list) else (host or "")
    path = url.get("path")
    path = "/".join(str(p) for p in path) if isinstance(path, list) else (path or "")
    protocol = url.get("protocol", "https")
    return redact(f"{protocol}://{host}/{path}".rstrip("/"))


def stream_to_text(stream) -> str:
    if stream is None:
        return ""
    if isinstance(stream, str):
        return stream
    if isinstance(stream, dict) and stream.get("type") == "Buffer":
        try:
            return bytes(stream.get("data", [])).decode("utf-8", errors="replace")
        except (TypeError, ValueError):
            return ""
    return str(stream)


def normalise(newman: dict, folders: dict[str, str], collection_name: str,
              environment_name: str) -> dict:
    run = newman.get("run", {})
    executions = run.get("executions", [])
    tests: list[dict] = []

    for order, execution in enumerate(executions, start=1):
        item = execution.get("item", {}) or {}
        request = execution.get("request", {}) or {}
        response = execution.get("response") or {}
        assertions = execution.get("assertions") or []
        req_error = execution.get("requestError")

        assertion_records = []
        for assertion in assertions:
            error = assertion.get("error")
            assertion_records.append({
                "name": assertion.get("assertion", ""),
                "skipped": bool(assertion.get("skipped")),
                "passed": error is None and not assertion.get("skipped"),
                "failure": redact(
                    f"{error.get('name', '')}: {error.get('message', '')}"
                ) if error else None,
            })

        executed = bool(response) or req_error is not None
        reason = None
        if req_error:
            status = "FAIL"
        elif not executed:
            status = "NOT EXECUTED"
            reason = "Newman recorded no response for this request."
        elif any(a["failure"] for a in assertion_records):
            status = "FAIL"
        elif assertion_records and all(a["skipped"] for a in assertion_records):
            status = "SKIPPED"
            reason = "All assertions for this request were skipped by the collection."
        elif assertion_records:
            status = "PASS"
        else:
            # The request ran, but the collection defines no assertions for it,
            # so there is no evidence of correctness. Never infer a PASS from a
            # bare 2xx. Reported as NOT EXECUTED with the reason recorded.
            status = "NOT EXECUTED"
            reason = ("Request was sent, but the collection defines no assertions "
                      "for it; no PASS can be inferred without a validation.")

        body = request.get("body") or {}
        raw_body = body.get("raw") if isinstance(body, dict) else None

        tests.append({
            "testCaseId": f"TC-{order:03d}",
            "executionOrder": order,
            "name": item.get("name", "(unnamed request)"),
            "folder": folders.get(item.get("id") or item.get("name", ""), "(root)"),
            "method": request.get("method", ""),
            "url": url_string(request.get("url")),
            "requestHeaders": header_list(request.get("header")),
            "requestBody": redact(truncate(raw_body)),
            "httpStatus": response.get("code"),
            "httpStatusText": response.get("status", ""),
            "responseTimeMs": response.get("responseTime"),
            "responseSizeBytes": response.get("responseSize"),
            "responseHeaders": header_list(response.get("header")),
            "responseBody": redact(truncate(stream_to_text(response.get("stream")))),
            "assertions": assertion_records,
            "assertionsTotal": len(assertion_records),
            "assertionsPassed": sum(1 for a in assertion_records if a["passed"]),
            "assertionsFailed": sum(1 for a in assertion_records if a["failure"]),
            "assertionsSkipped": sum(1 for a in assertion_records if a["skipped"]),
            "transportError": redact(
                f"{req_error.get('name', '')}: {req_error.get('message', '')}"
                if isinstance(req_error, dict) else str(req_error)
            ) if req_error else None,
            "status": status,
            "statusReason": reason,
        })

    counts = {s: sum(1 for t in tests if t["status"] == s)
              for s in ("PASS", "FAIL", "SKIPPED", "BLOCKED", "NOT EXECUTED")}
    stats = run.get("stats", {})
    timings = run.get("timings", {})

    return {
        "phase": "5-postman-testing",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "collectionName": collection_name,
        "environmentName": environment_name,
        "executed": True,
        "scope": "FULL_COLLECTION",
        "summary": {
            "totalTestCases": len(tests),
            "passed": counts["PASS"],
            "failed": counts["FAIL"],
            "skipped": counts["SKIPPED"],
            "blocked": counts["BLOCKED"],
            "notExecuted": counts["NOT EXECUTED"],
            "passPercentage": round(
                counts["PASS"] / len(tests) * 100, 1) if tests else 0.0,
            "requestsTotal": stats.get("requests", {}).get("total", len(tests)),
            "assertionsTotal": stats.get("assertions", {}).get("total", 0),
            "assertionsFailed": stats.get("assertions", {}).get("failed", 0),
            "durationMs": timings.get("completed", 0) - timings.get("started", 0)
            if timings.get("completed") and timings.get("started") else None,
            "result": "FAIL" if counts["FAIL"] else ("PASS" if counts["PASS"] else "NOT EXECUTED"),
        },
        "testCases": tests,
    }


def blocked_result(reason: str, collection_name: str, environment_name: str) -> dict:
    return {
        "phase": "5-postman-testing",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "collectionName": collection_name,
        "environmentName": environment_name,
        "executed": False,
        "scope": "FULL_COLLECTION",
        "blockedReason": reason,
        "summary": {
            "totalTestCases": 0, "passed": 0, "failed": 0, "skipped": 0,
            "blocked": 0, "notExecuted": 0, "passPercentage": 0.0,
            "requestsTotal": 0, "assertionsTotal": 0, "assertionsFailed": 0,
            "durationMs": None, "result": "BLOCKED",
        },
        "testCases": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute the workspace Postman collection with Newman.")
    parser.add_argument("--quiet", action="store_true", help="suppress the console summary")
    args = parser.parse_args()

    config = load_config()
    collection_dir = resolve(config, "POSTMAN_COLLECTION_DIR")
    execution_dir = resolve(config, "EXECUTION_DIRECTORY")
    target_env = config["TARGET_ENVIRONMENT"]
    execution_dir.mkdir(parents=True, exist_ok=True)
    out_path = execution_dir / "postman-results.json"

    def fail(reason: str) -> int:
        out_path.write_text(json.dumps(blocked_result(reason, "", target_env), indent=2), encoding="utf-8")
        print(f"ERROR: {reason}", file=sys.stderr)
        return 2

    if not collection_dir.is_dir():
        return fail(f"Postman collection directory not found at {collection_dir}")

    collection = discover(collection_dir, config, "POSTMAN_COLLECTION_FILE",
                          ["*.postman_collection.json", "*collection*.json"])
    if not collection:
        return fail(f"No Postman collection file found under {collection_dir}")

    environment = discover(collection_dir, config, "POSTMAN_ENVIRONMENT_FILE",
                           ["*.postman_environment.json", "*environment*.json"],
                           prefer=target_env)

    if shutil.which("newman") is None:
        return fail("Newman is not available on PATH. Install it with: npm install -g newman")

    try:
        collection_json = json.loads(collection.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return fail(f"Postman collection could not be parsed: {exc}")

    collection_name = collection_json.get("info", {}).get("name", collection.stem)
    environment_name = environment.stem if environment else f"{target_env} (none supplied)"

    newman_json = execution_dir / "newman-raw.json"
    command = [
        "newman", "run", str(collection),
        "--reporters", "cli,json",
        "--reporter-json-export", str(newman_json),
    ]

    # Newman rejects a zero or negative value for these, so only pass them when set.
    def positive(key: str) -> int:
        try:
            return max(0, int(config[key]))
        except ValueError:
            return 0

    timeout = positive("NEWMAN_TIMEOUT_REQUEST")
    if timeout:
        command += ["--timeout-request", str(timeout)]
    delay = positive("NEWMAN_DELAY_REQUEST")
    if delay:
        command += ["--delay-request", str(delay)]

    if environment:
        command += ["--environment", str(environment)]
    if config["NEWMAN_INSECURE"].lower() == "true":
        command.append("--insecure")
    if config["NEWMAN_BAIL"].lower() == "true":
        command.append("--bail")

    if not args.quiet:
        print(f"Executing full Postman collection: {collection_name}")
        print(f"  collection : {collection}")
        print(f"  environment: {environment or '(none)'}")

    # Newman exits non-zero when tests fail; that is a reportable outcome, not
    # a framework error, so the return code is not treated as fatal here.
    subprocess.run(command, cwd=str(collection_dir.parent), check=False)

    if not newman_json.is_file():
        return fail("Newman produced no JSON report; the collection did not execute")

    try:
        raw = json.loads(newman_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return fail(f"Newman JSON report could not be parsed: {exc}")

    folders = folder_index(raw.get("collection") or collection_json)
    result = normalise(raw, folders, collection_name, environment_name)
    result["collectionPath"] = str(collection.relative_to(collection_dir.parent))
    result["environmentPath"] = str(environment.relative_to(collection_dir.parent)) if environment else None

    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    newman_json.unlink(missing_ok=True)

    if not args.quiet:
        s = result["summary"]
        print(f"Postman execution: {s['result']}")
        print(f"  {s['totalTestCases']} test cases - {s['passed']} passed, "
              f"{s['failed']} failed, {s['skipped']} skipped, {s['notExecuted']} not executed")
        print(f"  written to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
