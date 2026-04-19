# medinovai-infrastructure

MedinovAI shared GitHub Actions reusable workflows and infrastructure templates.

## Contents

| Path                                                     | What it is                                                                                              |
| -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| [`.github/workflows/deploy-to-aifactory.yml`](.github/workflows/deploy-to-aifactory.yml) | Reusable workflow: deploy a service to the AIFactory MacStudio via Tailscale.         |
| [`.github/workflows/secret-scan.yml`](.github/workflows/secret-scan.yml) | Reusable workflow: org-wide secret scanning (gitleaks + detect-secrets + SARIF upload). |
| [`templates/secret-hygiene/`](templates/secret-hygiene/README.md) | Org-wide **secret-hygiene kit**: `.gitignore`, gitleaks config, pre-commit config. **Every MedinovAI repo should adopt this.** |
| [`PLATFORM_ALIGNMENT.md`](PLATFORM_ALIGNMENT.md)         | How this repo fits into the MedinovAI 5-tier platform architecture.                                     |
| [`CLAUDE.md`](CLAUDE.md)                                 | Agent context for this repo.                                                                            |

## Security / secret hygiene

After the April 2026 live-key incident (`CyberSecurity#14`, five distinct
live API keys across seven repos), the org baseline for preventing secret
leaks lives in [`templates/secret-hygiene/`](templates/secret-hygiene/README.md).
Every `medinovai-health` repo should:

1. Copy the four template files into the repo root.
2. Reference the reusable `secret-scan.yml` workflow from its own CI.
3. Enable **GitHub Advanced Security → Secret Scanning + Push Protection**
   at the repo level.

See the [kit README](templates/secret-hygiene/README.md) for the exact
bootstrap steps.
