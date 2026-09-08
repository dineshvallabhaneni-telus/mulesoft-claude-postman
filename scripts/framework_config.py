"""Shared settings and redaction helpers for the validation framework.

The framework is zero-config. Everything it needs is either already in the
GitHub Actions workspace or has a sensible default here. Any value can be
overridden by an environment variable of the same name, which is how a calling
GitHub Actions workflow customises a run:

    env:
      TARGET_ENVIRONMENT: QA
      PREVIOUS_WORKSPACE: ./baseline

There is no configuration file and no credentials file. Secrets are supplied
only as environment variables, normally from GitHub Actions secrets, and are
redacted from everything this framework writes.
"""

from __future__ import annotations

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(os.environ.get("GITHUB_WORKSPACE") or Path(__file__).resolve().parent.parent).resolve()

DEFAULTS = {
    # Empty means "derive from the workspace"; see resolve_application_name().
    "APPLICATION_NAME": "",
    "TARGET_ENVIRONMENT": "DEV",

    # Where things already are in the workspace.
    "CURRENT_WORKSPACE": ".",
    "PREVIOUS_WORKSPACE": "./previous_ws",
    "POSTMAN_COLLECTION_DIR": "./postman_collection",

    # Empty means "auto-discover inside POSTMAN_COLLECTION_DIR".
    "POSTMAN_COLLECTION_FILE": "",
    "POSTMAN_ENVIRONMENT_FILE": "",

    # Where this framework writes. Nothing else is written to.
    "EXECUTION_DIRECTORY": "./workspace/execution",
    "REPORT_OUTPUT_DIRECTORY": "./reports",
    "REPORT_FILE_NAME": "",

    # Comparison tuning.
    "MULESOFT_SOURCE_SUBDIRS": "",
    "COMPARISON_EXCLUDE": (
        ".git,.github,.claude,.vscode,.idea,target,node_modules,.mule,"
        "previous_ws,workspace,reports,scripts,Prompt,postman_collection,.DS_Store"
    ),
    "COMPARISON_MAX_DIFF_LINES": "400",

    # Newman tuning.
    "NEWMAN_TIMEOUT_REQUEST": "60000",
    "NEWMAN_DELAY_REQUEST": "0",
    "NEWMAN_INSECURE": "false",
    "NEWMAN_BAIL": "false",
}


def resolve_application_name() -> str:
    """Derive the application name from the workspace itself.

    Order: pom.xml artifactId, then the GitHub repository name, then the
    workspace directory name.
    """
    pom = REPO_ROOT / "pom.xml"
    if pom.is_file():
        try:
            root = ET.fromstring(pom.read_text(encoding="utf-8", errors="replace"))
            for child in root:
                if child.tag.rsplit("}", 1)[-1] == "artifactId" and (child.text or "").strip():
                    return child.text.strip()
        except (OSError, ET.ParseError):
            pass
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    if repository:
        return repository.rsplit("/", 1)[-1]
    return REPO_ROOT.name


def load_config() -> dict[str, str]:
    config = dict(DEFAULTS)
    for key in list(config):
        override = os.environ.get(key)
        if override not in (None, ""):
            config[key] = override
    if not config["APPLICATION_NAME"].strip():
        config["APPLICATION_NAME"] = resolve_application_name()
    return config


def resolve(config: dict[str, str], key: str) -> Path:
    """Resolve a configured path against the workspace root."""
    return (REPO_ROOT / config[key]).resolve()


def split_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


# --------------------------------------------------------------------------
# Redaction
# --------------------------------------------------------------------------

_SENSITIVE_KEY = re.compile(
    r"(pass(word|wd)?|secret|token|api[-_ ]?key|client[-_ ]?secret|credential|"
    r"authorization|auth[-_ ]?key|private[-_ ]?key|access[-_ ]?key|bearer|"
    r"connection[-_ ]?string|salt|passphrase)",
    re.IGNORECASE,
)

# Matches key="value" / key: value / key=value / "key": "value"
_KEY_VALUE = re.compile(
    r"""(?P<key>[A-Za-z0-9_.\-\[\]]*
        (?:pass(?:word|wd)?|secret|token|api[-_]?key|client[-_]?secret|credential|
           authorization|auth[-_]?key|private[-_]?key|access[-_]?key|passphrase|salt)
        [A-Za-z0-9_.\-\[\]]*)
        (?P<sep>\s*["']?\s*[:=]\s*["']?)
        (?P<value>[^"'\s<>,}\]]+)""",
    re.IGNORECASE | re.VERBOSE,
)

_BEARER = re.compile(r"(Bearer\s+)[A-Za-z0-9._\-]{8,}", re.IGNORECASE)
_BASIC = re.compile(r"(Basic\s+)[A-Za-z0-9+/=]{8,}", re.IGNORECASE)
_URL_CREDS = re.compile(r"(://)[^/\s:@]+:[^/\s:@]+(@)")
_PAT_LIKE = re.compile(r"\b(?:github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{20,})\b")

REDACTED = "[REDACTED]"


def redact(text: str | None) -> str:
    """Strip credential-looking values from any text that reaches a report."""
    if not text:
        return "" if text is None else text
    out = _PAT_LIKE.sub(REDACTED, text)
    out = _URL_CREDS.sub(r"\1" + REDACTED + r"\2", out)
    out = _BEARER.sub(r"\1" + REDACTED, out)
    out = _BASIC.sub(r"\1" + REDACTED, out)
    out = _KEY_VALUE.sub(lambda m: f"{m.group('key')}{m.group('sep')}{REDACTED}", out)
    return out


def is_sensitive_key(name: str) -> bool:
    return bool(_SENSITIVE_KEY.search(name or ""))
