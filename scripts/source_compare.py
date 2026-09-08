#!/usr/bin/env python3
"""Phase 4 - Source Comparison.

Compares the current MuleSoft source in the GitHub Actions workspace against the
previous deployment's source, which is already present in the workspace at
PREVIOUS_WORKSPACE (default ./previous_ws). Nothing is cloned or downloaded.

Emits <EXECUTION_DIRECTORY>/source-comparison.json describing added, deleted and
modified files, classified by change type, together with Mule flow, API,
dependency and configuration deltas.

Usage:
    python3 scripts/source_compare.py [--quiet]
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

from framework_config import load_config, resolve, split_list, redact

TEXT_SUFFIXES = {
    ".xml", ".properties", ".yaml", ".yml", ".json", ".dwl", ".raml", ".java",
    ".md", ".txt", ".sql", ".csv", ".js", ".ts", ".sh", ".bat", ".conf", ".cfg",
    ".gitignore", ".editorconfig",
}

# (change category, default impact) keyed by a predicate over the relative path.
HIGH, MEDIUM, LOW = "HIGH", "MEDIUM", "LOW"


def classify(rel_path: str) -> tuple[str, str]:
    """Return (category, impact) for a repository-relative path."""
    p = rel_path.replace("\\", "/")
    lower = p.lower()
    name = lower.rsplit("/", 1)[-1]
    suffix = "." + name.rsplit(".", 1)[-1] if "." in name else ""

    if name == "pom.xml" or name in ("build.gradle", "settings.gradle"):
        return "DEPENDENCY", HIGH
    if "/src/test/" in f"/{lower}" or lower.startswith("src/test/"):
        return "TEST", LOW
    if "src/main/mule/" in lower and suffix == ".xml":
        return "MULE_FLOW", HIGH
    if "src/main/api/" in lower or "/api/" in f"/{lower}" and suffix in (".raml", ".yaml", ".yml", ".json"):
        return "API_SPEC", HIGH
    if suffix in (".raml",):
        return "API_SPEC", HIGH
    if suffix == ".dwl" or "/dwl/" in f"/{lower}":
        return "DATAWEAVE", HIGH
    if suffix in (".properties", ".yaml", ".yml") and "src/main/resources" in lower:
        return "CONFIGURATION", MEDIUM
    if name in ("mule-artifact.json", "log4j2.xml", "log4j2-test.xml"):
        return "CONFIGURATION", MEDIUM
    if suffix == ".xml" and "src/main/resources" in lower:
        return "CONFIGURATION", MEDIUM
    if suffix in (".md", ".txt"):
        return "DOCUMENTATION", LOW
    if suffix in (".jar", ".zip", ".png", ".jpg", ".jpeg", ".gif", ".pdf", ".p12", ".jks"):
        return "BINARY", MEDIUM
    return "OTHER", MEDIUM


def is_text(path: Path) -> bool:
    if path.suffix.lower() in TEXT_SUFFIXES:
        return True
    try:
        chunk = path.open("rb").read(4096)
    except OSError:
        return False
    return b"\0" not in chunk


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def collect(root: Path, excludes: list[str], subdirs: list[str]) -> dict[str, Path]:
    """Map repo-relative POSIX path -> absolute path, honouring exclusions."""
    files: dict[str, Path] = {}
    if not root.is_dir():
        return files
    excluded = set(excludes)
    for path in root.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        rel = path.relative_to(root).as_posix()
        parts = rel.split("/")
        if any(part in excluded for part in parts):
            continue
        if subdirs and not any(rel == s or rel.startswith(s.rstrip("/") + "/") for s in subdirs):
            continue
        files[rel] = path
    return files


# --------------------------------------------------------------------------
# Mule XML analysis
# --------------------------------------------------------------------------

def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def parse_mule_xml(text: str) -> dict:
    """Extract flows, sub-flows and HTTP endpoints from a Mule config file."""
    result: dict = {"flows": [], "subFlows": [], "endpoints": [], "parseError": None}
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        result["parseError"] = str(exc)
        return result

    for element in root.iter():
        tag = _local(element.tag)
        name = element.get("name")
        if tag == "flow" and name:
            result["flows"].append(name)
        elif tag == "sub-flow" and name:
            result["subFlows"].append(name)
        elif tag == "listener":
            path = element.get("path")
            if path:
                methods = element.get("allowedMethods", "ANY")
                result["endpoints"].append(f"{methods} {path}")
        elif tag == "request":
            path = element.get("path")
            if path:
                result["endpoints"].append(f"OUTBOUND {element.get('method', 'ANY')} {path}")
        elif tag in ("api-gateway", "apikit-config"):
            raml = element.get("raml") or element.get("api")
            if raml:
                result["endpoints"].append(f"APIKIT {raml}")

    for key in ("flows", "subFlows", "endpoints"):
        result[key] = sorted(set(result[key]))
    return result


def mule_delta(before: str | None, after: str | None) -> dict | None:
    old = parse_mule_xml(before) if before is not None else {"flows": [], "subFlows": [], "endpoints": []}
    new = parse_mule_xml(after) if after is not None else {"flows": [], "subFlows": [], "endpoints": []}
    delta = {}
    for key in ("flows", "subFlows", "endpoints"):
        added = sorted(set(new.get(key, [])) - set(old.get(key, [])))
        removed = sorted(set(old.get(key, [])) - set(new.get(key, [])))
        if added:
            delta[f"added{key[0].upper()}{key[1:]}"] = added
        if removed:
            delta[f"removed{key[0].upper()}{key[1:]}"] = removed
    return delta or None


# --------------------------------------------------------------------------
# pom.xml dependency analysis
# --------------------------------------------------------------------------

def parse_dependencies(text: str) -> dict[str, str]:
    """Map groupId:artifactId -> version for every dependency in a pom."""
    deps: dict[str, str] = {}
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return deps
    for element in root.iter():
        if _local(element.tag) != "dependency":
            continue
        fields = {_local(child.tag): (child.text or "").strip() for child in element}
        group = fields.get("groupId", "")
        artifact = fields.get("artifactId", "")
        if artifact:
            deps[f"{group}:{artifact}"] = fields.get("version", "(inherited)")
    return deps


def dependency_delta(before: str | None, after: str | None) -> dict | None:
    old = parse_dependencies(before) if before else {}
    new = parse_dependencies(after) if after else {}
    added = sorted(f"{k}:{new[k]}" for k in set(new) - set(old))
    removed = sorted(f"{k}:{old[k]}" for k in set(old) - set(new))
    changed = sorted(
        f"{k}: {old[k]} -> {new[k]}" for k in set(old) & set(new) if old[k] != new[k]
    )
    delta = {}
    if added:
        delta["addedDependencies"] = added
    if removed:
        delta["removedDependencies"] = removed
    if changed:
        delta["changedVersions"] = changed
    return delta or None


# --------------------------------------------------------------------------
# Property / YAML key analysis
# --------------------------------------------------------------------------

def parse_property_keys(text: str, suffix: str) -> set[str]:
    keys: set[str] = set()
    if suffix == ".properties":
        for raw in text.splitlines():
            line = raw.strip()
            if line and not line.startswith(("#", "!")) and "=" in line:
                keys.add(line.split("=", 1)[0].strip())
    else:  # yaml / yml - flat key capture, adequate for signalling change
        for raw in text.splitlines():
            line = raw.rstrip()
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or ":" not in stripped:
                continue
            indent = len(line) - len(line.lstrip())
            keys.add(f"{' ' * indent}{stripped.split(':', 1)[0].strip()}")
    return keys


def config_delta(before: str | None, after: str | None, suffix: str) -> dict | None:
    old = parse_property_keys(before, suffix) if before else set()
    new = parse_property_keys(after, suffix) if after else set()
    delta = {}
    if new - old:
        delta["addedKeys"] = sorted(new - old)
    if old - new:
        delta["removedKeys"] = sorted(old - new)
    return delta or None


# --------------------------------------------------------------------------
# Diff rendering
# --------------------------------------------------------------------------

def unified(before: str, after: str, rel: str, max_lines: int) -> dict:
    lines = list(difflib.unified_diff(
        before.splitlines(), after.splitlines(),
        fromfile=f"previous/{rel}", tofile=f"current/{rel}", lineterm="", n=3,
    ))
    added = sum(1 for l in lines if l.startswith("+") and not l.startswith("+++"))
    removed = sum(1 for l in lines if l.startswith("-") and not l.startswith("---"))
    truncated = len(lines) > max_lines
    body = "\n".join(lines[:max_lines])
    if truncated:
        body += f"\n... diff truncated, {len(lines) - max_lines} further lines omitted ..."
    return {
        "linesAdded": added,
        "linesRemoved": removed,
        "truncated": truncated,
        "text": redact(body),
    }


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def build_entry(rel: str, status: str, cur: Path | None, prev: Path | None,
                max_diff_lines: int) -> dict:
    category, impact = classify(rel)
    entry: dict = {"path": rel, "status": status, "category": category, "impact": impact}

    suffix = Path(rel).suffix.lower()
    cur_text = read_text(cur) if cur and is_text(cur) else None
    prev_text = read_text(prev) if prev and is_text(prev) else None
    binary = (cur is not None and cur_text is None) or (prev is not None and prev_text is None)
    entry["binary"] = binary

    if status == "MODIFIED":
        entry["previousSha256"] = sha256(prev)
        entry["currentSha256"] = sha256(cur)
        if binary:
            entry["previousSizeBytes"] = prev.stat().st_size
            entry["currentSizeBytes"] = cur.stat().st_size
        else:
            entry["diff"] = unified(prev_text, cur_text, rel, max_diff_lines)
    elif status == "ADDED":
        entry["currentSha256"] = sha256(cur)
        entry["currentSizeBytes"] = cur.stat().st_size
        if not binary:
            entry["lineCount"] = len(cur_text.splitlines())
    elif status == "DELETED":
        entry["previousSha256"] = sha256(prev)
        entry["previousSizeBytes"] = prev.stat().st_size
        if not binary:
            entry["lineCount"] = len(prev_text.splitlines())

    if category == "MULE_FLOW" and not binary:
        delta = mule_delta(prev_text, cur_text)
        if delta:
            entry["muleDelta"] = delta
    elif category == "DEPENDENCY" and not binary:
        delta = dependency_delta(prev_text, cur_text)
        if delta:
            entry["dependencyDelta"] = delta
    elif category == "CONFIGURATION" and suffix in (".properties", ".yaml", ".yml"):
        delta = config_delta(prev_text, cur_text, suffix)
        if delta:
            entry["configDelta"] = delta

    return entry


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare current source against the previous deployment workspace.")
    parser.add_argument("--quiet", action="store_true", help="suppress the console summary")
    args = parser.parse_args()

    config = load_config()
    current_root = resolve(config, "CURRENT_WORKSPACE")
    previous_root = resolve(config, "PREVIOUS_WORKSPACE")
    execution_dir = resolve(config, "EXECUTION_DIRECTORY")
    excludes = split_list(config["COMPARISON_EXCLUDE"])
    subdirs = split_list(config["MULESOFT_SOURCE_SUBDIRS"])
    max_diff_lines = int(config["COMPARISON_MAX_DIFF_LINES"])

    if not previous_root.is_dir():
        print(
            f"ERROR: previous deployment workspace not found at {previous_root}.\n"
            "       Phase 4 requires the previous deployment source to be present in the\n"
            "       workspace (PREVIOUS_WORKSPACE). Nothing is cloned or downloaded.",
            file=sys.stderr,
        )
        return 2

    current = collect(current_root, excludes, subdirs)
    previous = collect(previous_root, excludes, subdirs)

    if not current:
        print(f"ERROR: no comparable files found under {current_root}", file=sys.stderr)
        return 2

    entries: list[dict] = []
    unchanged = 0

    for rel in sorted(set(current) | set(previous)):
        cur, prev = current.get(rel), previous.get(rel)
        if cur and prev:
            if sha256(cur) == sha256(prev):
                unchanged += 1
                continue
            entries.append(build_entry(rel, "MODIFIED", cur, prev, max_diff_lines))
        elif cur:
            entries.append(build_entry(rel, "ADDED", cur, None, max_diff_lines))
        else:
            entries.append(build_entry(rel, "DELETED", None, prev, max_diff_lines))

    by_status = {s: [e for e in entries if e["status"] == s] for s in ("ADDED", "DELETED", "MODIFIED")}
    by_category: dict[str, int] = {}
    for entry in entries:
        by_category[entry["category"]] = by_category.get(entry["category"], 0) + 1

    highest = LOW
    for entry in entries:
        if entry["impact"] == HIGH:
            highest = HIGH
            break
        if entry["impact"] == MEDIUM:
            highest = MEDIUM

    # Aggregate behaviour-relevant deltas so the report and Claude's analysis do
    # not have to re-derive them from raw diffs.
    aggregate: dict[str, list[str]] = {
        "addedFlows": [], "removedFlows": [], "addedEndpoints": [], "removedEndpoints": [],
        "addedDependencies": [], "removedDependencies": [], "changedDependencyVersions": [],
        "addedConfigKeys": [], "removedConfigKeys": [],
    }
    for entry in entries:
        mule = entry.get("muleDelta", {})
        aggregate["addedFlows"] += [f"{entry['path']}: {n}" for n in mule.get("addedFlows", []) + mule.get("addedSubFlows", [])]
        aggregate["removedFlows"] += [f"{entry['path']}: {n}" for n in mule.get("removedFlows", []) + mule.get("removedSubFlows", [])]
        aggregate["addedEndpoints"] += [f"{entry['path']}: {n}" for n in mule.get("addedEndpoints", [])]
        aggregate["removedEndpoints"] += [f"{entry['path']}: {n}" for n in mule.get("removedEndpoints", [])]
        dep = entry.get("dependencyDelta", {})
        aggregate["addedDependencies"] += dep.get("addedDependencies", [])
        aggregate["removedDependencies"] += dep.get("removedDependencies", [])
        aggregate["changedDependencyVersions"] += dep.get("changedVersions", [])
        cfg = entry.get("configDelta", {})
        aggregate["addedConfigKeys"] += [f"{entry['path']}: {k}" for k in cfg.get("addedKeys", [])]
        aggregate["removedConfigKeys"] += [f"{entry['path']}: {k}" for k in cfg.get("removedKeys", [])]

    result = {
        "phase": "4-source-comparison",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "applicationName": config["APPLICATION_NAME"],
        "targetEnvironment": config["TARGET_ENVIRONMENT"],
        "baseline": {
            "type": "previous-deployment-workspace",
            "path": str(previous_root),
            "description": "Previous deployment source already present in the workspace; not cloned or downloaded.",
        },
        "current": {"type": "github-actions-workspace", "path": str(current_root)},
        "scope": {
            "excludedNames": excludes,
            "restrictedToSubdirs": subdirs or None,
            "maxDiffLines": max_diff_lines,
        },
        "summary": {
            "filesCompared": len(set(current) | set(previous)),
            "unchanged": unchanged,
            "added": len(by_status["ADDED"]),
            "deleted": len(by_status["DELETED"]),
            "modified": len(by_status["MODIFIED"]),
            "totalChanged": len(entries),
            "byCategory": dict(sorted(by_category.items())),
            "highestImpact": highest if entries else "NONE",
            "result": "CHANGES_DETECTED" if entries else "IDENTICAL",
        },
        "behaviourDeltas": {k: v for k, v in aggregate.items() if v},
        "changes": entries,
    }

    execution_dir.mkdir(parents=True, exist_ok=True)
    out_path = execution_dir / "source-comparison.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    if not args.quiet:
        s = result["summary"]
        print(f"Source comparison: {s['result']}")
        print(f"  baseline : {previous_root}")
        print(f"  current  : {current_root}")
        print(f"  compared {s['filesCompared']} files - "
              f"{s['added']} added, {s['deleted']} deleted, {s['modified']} modified, "
              f"{s['unchanged']} unchanged")
        print(f"  highest impact: {s['highestImpact']}")
        print(f"  written to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
