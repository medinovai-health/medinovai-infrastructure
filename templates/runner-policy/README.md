# Runner Policy Kit

Org-wide runner-policy lint for the `medinovai-health` GitHub organization.

## Why this exists

The `medinovai-health` org has **no entitlement to GitHub-hosted runners**.
The org has exactly one runner pool:

    [self-hosted, aifactory, ...]   # macOS / ARM64

Any workflow job declaring `runs-on: ubuntu-latest` (or any other hosted
label — `macos-*`, `windows-*`) sits in the runner-assignment queue for ~7
seconds and then auto-fails with:

```
runner_id: 0
runner_name: ""
steps: []
conclusion: "failure"
```

That failure shape is **indistinguishable from a real test regression** and
has hidden weeks of silent CI breakage across the org (the root-cause report
is [`medinovai-infrastructure#1`](https://github.com/medinovai-health/medinovai-infrastructure/issues/1)).

This kit prevents new workflows from landing with that bug.

## Contents

| File | Purpose |
| --- | --- |
| `lint-workflow-runners.py` | Static linter for `runs-on` directives. Run locally or in CI. |
| `workflow-lint.template.yml` | Consumer workflow — copy into any repo's `.github/workflows/`. Delegates to the reusable workflow in this repo. |
| `README.md` | This file. |

The reusable workflow itself lives at
[`.github/workflows/workflow-lint.yml`](../../.github/workflows/workflow-lint.yml)
in this repository.

## Behaviour

The linter walks `./.github/workflows/*.{yml,yaml}` in the consumer repo and
inspects every job's `runs-on`. It classifies each value as:

| Shape | Decision |
| --- | --- |
| `[self-hosted, aifactory]` or any list containing `self-hosted` | **PASS** |
| bare `self-hosted` | **PASS** |
| any other bare custom label (e.g. `my-gpu-runner`) | **PASS** |
| `ubuntu-*`, `macos-*`, `windows-*` (string or in list) | **FAIL** |
| `${{ ... }}` dynamic expression | **WARN** (can't be statically proven safe) |
| no `runs-on` at all, and no `uses:` | **FAIL** |
| reusable-workflow job (`uses:` with no `runs-on`) | **SKIP** (runner inherited) |

A workflow file can opt out by including `# runner-policy: ignore` within its
first 20 lines. Use sparingly, and document the reason.

## Adoption

### Method 1: use the reusable workflow (recommended)

Copy `workflow-lint.template.yml` into your repo's `.github/workflows/` as
`workflow-lint.yml`. No other changes required — the workflow pulls the
script on each run, so you always get the latest policy.

### Method 2: run the linter locally / in a bespoke CI

```bash
curl -fsSL \
  https://raw.githubusercontent.com/medinovai-health/medinovai-infrastructure/main/templates/runner-policy/lint-workflow-runners.py \
  -o /tmp/lint-workflow-runners.py

python3.12 -m venv .lint-venv
.lint-venv/bin/pip install pyyaml==6.0.2
.lint-venv/bin/python /tmp/lint-workflow-runners.py --repo .
```

Exit code `1` means violations are present.

## Observability mode

Set `fail_on_findings: false` when calling the reusable workflow. The check
still runs and reports findings in the run summary, but it no longer blocks
the PR. Useful during bulk migrations.

## Related work

* [`medinovai-infrastructure#1`](https://github.com/medinovai-health/medinovai-infrastructure/issues/1) — platform-level tracker (requests hosted runners or an amd64 Linux self-hosted runner).
* `medinovai-health/CyberSecurity` PR #10 — per-repo workaround demonstrating the migration pattern on a governance repo.
* `medinovai-health/medinovai-core-platform` PR #22 — migrates reusable service templates (Python/Node/C#) off `ubuntu-latest`, unwedging every `services-*` check in that monorepo.
