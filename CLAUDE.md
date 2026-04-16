# CLAUDE.md - medinovai-infrastructure

## Purpose

Infrastructure - Helm, Terraform, deploy engine, monitoring, DevOps tooling

## Compliance Tier

- **Platform Tier:** Varies by service
- **Compliance Tier:** Varies by service (check each service.yaml)

## Repo Identity

| Field | Value |
|-------|-------|
| Repo | medinovai-infrastructure |
| Type | Monorepo |
| Domain | infrastructure |
| Language | Mixed (Python, TypeScript, C#) |
| Platform Standard | v2.1 |

## How to Run Tests

```bash
# Per-service tests
cd services/<service-name>
pytest  # Python
npm test  # Node.js
dotnet test  # C#
```

## Coding Conventions

- Constants: `E_VARIABLE` (uppercase, E_ prefix)
- Variables: `mos_variableName` (lowerCamelCase, mos_ prefix)
- Methods: max 40 lines
- Docstrings: Google-style on all public functions
- Type hints on ALL function parameters and returns
- Logging: structlog ZTA format (structured JSON)
- Encoding: UTF-8 everywhere

## Code Navigation — jCodeMunch (use instead of reading files)

All repos are pre-indexed by a background daemon. Use these MCP tools:

```
list_repos                                             → check indexed repos
search_symbols: { "repo": "<name>", "query": "..." }  → find functions/classes
get_symbol:     { "repo": "<name>", "symbol_id": "..." } → get exact source
get_repo_outline:   { "repo": "<name>" }               → repo structure
get_context_bundle: { "repo": "<name>", "symbol_id": "..." } → symbol + imports
```

Fall back to direct file reads only when editing. Zero cost — uses local Ollama.
