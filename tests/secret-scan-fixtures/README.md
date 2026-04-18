# Secret-Scan Verification Fixtures

> **Do not copy these files into any other repo.**
> They exist *only* to prove the reusable \`secret-scan.yml\` workflow actually
> catches the leak shapes we care about. If the self-test job goes green when
> one of these files is present, the ruleset is regressing and needs to be
> fixed in `templates/secret-hygiene/.gitleaks.toml.template` **before** any
> further adoption PR is merged.

## What's in here

| File                          | Pattern it asserts                                                  |
| ----------------------------- | ------------------------------------------------------------------- |
| `leak-openai-project.txt`     | `sk-proj-…` key body (caught by `medinovai-openai-project-key`)     |
| `leak-anthropic.txt`          | `sk-ant-api03-…` key body (caught by `medinovai-anthropic-key`)     |
| `leak-next-public.env`        | `NEXT_PUBLIC_OPENAI_API_KEY=…` (caught by `medinovai-next-public-secret`) |
| `leak-hardcoded-mysql.yml`    | `MYSQL_PASSWORD=…` hardcoded value (caught by `medinovai-hardcoded-mysql-password`) |
| `leak-session-log.jsonl`      | file path inside `**/session-logs/` containing a key (caught by path rule + ignore) |
| `allowlist-placeholder.env`   | `REPLACE_ME` / `REDACTED_*` — must **not** be flagged (allowlist proof) |

## How the harness uses these

The workflow
[`.github/workflows/secret-scan-selftest.yml`](../../.github/workflows/secret-scan-selftest.yml)
runs **twice** on every PR to this repo:

1. With all fixtures present → gitleaks **must** exit non-zero (findings).
2. With only the allowlist fixture present → gitleaks **must** exit zero.

If either assertion flips, the self-test fails and the PR cannot merge.

## Why the fixtures use obviously-fake values

The keys in these files are deliberately malformed (wrong length, invalid
base64, etc.) so they cannot be real credentials while still matching our
regex rules. This lets the fixtures live safely in a public-ish repo and
survive detect-secrets' own entropy check without triggering GitHub's push
protection.
