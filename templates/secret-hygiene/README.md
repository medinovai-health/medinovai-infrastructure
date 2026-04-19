# Secret-Hygiene Template Kit

**Version:** 1 (2026-04-18)
**Owner:** `medinovai-infrastructure` · Security-Compliance Squad
**Related:** [`CyberSecurity#14`](https://github.com/medinovai-health/CyberSecurity/issues/14) (org-wide live-secret incident, April 2026).

## Why this kit exists

Between Oct 2025 and Apr 2026, five live API keys leaked across seven
`medinovai-health` repos:

| Key                                             | Entered repo via                       |
| ----------------------------------------------- | -------------------------------------- |
| OpenAI `sk-proj-yxGaT6a…`                       | Cursor agent **session logs** mirrored into `atlas-os`, `core-platform`, and a `zeroTouchMarketing` state backup |
| OpenAI `sk-proj-PvBHlM4Q…`                      | Committed `ATS/.env.production`        |
| OpenAI `sk-proj-H6IxpK7B…` + `NEXT_PUBLIC_` copy | Hardcoded in `Cognaium/scripts/create-env.js` — which also exposed the key to every browser via `NEXT_PUBLIC_OPENAI_API_KEY` |
| OpenAI `sk-proj-b_U9WLqT…`                      | `medinovaios/…/docker-compose.yml` `${VAR:-LIVE_KEY}` fallback |
| Anthropic `sk-ant-api03-q9bn944b…`              | Same `medinovaios` compose files       |
| MySQL password `Vikram@2024` + `Vikram@2004`    | Same Cognaium `create-env.js`          |

Every single one would have been stopped by this kit. This directory is the
org's **standard baseline** for new and existing repos.

## What's in this kit

| File                                    | Purpose                                                              | Install as                            |
| --------------------------------------- | -------------------------------------------------------------------- | ------------------------------------- |
| `gitignore.template`                    | Ignore `.env*`, agent session logs, cloud tokens, tfstate, etc.      | `.gitignore` (root of repo)           |
| `.pre-commit-config.yaml.template`      | gitleaks + detect-secrets + `.env` / session-log hooks (local)       | `.pre-commit-config.yaml` (root)      |
| `.gitleaks.toml.template`               | Shared gitleaks ruleset + MedinovAI-specific rules + allowlist       | `.gitleaks.toml` (root)               |
| `../../.github/workflows/secret-scan.yml` | Reusable GitHub Actions workflow (gitleaks + detect-secrets + SARIF) | Referenced from your repo's CI (see below) |

## Installing in an existing repo

```bash
# From the root of the target repo:
REPO="medinovai-health/medinovai-infrastructure"
BRANCH="main"
BASE="https://raw.githubusercontent.com/${REPO}/${BRANCH}/templates/secret-hygiene"

# 1. Baseline .gitignore (merge, do not overwrite, if you already have one).
curl -fsSL "${BASE}/gitignore.template" -o .gitignore.medinovai
# Review and merge into your existing .gitignore, then:
rm .gitignore.medinovai

# 2. Pre-commit hooks.
curl -fsSL "${BASE}/.pre-commit-config.yaml.template" -o .pre-commit-config.yaml
curl -fsSL "${BASE}/.gitleaks.toml.template"           -o .gitleaks.toml
pip install pre-commit
pre-commit install
pre-commit run --all-files   # expected: clean (or one-time findings to triage)

# 3. Bootstrap detect-secrets baseline.
pip install detect-secrets==1.5.0
detect-secrets scan > .secrets.baseline
# Then audit it so existing false positives don't fail CI:
detect-secrets audit .secrets.baseline

# 4. Wire the reusable CI workflow.
mkdir -p .github/workflows
cat > .github/workflows/security.yml <<'YAML'
name: Security
on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: "0 5 * * *"   # nightly full-history scan

permissions:
  contents: read
  security-events: write

jobs:
  secrets:
    uses: medinovai-health/medinovai-infrastructure/.github/workflows/secret-scan.yml@main
    with:
      fetch_depth: ${{ github.event_name == 'schedule' && 0 || 1 }}
      upload_sarif: true
YAML

git add .gitignore .pre-commit-config.yaml .gitleaks.toml .secrets.baseline \
        .github/workflows/security.yml
git commit -m "security: adopt MedinovAI org-wide secret-hygiene baseline"
```

## Installing in a new repo

`medinovai-deploy` and `medinovai-developer` (the template / scaffolder repos)
should emit all four files automatically at repo-creation time. See
`medinovai-infrastructure#2` for tracking.

## Tuning for false positives

Central rules live in `.gitleaks.toml.template` here. Prefer fixing **here**
(org-wide allowlist) over silencing a finding repo-locally, so every repo
benefits. Open a PR against this file with:

- the specific finding (redacted) and the pattern you want to allow,
- why it is not a real secret (e.g. test fixture, sample data),
- the smallest possible `allowlist` change.

For repo-local allowlisting — only when the finding is truly repo-specific —
append to the repo's own `.gitleaks.toml` below the `# === repo-specific
overrides ===` marker (add the marker if missing).

## What still needs to happen org-wide

- [ ] Enable **GitHub Advanced Security → Secret Scanning** and **Push
      Protection** on every `medinovai-health` repo (org-wide policy).
- [ ] Deploy this kit into the `medinovai-deploy` + `medinovai-developer`
      templates so it ships with every new repo by default
      (tracked: `medinovai-infrastructure#2`).
- [ ] Backfill adoption across the existing 192+ repos, prioritising:
      `ATS`, `Cognaium`, `medinovaios`, `atlas-os`, `core-platform`,
      `zeroTouchMarketing` — all implicated in `CyberSecurity#14`.
- [ ] `git filter-repo` sweep to purge the already-leaked keys from each
      repo's history (separate effort per repo; see `CyberSecurity#14`
      action items).

## Escalation

If this kit blocks a legitimate workflow or produces a false positive you
cannot resolve with the patterns above, file an issue on
`medinovai-infrastructure` with the `security-hygiene` label.
