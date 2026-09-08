#!/usr/bin/env python3
"""Phase 6 - Consolidated Microsoft Word validation report.

Consumes the deterministic evidence produced by phases 4 and 5, plus the
Claude-authored judgement file, and renders a single professional .docx:

    <EXECUTION_DIRECTORY>/source-comparison.json   (scripts/source_compare.py)
    <EXECUTION_DIRECTORY>/postman-results.json     (scripts/run_postman.py)
    <EXECUTION_DIRECTORY>/analysis.json            (written by Claude)

Report structure follows .claude/references/test-report-schema.md.

Usage:
    python3 scripts/generate_report.py [--output PATH]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

from framework_config import load_config, resolve

STATUS_COLOURS = {
    "PASS": "C6EFCE", "FAIL": "FFC7CE", "BLOCKED": "FFE0B2",
    "SKIPPED": "FFF2CC", "NOT EXECUTED": "E7E6E6",
    "SAFE_TO_PROCEED": "C6EFCE", "PROCEED_WITH_CAUTION": "FFE0B2",
    "NOT_SAFE": "FFC7CE",
    "HIGH": "FFC7CE", "MEDIUM": "FFE0B2", "LOW": "E7E6E6", "NONE": "C6EFCE",
    "ADDED": "C6EFCE", "DELETED": "FFC7CE", "MODIFIED": "FFF2CC",
    "IDENTICAL": "C6EFCE", "CHANGES_DETECTED": "FFF2CC",
}
HEADER_FILL = "1F3864"
ACCENT = RGBColor(0x1F, 0x38, 0x64)
MUTED = RGBColor(0x59, 0x59, 0x59)


# --------------------------------------------------------------------------
# docx helpers
# --------------------------------------------------------------------------

def shade(cell, hex_fill: str) -> None:
    element = OxmlElement("w:shd")
    element.set(qn("w:val"), "clear")
    element.set(qn("w:fill"), hex_fill)
    cell._tc.get_or_add_tcPr().append(element)


def style_cell(cell, text: str, *, bold: bool = False, size: int = 9,
               colour: RGBColor | None = None, mono: bool = False) -> None:
    cell.text = ""
    paragraph = cell.paragraphs[0]
    paragraph.paragraph_format.space_before = Pt(1)
    paragraph.paragraph_format.space_after = Pt(1)
    run = paragraph.add_run(str(text) if text not in (None, "") else "-")
    run.bold = bold
    run.font.size = Pt(size)
    run.font.name = "Consolas" if mono else "Calibri"
    if colour is not None:
        run.font.color.rgb = colour


def add_table(document, headers: list[str], widths: list[float] | None = None):
    table = document.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    for index, header in enumerate(headers):
        cell = table.rows[0].cells[index]
        style_cell(cell, header, bold=True, size=9, colour=RGBColor(0xFF, 0xFF, 0xFF))
        shade(cell, HEADER_FILL)
    if widths:
        for row in table.rows:
            for index, width in enumerate(widths):
                row.cells[index].width = Inches(width)
    return table


def add_row(table, values: list, widths: list[float] | None = None,
            status_column: int | None = None, mono_columns: tuple[int, ...] = ()):
    cells = table.add_row().cells
    for index, value in enumerate(values):
        style_cell(cells[index], value, size=9, mono=index in mono_columns)
        if status_column is not None and index == status_column:
            fill = STATUS_COLOURS.get(str(value).upper())
            if fill:
                shade(cells[index], fill)
                cells[index].paragraphs[0].runs[0].bold = True
    if widths:
        for index, width in enumerate(widths):
            cells[index].width = Inches(width)
    return cells


def kv_table(document, pairs: list[tuple[str, object]]):
    table = add_table(document, ["Attribute", "Value"], [2.1, 4.4])
    for key, value in pairs:
        add_row(table, [key, value], [2.1, 4.4])
        table.rows[-1].cells[0].paragraphs[0].runs[0].bold = True
    document.add_paragraph()
    return table


def bullets(document, items: list[str], empty: str = "None identified.") -> None:
    if not items:
        para = document.add_paragraph(empty)
        para.runs[0].italic = True
        para.runs[0].font.color.rgb = MUTED
        return
    for item in items:
        document.add_paragraph(str(item), style="List Bullet")


def code_block(document, text: str, max_lines: int = 120) -> None:
    lines = text.splitlines()
    truncated = len(lines) > max_lines
    body = "\n".join(lines[:max_lines])
    if truncated:
        body += f"\n... {len(lines) - max_lines} further lines omitted; see source-comparison.json ..."
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.left_indent = Inches(0.25)
    paragraph.paragraph_format.space_after = Pt(6)
    run = paragraph.add_run(body)
    run.font.name = "Consolas"
    run.font.size = Pt(7.5)


def heading(document, text: str, level: int = 1):
    head = document.add_heading(text, level=level)
    for run in head.runs:
        run.font.color.rgb = ACCENT
    return head


def status_paragraph(document, label: str, value: str) -> None:
    paragraph = document.add_paragraph()
    run = paragraph.add_run(f"{label}: ")
    run.bold = True
    run.font.size = Pt(12)
    value_run = paragraph.add_run(str(value))
    value_run.bold = True
    value_run.font.size = Pt(12)
    upper = str(value).upper()
    if upper in ("FAIL", "NOT_SAFE", "BLOCKED"):
        value_run.font.color.rgb = RGBColor(0xC0, 0x00, 0x00)
    elif upper in ("PASS", "SAFE_TO_PROCEED"):
        value_run.font.color.rgb = RGBColor(0x1E, 0x71, 0x45)
    else:
        value_run.font.color.rgb = RGBColor(0xB2, 0x6B, 0x00)


# --------------------------------------------------------------------------
# Data loading
# --------------------------------------------------------------------------

def load_json(path: Path, label: str) -> dict | None:
    if not path.is_file():
        print(f"WARNING: {label} not found at {path}", file=sys.stderr)
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"WARNING: {label} at {path} is not valid JSON: {exc}", file=sys.stderr)
        return None


def derive_overall(comparison: dict | None, postman: dict | None,
                   analysis: dict) -> str:
    """Overall result, preferring Claude's judgement but never contradicting evidence."""
    stated = str(analysis.get("overallValidationResult", "")).upper().strip()
    if postman is None or not postman.get("executed"):
        return "BLOCKED"
    if postman.get("summary", {}).get("failed", 0) > 0:
        return "FAIL"
    if comparison is None:
        return "BLOCKED"
    if stated in ("PASS", "FAIL", "BLOCKED"):
        return stated
    return "PASS" if postman.get("summary", {}).get("passed", 0) > 0 else "BLOCKED"


# --------------------------------------------------------------------------
# Sections
# --------------------------------------------------------------------------

def cover_page(document, config, comparison, postman, overall, generated) -> None:
    for _ in range(4):
        document.add_paragraph()

    title = document.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run(config.get("APPLICATION_NAME") or "MuleSoft Application")
    run.bold = True
    run.font.size = Pt(26)
    run.font.color.rgb = ACCENT

    subtitle = document.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle.add_run("Deployment Validation and Postman Test Execution Report")
    run.font.size = Pt(15)
    run.font.color.rgb = MUTED

    document.add_paragraph()
    table = add_table(document, ["Attribute", "Value"], [2.3, 4.0])
    rows = [
        ("Application", config.get("APPLICATION_NAME") or "(not configured)"),
        ("Environment", config.get("TARGET_ENVIRONMENT", "DEV")),
        ("Report Generated (UTC)", generated),
        ("Comparison Baseline", "Previous deployment source in workspace"),
        ("Postman Collection", (postman or {}).get("collectionName", "(not executed)")),
        ("Source Comparison", (comparison or {}).get("summary", {}).get("result", "NOT AVAILABLE")),
        ("Postman Result", (postman or {}).get("summary", {}).get("result", "NOT EXECUTED")),
        ("Overall Validation Result", overall),
    ]
    for key, value in rows:
        cells = add_row(table, [key, value], [2.3, 4.0], status_column=1)
        cells[0].paragraphs[0].runs[0].bold = True

    document.add_paragraph()
    note = document.add_paragraph()
    note.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = note.add_run(
        "Generated automatically from GitHub Actions. "
        "All results are derived from actual execution evidence. "
        "Credentials and secrets are redacted."
    )
    run.italic = True
    run.font.size = Pt(9)
    run.font.color.rgb = MUTED
    document.add_page_break()


def section_summary(document, config, comparison, postman, analysis, overall) -> None:
    heading(document, "1. Summary", 1)

    status_paragraph(document, "Overall Validation Result", overall)
    status_paragraph(document, "Source Comparison",
                     (comparison or {}).get("summary", {}).get("result", "NOT AVAILABLE"))
    status_paragraph(document, "Overall Postman Test Status",
                     (postman or {}).get("summary", {}).get("result", "NOT EXECUTED"))
    document.add_paragraph()

    heading(document, "1.1 Scope", 2)
    kv_table(document, [
        ("Application", config.get("APPLICATION_NAME") or "(not configured)"),
        ("Target environment", config.get("TARGET_ENVIRONMENT", "DEV")),
        ("Current source", (comparison or {}).get("current", {}).get("path", "workspace")),
        ("Previous deployment source", (comparison or {}).get("baseline", {}).get("path", "previous_ws")),
        ("Postman collection", (postman or {}).get("collectionPath") or "(not executed)"),
        ("Postman environment", (postman or {}).get("environmentPath") or "(none supplied)"),
        ("Test execution scope", "Full collection - every request executed"),
    ])

    heading(document, "1.2 High-Level Changes Identified", 2)
    bullets(document, analysis.get("highLevelChanges", []),
            "No high-level changes were recorded by the analysis step.")
    document.add_paragraph()

    heading(document, "1.3 Result Counts", 2)
    csum = (comparison or {}).get("summary", {})
    psum = (postman or {}).get("summary", {})
    table = add_table(document, ["Metric", "Count"], [3.6, 1.6])
    for key, value in [
        ("Files compared", csum.get("filesCompared", "-")),
        ("Files added", csum.get("added", "-")),
        ("Files deleted", csum.get("deleted", "-")),
        ("Files modified", csum.get("modified", "-")),
        ("Files unchanged", csum.get("unchanged", "-")),
        ("Test cases total", psum.get("totalTestCases", 0)),
        ("Test cases passed", psum.get("passed", 0)),
        ("Test cases failed", psum.get("failed", 0)),
        ("Test cases skipped", psum.get("skipped", 0)),
        ("Test cases blocked", psum.get("blocked", 0)),
        ("Test cases not executed", psum.get("notExecuted", 0)),
        ("Pass percentage", f"{psum.get('passPercentage', 0)}%"),
        ("Assertions executed", psum.get("assertionsTotal", 0)),
        ("Assertions failed", psum.get("assertionsFailed", 0)),
        ("Execution duration", f"{psum['durationMs']} ms" if psum.get("durationMs") else "-"),
    ]:
        cells = add_row(table, [key, value], [3.6, 1.6])
        cells[0].paragraphs[0].runs[0].bold = True
    document.add_page_break()


def section_source_comparison(document, comparison) -> None:
    heading(document, "2. Source Comparison", 1)

    if comparison is None:
        para = document.add_paragraph(
            "Source comparison evidence is not available. Phase 4 did not complete, "
            "so no change analysis can be reported."
        )
        para.runs[0].bold = True
        document.add_page_break()
        return

    para = document.add_paragraph(
        "The current source in the GitHub Actions workspace was compared file by file, "
        "by content hash, against the previous deployment's source already present in "
        "the workspace. No repository was cloned and no artifact was downloaded."
    )
    para.runs[0].font.size = Pt(10)

    summary = comparison.get("summary", {})
    kv_table(document, [
        ("Baseline", comparison.get("baseline", {}).get("path", "-")),
        ("Current", comparison.get("current", {}).get("path", "-")),
        ("Files compared", summary.get("filesCompared", 0)),
        ("Added / Deleted / Modified",
         f"{summary.get('added', 0)} / {summary.get('deleted', 0)} / {summary.get('modified', 0)}"),
        ("Unchanged", summary.get("unchanged", 0)),
        ("Highest change impact", summary.get("highestImpact", "NONE")),
        ("Comparison result", summary.get("result", "-")),
    ])

    heading(document, "2.1 Changes by Category", 2)
    by_category = summary.get("byCategory", {})
    if by_category:
        table = add_table(document, ["Change Category", "Files"], [3.6, 1.6])
        for category, count in by_category.items():
            add_row(table, [category, count], [3.6, 1.6])
    else:
        bullets(document, [], "No changes detected between the two versions.")
    document.add_paragraph()

    heading(document, "2.2 Changed Files", 2)
    changes = comparison.get("changes", [])
    if changes:
        table = add_table(document, ["File", "Status", "Category", "Impact", "+/-"],
                          [2.9, 0.8, 1.1, 0.7, 0.8])
        for change in changes:
            diff = change.get("diff", {})
            delta = (f"+{diff['linesAdded']}/-{diff['linesRemoved']}"
                     if diff else ("binary" if change.get("binary") else "-"))
            add_row(table, [change["path"], change["status"], change["category"],
                            change["impact"], delta],
                    [2.9, 0.8, 1.1, 0.7, 0.8], status_column=1, mono_columns=(0,))
    else:
        bullets(document, [], "No changed files.")
    document.add_paragraph()

    heading(document, "2.3 Behaviour-Relevant Deltas", 2)
    deltas = comparison.get("behaviourDeltas", {})
    labels = {
        "addedFlows": "Mule flows added",
        "removedFlows": "Mule flows removed",
        "addedEndpoints": "HTTP endpoints added",
        "removedEndpoints": "HTTP endpoints removed",
        "addedDependencies": "Dependencies added",
        "removedDependencies": "Dependencies removed",
        "changedDependencyVersions": "Dependency versions changed",
        "addedConfigKeys": "Configuration keys added",
        "removedConfigKeys": "Configuration keys removed",
    }
    if deltas:
        for key, label in labels.items():
            if deltas.get(key):
                head = document.add_paragraph()
                run = head.add_run(label)
                run.bold = True
                run.font.size = Pt(10)
                bullets(document, deltas[key])
    else:
        bullets(document, [],
                "No flow, endpoint, dependency or configuration key changes were detected.")
    document.add_page_break()


def section_postman(document, postman) -> None:
    heading(document, "3. Postman Test Results", 1)

    if postman is None:
        para = document.add_paragraph("Postman execution evidence is not available.")
        para.runs[0].bold = True
        document.add_page_break()
        return

    if not postman.get("executed"):
        status_paragraph(document, "Postman Execution", "BLOCKED")
        para = document.add_paragraph(
            f"Reason: {postman.get('blockedReason', 'not recorded')}"
        )
        para.runs[0].bold = True
        document.add_paragraph(
            "No test cases were executed, so no test result may be inferred. "
            "All collection test cases are classified BLOCKED."
        )
        document.add_page_break()
        return

    summary = postman.get("summary", {})
    kv_table(document, [
        ("Collection", postman.get("collectionName", "-")),
        ("Collection path", postman.get("collectionPath", "-")),
        ("Environment", postman.get("environmentName", "-")),
        ("Execution scope", "Full collection - every request in the collection was executed"),
        ("Test cases executed", summary.get("totalTestCases", 0)),
        ("Passed", summary.get("passed", 0)),
        ("Failed", summary.get("failed", 0)),
        ("Skipped", summary.get("skipped", 0)),
        ("Not executed", summary.get("notExecuted", 0)),
        ("Pass percentage", f"{summary.get('passPercentage', 0)}%"),
        ("Assertions total / failed",
         f"{summary.get('assertionsTotal', 0)} / {summary.get('assertionsFailed', 0)}"),
        ("Duration", f"{summary['durationMs']} ms" if summary.get("durationMs") else "-"),
        ("Overall Postman result", summary.get("result", "-")),
    ])

    heading(document, "3.1 Results by Folder", 2)
    folders: dict[str, dict[str, int]] = {}
    for test in postman.get("testCases", []):
        bucket = folders.setdefault(test["folder"], {
            "PASS": 0, "FAIL": 0, "SKIPPED": 0, "BLOCKED": 0, "NOT EXECUTED": 0})
        bucket[test["status"]] = bucket.get(test["status"], 0) + 1
    if folders:
        table = add_table(document, ["Folder", "Pass", "Fail", "Skip", "Not Exec."],
                          [2.8, 0.8, 0.8, 0.8, 1.1])
        for name, counts in sorted(folders.items()):
            add_row(table, [name, counts["PASS"], counts["FAIL"], counts["SKIPPED"],
                            counts["NOT EXECUTED"]], [2.8, 0.8, 0.8, 0.8, 1.1])
    document.add_paragraph()

    heading(document, "3.2 Failures", 2)
    failures = [t for t in postman.get("testCases", []) if t["status"] == "FAIL"]
    if not failures:
        bullets(document, [], "No test case failures were recorded.")
    for test in failures:
        head = document.add_paragraph()
        run = head.add_run(f"{test['testCaseId']} - {test['name']}")
        run.bold = True
        run.font.size = Pt(10.5)
        run.font.color.rgb = RGBColor(0xC0, 0x00, 0x00)
        kv_table(document, [
            ("Folder", test["folder"]),
            ("Request", f"{test['method']} {test['url']}"),
            ("HTTP status", f"{test['httpStatus']} {test['httpStatusText']}".strip()
             if test["httpStatus"] else "no response"),
            ("Response time", f"{test['responseTimeMs']} ms" if test.get("responseTimeMs") else "-"),
            ("Transport error", test.get("transportError") or "-"),
            ("Assertions failed",
             f"{test['assertionsFailed']} of {test['assertionsTotal']}"),
        ])
        failed_assertions = [a for a in test["assertions"] if a["failure"]]
        if failed_assertions:
            table = add_table(document, ["Failed Assertion", "Detail"], [2.4, 4.1])
            for assertion in failed_assertions:
                add_row(table, [assertion["name"], assertion["failure"]], [2.4, 4.1])
            document.add_paragraph()
        if test.get("responseBody"):
            caption = document.add_paragraph()
            run = caption.add_run("Response body (redacted, truncated):")
            run.bold = True
            run.font.size = Pt(9)
            code_block(document, test["responseBody"], max_lines=25)
    document.add_page_break()


def section_risk(document, analysis) -> None:
    heading(document, "4. Risk and Impact Analysis", 1)

    narrative = analysis.get("changeImpactNarrative")
    if narrative:
        document.add_paragraph(str(narrative))
        document.add_paragraph()

    heading(document, "4.1 Potential Issues Introduced by the Changes", 2)
    risks = analysis.get("risks", [])
    if risks:
        table = add_table(document, ["Area", "Severity", "Potential Issue", "Mitigation"],
                          [1.3, 0.8, 2.6, 1.8])
        for risk in sorted(risks, key=lambda r: {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(
                str(r.get("severity", "")).upper(), 3)):
            add_row(table, [risk.get("area", "-"), str(risk.get("severity", "-")).upper(),
                            risk.get("description", "-"), risk.get("mitigation", "-")],
                    [1.3, 0.8, 2.6, 1.8], status_column=1)
    else:
        bullets(document, [], "No risks were identified by the analysis step.")
    document.add_paragraph()

    heading(document, "4.2 APIs and Functionality Requiring Attention", 2)
    apis = analysis.get("apisRequiringAttention", [])
    if apis:
        table = add_table(document, ["API / Functionality", "Reason for Attention"], [2.4, 4.1])
        for api in apis:
            add_row(table, [api.get("api", "-"), api.get("reason", "-")], [2.4, 4.1])
    else:
        bullets(document, [], "No APIs were flagged as requiring specific attention.")
    document.add_page_break()


def section_recommendation(document, analysis, overall) -> None:
    heading(document, "5. Final Recommendation", 1)

    recommendation = analysis.get("recommendation", {}) or {}
    verdict = str(recommendation.get("verdict", "")).upper().strip() or "NOT_DETERMINED"
    status_paragraph(document, "Recommendation", verdict.replace("_", " "))
    status_paragraph(document, "Overall Validation Result", overall)
    document.add_paragraph()

    rationale = recommendation.get("rationale")
    if rationale:
        heading(document, "5.1 Rationale", 2)
        document.add_paragraph(str(rationale))

    heading(document, "5.2 Failures and Concerns", 2)
    concerns = recommendation.get("concerns", [])
    if concerns:
        for concern in concerns:
            para = document.add_paragraph(str(concern), style="List Bullet")
            para.runs[0].bold = True
            para.runs[0].font.color.rgb = RGBColor(0xC0, 0x00, 0x00)
    else:
        bullets(document, [], "No failures or concerns were raised.")
    document.add_paragraph()

    heading(document, "5.3 Recommended Actions", 2)
    bullets(document, recommendation.get("actions", []), "No follow-up actions required.")
    document.add_page_break()


def appendix_inventory(document, postman) -> None:
    heading(document, "Appendix A - Complete Test Case Inventory", 1)
    document.add_paragraph(
        "Every test case defined by the Postman collection appears below. "
        "No test case is omitted."
    )
    tests = (postman or {}).get("testCases", [])
    if not tests:
        bullets(document, [], "The collection produced no test cases (execution was blocked).")
        document.add_page_break()
        return
    table = add_table(document, ["ID", "Order", "Folder", "Test Case", "Method",
                                 "HTTP", "Result"],
                      [0.7, 0.5, 1.3, 2.0, 0.6, 0.5, 0.9])
    for test in tests:
        add_row(table, [test["testCaseId"], test["executionOrder"], test["folder"],
                        test["name"], test["method"], test.get("httpStatus") or "-",
                        test["status"]],
                [0.7, 0.5, 1.3, 2.0, 0.6, 0.5, 0.9], status_column=6)
    document.add_page_break()


def appendix_evidence(document, postman) -> None:
    heading(document, "Appendix B - Test Case Execution Evidence", 1)
    tests = (postman or {}).get("testCases", [])
    if not tests:
        bullets(document, [], "No execution evidence available.")
        document.add_page_break()
        return
    for test in tests:
        head = document.add_heading(f"{test['testCaseId']} - {test['name']}", level=2)
        for run in head.runs:
            run.font.color.rgb = ACCENT
            run.font.size = Pt(11)
        kv_table(document, [
            ("Folder / use case", test["folder"]),
            ("Execution order", test["executionOrder"]),
            ("Method", test["method"]),
            ("URL (redacted)", test["url"]),
            ("Request headers (redacted)", test["requestHeaders"] or "-"),
            ("Request body (redacted)", test["requestBody"] or "-"),
            ("HTTP status", f"{test['httpStatus']} {test['httpStatusText']}".strip()
             if test["httpStatus"] else "no response"),
            ("Response time", f"{test['responseTimeMs']} ms" if test.get("responseTimeMs") else "-"),
            ("Response size", f"{test['responseSizeBytes']} bytes"
             if test.get("responseSizeBytes") else "-"),
            ("Assertions", f"{test['assertionsPassed']} passed, "
                           f"{test['assertionsFailed']} failed, "
                           f"{test['assertionsSkipped']} skipped "
                           f"(of {test['assertionsTotal']})"),
            ("Transport error", test.get("transportError") or "-"),
            ("Result", test["status"]),
            ("Result note", test.get("statusReason") or "-"),
        ])
        if test["assertions"]:
            table = add_table(document, ["Assertion", "Result", "Detail"], [2.6, 0.9, 3.0])
            for assertion in test["assertions"]:
                result = ("SKIPPED" if assertion["skipped"]
                          else ("PASS" if assertion["passed"] else "FAIL"))
                add_row(table, [assertion["name"], result, assertion["failure"] or "-"],
                        [2.6, 0.9, 3.0], status_column=1)
            document.add_paragraph()
        if test.get("responseBody"):
            caption = document.add_paragraph()
            run = caption.add_run("Response body (redacted, truncated):")
            run.bold = True
            run.font.size = Pt(9)
            code_block(document, test["responseBody"], max_lines=30)
    document.add_page_break()


def appendix_diffs(document, comparison) -> None:
    heading(document, "Appendix C - Detailed File Change Log", 1)
    changes = (comparison or {}).get("changes", [])
    if not changes:
        bullets(document, [], "No file changes to detail.")
        document.add_page_break()
        return
    for change in changes:
        head = document.add_heading(f"{change['status']} - {change['path']}", level=2)
        for run in head.runs:
            run.font.color.rgb = ACCENT
            run.font.size = Pt(10.5)
        pairs = [
            ("Category", change["category"]),
            ("Impact", change["impact"]),
            ("Binary", "Yes" if change.get("binary") else "No"),
        ]
        if change.get("previousSha256"):
            pairs.append(("Previous SHA-256", change["previousSha256"][:16] + "..."))
        if change.get("currentSha256"):
            pairs.append(("Current SHA-256", change["currentSha256"][:16] + "..."))
        kv_table(document, pairs)

        for key, label in (("muleDelta", "Mule flow / endpoint changes"),
                           ("dependencyDelta", "Dependency changes"),
                           ("configDelta", "Configuration key changes")):
            delta = change.get(key)
            if delta:
                caption = document.add_paragraph()
                run = caption.add_run(label)
                run.bold = True
                run.font.size = Pt(9.5)
                for name, values in delta.items():
                    document.add_paragraph(f"{name}: {', '.join(values)}", style="List Bullet")
                document.add_paragraph()

        diff = change.get("diff")
        if diff and diff.get("text"):
            caption = document.add_paragraph()
            run = caption.add_run(
                f"Unified diff (+{diff['linesAdded']} / -{diff['linesRemoved']}, redacted):")
            run.bold = True
            run.font.size = Pt(9)
            code_block(document, diff["text"])
    document.add_page_break()


def appendix_boundaries(document, config, comparison, postman) -> None:
    heading(document, "Appendix D - Execution Boundaries and Compliance", 1)
    table = add_table(document, ["Control", "Confirmation"], [3.2, 3.3])
    for control, confirmation in [
        ("Repository cloning", "No repository was cloned. The source was read from the existing workspace."),
        ("Artifact download", "No deployment artifact was downloaded from any platform."),
        ("Anypoint Platform", "Not contacted. The previous deployment baseline came from the workspace."),
        ("Previous deployment baseline",
         (comparison or {}).get("baseline", {}).get("path", "previous_ws")),
        ("Source modification", "The MuleSoft source was read only and was not modified."),
        ("Postman collection", "Read from the workspace and executed unmodified."),
        ("Postman environment", "Used unmodified; no environment values were written back."),
        ("Target environment", config.get("TARGET_ENVIRONMENT", "DEV")),
        ("Git write operations", "None performed by this framework."),
        ("Credential handling", "Secrets supplied as environment variables and redacted from this report."),
        ("Result inference", "No PASS was inferred. Every result is backed by execution evidence."),
    ]:
        cells = add_row(table, [control, confirmation], [3.2, 3.3])
        cells[0].paragraphs[0].runs[0].bold = True
    document.add_paragraph()

    para = document.add_paragraph()
    run = para.add_run(
        "All results in this report are derived from actual execution evidence captured "
        "during the workflow run. Test cases that could not be executed are reported as "
        "BLOCKED or NOT EXECUTED with the reason recorded, never as PASS."
    )
    run.italic = True
    run.font.size = Pt(9)
    run.font.color.rgb = MUTED


# --------------------------------------------------------------------------
# Document assembly
# --------------------------------------------------------------------------

def page_footer(document, text: str) -> None:
    for section in document.sections:
        paragraph = section.footer.paragraphs[0]
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = paragraph.add_run(text)
        run.font.size = Pt(8)
        run.font.color.rgb = MUTED


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the consolidated Word validation report.")
    parser.add_argument("--output", help="explicit output .docx path")
    args = parser.parse_args()

    config = load_config()
    execution_dir = resolve(config, "EXECUTION_DIRECTORY")
    report_dir = resolve(config, "REPORT_OUTPUT_DIRECTORY")

    comparison = load_json(execution_dir / "source-comparison.json", "source comparison evidence")
    postman = load_json(execution_dir / "postman-results.json", "Postman execution evidence")
    analysis = load_json(execution_dir / "analysis.json", "analysis") or {}

    if comparison is None and postman is None:
        print("ERROR: neither phase 4 nor phase 5 produced evidence; nothing to report.",
              file=sys.stderr)
        return 2

    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    overall = derive_overall(comparison, postman, analysis)

    document = Document()
    normal = document.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(10)
    for section in document.sections:
        section.left_margin = section.right_margin = Inches(0.9)
        section.top_margin = section.bottom_margin = Inches(0.8)

    cover_page(document, config, comparison, postman, overall, generated)
    section_summary(document, config, comparison, postman, analysis, overall)
    section_source_comparison(document, comparison)
    section_postman(document, postman)
    section_risk(document, analysis)
    section_recommendation(document, analysis, overall)
    appendix_inventory(document, postman)
    appendix_evidence(document, postman)
    appendix_diffs(document, comparison)
    appendix_boundaries(document, config, comparison, postman)

    app = (config.get("APPLICATION_NAME") or "mulesoft-application").strip()
    safe_app = "".join(c if c.isalnum() or c in "-_" else "-" for c in app).strip("-").lower()
    page_footer(document, f"{app} - {config.get('TARGET_ENVIRONMENT', 'DEV')} "
                          f"validation report - generated {generated}")

    if args.output:
        out_path = Path(args.output)
        if not out_path.is_absolute():
            out_path = report_dir / args.output
    else:
        name = config.get("REPORT_FILE_NAME", "").strip()
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        out_path = report_dir / (name or f"{safe_app}-{config.get('TARGET_ENVIRONMENT', 'DEV').lower()}-validation-{stamp}.docx")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    document.save(str(out_path))

    # Validate the written document before declaring success.
    reopened = Document(str(out_path))
    headings = [p.text for p in reopened.paragraphs if p.style.name.startswith("Heading 1")]
    required = ["1. Summary", "2. Source Comparison", "3. Postman Test Results",
                "4. Risk and Impact Analysis", "5. Final Recommendation"]
    missing = [r for r in required if r not in headings]
    if missing:
        print(f"ERROR: generated report is missing sections: {missing}", file=sys.stderr)
        return 2

    inventory_count = len((postman or {}).get("testCases", []))
    print(f"Report generated: {out_path}")
    print(f"  overall result       : {overall}")
    print(f"  sections             : {len(headings)} top-level")
    print(f"  test cases documented: {inventory_count}")
    print(f"  size                 : {out_path.stat().st_size} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
