# Runner Policy Fixtures

Deliberately-constructed GitHub Actions workflow fixtures used by
`.github/workflows/workflow-lint-selftest.yml` to verify that the
`lint-workflow-runners.py` linter:

1. **flags** every forbidden hosted-runner shape we've seen in the wild;
2. **accepts** every self-hosted / reusable-workflow shape we actually use;
3. **honours** the `# runner-policy: ignore` opt-out marker.

## Layout

| Path | Expectation |
| --- | --- |
| `forbidden/ubuntu-latest.yml` | String form `ubuntu-latest` → ERROR |
| `forbidden/macos-13.yml` | String form `macos-13` → ERROR |
| `forbidden/windows-in-list.yml` | List form containing `windows-latest` → ERROR |
| `allowed/aifactory-list.yml` | Canonical `[self-hosted, aifactory]` → PASS |
| `allowed/reusable-caller.yml` | `uses:` with no `runs-on` → PASS (inherited runner) |
| `ignored/legacy-ubuntu.yml` | `ubuntu-latest` + `# runner-policy: ignore` → PASS |

## Why this is a test suite and not just a set of examples

These fixtures are **asserted against** in CI. If a future change to the
linter accidentally stops catching `ubuntu-latest`, the self-test goes
red. Without that assertion, the linter could silently regress and every
downstream repo would quietly drift back to the exact silent-CI-failure
bug this kit was built to prevent (see
[`medinovai-infrastructure#1`](https://github.com/medinovai-health/medinovai-infrastructure/issues/1)).
