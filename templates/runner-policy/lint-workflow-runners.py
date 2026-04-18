#!/usr/bin/env python3
"""
lint-workflow-runners.py
========================

MedinovAI-org workflow-runner policy linter. Reads every GitHub Actions
workflow file under ``.github/workflows/`` and flags any ``runs-on:``
directive that references a hosted-runner label the org is not entitled
to use.

Why this exists
---------------

The ``medinovai-health`` org has no GitHub-hosted runner entitlement — see
``medinovai-infrastructure#1``. The org has exactly one runner pool:

    [self-hosted, aifactory, ...]

Any job declaring ``runs-on: ubuntu-latest`` (or any other hosted label)
sits in the runner-assignment queue for ~7 seconds, then auto-fails with
``runner_id: 0, steps: []``. That failure shape is indistinguishable from
a real test regression and has hidden weeks of silent CI breakage.

This linter refuses to let new workflows land with a hosted-runner label.

Behaviour
---------

* Walks the repository for ``.github/workflows/*.yml`` (and ``*.yaml``).
* For each job (including jobs inside matrix strategies), inspects the
  ``runs-on`` value.
* FAIL when ``runs-on`` references a forbidden hosted-runner prefix:
  ``ubuntu-``, ``windows-``, ``macos-`` (ignoring ``[self-hosted, ...]``
  arrays that happen to mention ``macos`` secondarily).
* WARN (non-fatal) when ``runs-on`` is a plain ``${{ ... }}`` expression
  (dynamic selection can't be statically proven safe). This keeps the
  check useful without blocking legitimate matrix-driven selection.
* PASS silently for ``[self-hosted, ...]`` lists or the bare string
  ``self-hosted``.
* Ignores workflow files that declare ``# runner-policy: ignore`` on any
  line within their first 20 lines. Use sparingly, document the reason.

Exit codes
----------

* 0 when no violations are found.
* 1 when any forbidden ``runs-on`` is detected.
* 2 when the tool itself fails (e.g. invalid YAML).

CLI
---

    python3 lint-workflow-runners.py [--repo PATH] [--format {text,json}]

``--repo`` defaults to the current working directory.

Dependencies
------------

Requires ``pyyaml``. On the aifactory runner, install into a venv:

    python3.12 -m venv .ci-venv && .ci-venv/bin/pip install pyyaml==6.0.2
    .ci-venv/bin/python scripts/lint-workflow-runners.py
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.stderr.write(
        "lint-workflow-runners.py requires PyYAML. Install it with:\n"
        "    pip install pyyaml\n"
    )
    sys.exit(2)


# Runner-label prefixes that indicate a GitHub-hosted runner. A job whose
# ``runs-on`` resolves to any of these is rejected because the medinovai
# org has no entitlement.
_FORBIDDEN_PREFIXES = ("ubuntu-", "windows-", "macos-")

# Labels that are explicitly allowed (self-hosted flavour). We accept the
# bare ``self-hosted`` token, and any list that contains ``self-hosted``.
_ALLOWED_SELF_HOSTED = {"self-hosted"}


@dataclass
class Finding:
    workflow: str
    job: str
    runs_on: Any
    level: str  # "error" or "warning"
    reason: str

    def as_dict(self) -> dict:
        return {
            "workflow": self.workflow,
            "job": self.job,
            "runs_on": self.runs_on,
            "level": self.level,
            "reason": self.reason,
        }


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)
    workflows_scanned: int = 0

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.level == "error"]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.level == "warning"]


def _classify(runs_on: Any) -> tuple[str, str]:
    """
    Return ``(level, reason)`` for a given ``runs-on`` value.

    ``level`` is one of ``ok``, ``warning``, ``error``.
    """

    # List form: ["self-hosted", "aifactory"] etc.
    if isinstance(runs_on, list):
        tokens = [str(t).lower() for t in runs_on]
        if any(t in _ALLOWED_SELF_HOSTED for t in tokens):
            return "ok", "self-hosted label present"
        for t in tokens:
            if any(t.startswith(p) for p in _FORBIDDEN_PREFIXES):
                return (
                    "error",
                    f"hosted-runner label '{t}' is not entitled on this org "
                    "(see medinovai-infrastructure#1)",
                )
        return "warning", f"unrecognised runner array: {runs_on!r}"

    # String form.
    if isinstance(runs_on, str):
        raw = runs_on.strip()
        lower = raw.lower()

        # Dynamic expression — can't statically verify.
        if raw.startswith("${{") and raw.endswith("}}"):
            return (
                "warning",
                "runs-on is a dynamic expression; ensure the resolved "
                "value is a self-hosted label",
            )

        if lower in _ALLOWED_SELF_HOSTED:
            return "ok", "bare self-hosted"
        if any(lower.startswith(p) for p in _FORBIDDEN_PREFIXES):
            return (
                "error",
                f"hosted-runner label '{lower}' is not entitled on this org "
                "(see medinovai-infrastructure#1)",
            )
        # Any other bare label is probably a custom self-hosted label.
        return "ok", f"custom label '{lower}'"

    return "warning", f"unexpected runs-on shape: {type(runs_on).__name__}"


def _is_ignored(path: Path) -> bool:
    try:
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            head = [next(fh, "") for _ in range(20)]
    except OSError:
        return False
    return any("runner-policy: ignore" in line for line in head)


def _extract_jobs(doc: Any) -> dict[str, Any]:
    """
    Return the top-level ``jobs`` mapping for a workflow document.
    Tolerates reusable workflows that have no ``jobs`` key (pure
    ``on.workflow_call``).
    """

    if not isinstance(doc, dict):
        return {}
    jobs = doc.get("jobs")
    if not isinstance(jobs, dict):
        return {}
    return jobs


def lint_workflow(path: Path) -> list[Finding]:
    if _is_ignored(path):
        return []
    try:
        raw = path.read_text(encoding="utf-8")
        doc = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        return [
            Finding(
                workflow=str(path),
                job="<parse>",
                runs_on=None,
                level="error",
                reason=f"YAML parse failed: {exc}",
            )
        ]

    findings: list[Finding] = []
    for job_name, job_def in _extract_jobs(doc).items():
        if not isinstance(job_def, dict):
            continue
        # Jobs that are ``uses:``-only reusable-workflow calls have no
        # runs-on of their own — the runner is inherited from the called
        # workflow.
        if "uses" in job_def and "runs-on" not in job_def:
            continue
        runs_on = job_def.get("runs-on")
        if runs_on is None:
            findings.append(
                Finding(
                    workflow=str(path),
                    job=job_name,
                    runs_on=None,
                    level="error",
                    reason="no runs-on declared",
                )
            )
            continue
        level, reason = _classify(runs_on)
        if level != "ok":
            findings.append(
                Finding(
                    workflow=str(path),
                    job=job_name,
                    runs_on=runs_on,
                    level=level,
                    reason=reason,
                )
            )
    return findings


def lint_repo(repo: Path) -> Report:
    report = Report()
    wf_dir = repo / ".github" / "workflows"
    if not wf_dir.is_dir():
        return report
    for path in sorted(wf_dir.rglob("*.yml")) + sorted(wf_dir.rglob("*.yaml")):
        if not path.is_file():
            continue
        # Skip reusable-only templates living under workflows/templates/ —
        # they are intended to be called via `uses:` and cannot be
        # triggered directly; but we STILL lint them, because a hosted
        # label in a template wedges every consumer. (This matches what
        # happened to medinovai-core-platform/.github/workflows/templates/
        # python-service.yml.)
        report.workflows_scanned += 1
        report.findings.extend(lint_workflow(path))
    return report


def _format_text(report: Report) -> str:
    lines: list[str] = []
    lines.append(f"Scanned {report.workflows_scanned} workflow file(s).")
    if not report.findings:
        lines.append("PASS — all runs-on directives target allowed runners.")
        return "\n".join(lines)

    for f in report.findings:
        tag = "ERROR" if f.level == "error" else "WARN "
        lines.append(f"  [{tag}] {f.workflow}::{f.job}")
        lines.append(f"           runs-on = {f.runs_on!r}")
        lines.append(f"           reason  = {f.reason}")

    n_err = len(report.errors)
    n_warn = len(report.warnings)
    lines.append("")
    lines.append(f"Summary: {n_err} error(s), {n_warn} warning(s).")
    if n_err:
        lines.append(
            "FAIL — at least one hosted-runner label present. "
            "Replace with `[self-hosted, aifactory]` or see "
            "medinovai-infrastructure#1 for the platform-level tracker."
        )
    else:
        lines.append("PASS (with warnings).")
    return "\n".join(lines)


def _format_json(report: Report) -> str:
    return json.dumps(
        {
            "workflows_scanned": report.workflows_scanned,
            "findings": [f.as_dict() for f in report.findings],
            "errors": len(report.errors),
            "warnings": len(report.warnings),
        },
        indent=2,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo",
        default=".",
        help="Repository root to scan (default: cwd).",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    args = parser.parse_args(argv)

    repo = Path(args.repo).resolve()
    report = lint_repo(repo)

    out = _format_json(report) if args.format == "json" else _format_text(report)
    print(out)

    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
