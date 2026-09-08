# Validation Report Schema

Output: a single Microsoft Word `.docx` in `reports/`.

Rendered by `scripts/generate_report.py` from three inputs:

| Input | Written by | Supplies |
|---|---|---|
| `workspace/execution/source-comparison.json` | `scripts/source_compare.py` | cover, sections 1 to 2, appendix C |
| `workspace/execution/postman-results.json` | `scripts/run_postman.py` | cover, sections 1 and 3, appendices A and B |
| `workspace/execution/analysis.json` | Claude | section 1.2, sections 4 and 5 |

---

## Cover Page

Application, target environment, generation timestamp, comparison baseline, Postman
collection, source comparison result, Postman result, and the overall validation
result — colour-coded.

---

## 1. Summary

**1.0** Overall validation result, source comparison result, and overall Postman test
status, as prominent colour-coded lines.

**1.1 Scope** — application, target environment, current source path, previous
deployment source path, collection path, environment path, and the execution scope
statement.

**1.2 High-Level Changes Identified** — from `analysis.highLevelChanges`. One line per
meaningful change, written for a release reviewer.

**1.3 Result Counts** — files compared, added, deleted, modified, unchanged; test cases
total, passed, failed, skipped, blocked, not executed; pass percentage; assertions
executed and failed; execution duration.

---

## 2. Source Comparison

Baseline and current paths, files compared, added/deleted/modified counts, unchanged
count, highest change impact, comparison result.

**2.1 Changes by Category** — file counts per category.

**2.2 Changed Files** — every changed file: path, status, category, impact, and
`+added/-removed` line counts.

**2.3 Behaviour-Relevant Deltas** — Mule flows added and removed, HTTP endpoints added
and removed, dependencies added, removed and version-changed, configuration keys added
and removed.

---

## 3. Postman Test Results

Collection, collection path, environment, execution scope, counts, pass percentage,
assertion totals, duration, overall result.

**3.1 Results by Folder** — pass, fail, skip and not-executed counts per collection
folder.

**3.2 Failures** — per failed test case: folder, request, HTTP status, response time,
transport error, failed assertion count, each failed assertion with its detail, and a
redacted excerpt of the response body.

---

## 4. Risk and Impact Analysis

From `analysis.json`.

The change impact narrative, then:

**4.1 Potential Issues Introduced by the Changes** — area, severity, potential issue,
mitigation. Sorted with HIGH first.

**4.2 APIs and Functionality Requiring Attention** — API or functionality, and the
reason it needs a closer look. Changed areas with no test coverage belong here.

---

## 5. Final Recommendation

From `analysis.json`.

Verdict — `SAFE_TO_PROCEED`, `PROCEED_WITH_CAUTION` or `NOT_SAFE` — alongside the
overall validation result.

**5.1 Rationale** — grounded in the comparison and the test evidence.

**5.2 Failures and Concerns** — each concern, most serious first, in red.

**5.3 Recommended Actions** — concrete follow-ups.

---

## Appendix A — Complete Test Case Inventory

Every test case in the collection: ID, execution order, folder, name, method, HTTP
status, colour-coded result.

No test case may be omitted, and these counts must reconcile with section 1.3.

---

## Appendix B — Test Case Execution Evidence

Per test case: folder, execution order, method, redacted URL, redacted request headers
and body, HTTP status, response time, response size, assertion counts, transport error,
result and result note; a table of every assertion with its outcome; and a redacted,
truncated response body.

---

## Appendix C — Detailed File Change Log

Per changed file: category, impact, binary flag, content hashes, the structured Mule /
dependency / configuration deltas, and the redacted unified diff.

---

## Appendix D — Execution Boundaries and Compliance

Confirms, as a table: no repository cloned, no artifact downloaded, Anypoint Platform
not contacted, the baseline used, source not modified, collection and environment used
unmodified, target environment, no Git write operations, secrets redacted, and that no
PASS was inferred.

---

## Result Reconciliation

The generator will not let the narrative contradict the evidence:

- any failed test case forces the overall result to `FAIL`
- an unexecuted collection forces `BLOCKED`
- otherwise `analysis.overallValidationResult` is honoured

## Validation Before Success

After saving, the document is re-opened and checked for all five required section
headings. A missing section is a non-zero exit, not a warning.
