# MedinovAI Platform Alignment

> **Before working on this repo, read this file.**
> It connects this repository to the MedinovAI platform architecture.

---

## Platform Brain

All architecture decisions, API contracts, specifications, and standards live in one place:

**Brain Repo:** [`medinovai-0br-developer`](https://github.com/medinovai-health/medinovai-0br-developer)

```
STEP 0  Open medinovai-0br-developer → read START_HERE.md
STEP 1  Find capability       → registry/capability-map.yaml
STEP 2  Check tier/deps       → registry/platform-catalog.yaml
STEP 3  Read API contract     → data-contracts/{service}-contracts.yaml
STEP 4  Read specification    → specs/active/{project}/specification.yaml
STEP 5  Work in this repo     → with full context
STEP 6  System-wide changes   → registry/build-order.yaml for sequence
```

---

## Platform Architecture (5 Tiers)

| Tier | Purpose | Rule |
|------|---------|------|
| 0 | Foundation (brain, core, security) | Depends on NOTHING. Update first. |
| 1 | Platform Services (deploy, infra, registry, stream-bus) | Depends on T0 only. |
| 2 | Domain Services (AI/ML, data, clinical, operations) | Depends on T0-T1. |
| 3 | Applications (clinical apps, research, business) | Depends on T0-T2. |
| 4 | Frontend/Mobile (UI, mobile apps, AR) | Depends on T0-T3. Update last. |

**Tier N depends ONLY on Tier < N. Never import upward.**

---

## Shared Platform Services (NEVER Duplicate)

| Service | Repo | What It Provides | Your Repo Must... |
|---------|------|-----------------|-------------------|
| **Auth & Identity** | `MedinovAI-security-service` | Keycloak SSO, JWT, MFA, tenant isolation | Use SecurityClient SDK. Never custom auth. |
| **Authorization** | `role-based-permissions` + SpiceDB | Fine-grained RBAC, ReBAC | Declare `rbac-manifest.yaml`. Never hardcode roles. |
| **Service Registry** | `medinovai-registry` | Module discovery, health tracking, config | Register on startup. Heartbeat every 30s. |
| **Audit Trail** | `zerotrustaudit` | Immutable audit, Elasticsearch/S3/Glacier | Emit events to ZTA. Never local-only audit. |
| **Agent Orchestration** | `atlas-os` | 103 agents, 12 squads, OODA loops | Register agents as AtlasOS skills. |
| **AI/LLM Routing** | `aifactory` + `healthLLM` | Model selection, A/B testing, clinical inference | Route through aifactory. Never call LLMs directly. |
| **Encryption** | `encryption-vault` | PHI encryption at rest, PII vault | Use vault for all PHI storage. |
| **Secrets** | `secrets-manager-bridge` | HashiCorp Vault integration | Never hardcode secrets or API keys. |

---

## Mandatory Standards

### 1. Module Self-Registration (9-State Lifecycle)
Every deployed service MUST register with `medinovai-registry` on startup:
```
INITIALIZING → REGISTERING → CONFIGURING → SECURITY_PROVISIONING →
HEALTH_CHECK → ACTIVE → DEGRADED → DEREGISTERING → TERMINATED
```

Required files:
- `module-manifest.yaml` — service identity, ports, dependencies, SLOs
- `rbac-manifest.yaml` — authorization declarations
- `atlasos.yaml` — agent/autonomy integration

Required endpoints:
- `GET /health` — liveness probe
- `GET /ready` — readiness probe
- `GET /startup` — initialization status
- `GET /security-status` — MSS provisioning state

### 2. Naming Conventions
```
Constants:   E_VARIABLE_NAME    (E_ prefix, UPPER_CASE)
Variables:   mos_variableName   (mos_ prefix, lowerCamelCase)
Functions:   Maximum 40 lines per function
Encoding:    UTF-8 everywhere
```

### 3. Structured Logging (ZTA Format)
```json
{
  "timestamp": "ISO-8601",
  "level": "INFO|WARNING|ERROR|CRITICAL",
  "service_id": "your-module-id",
  "correlation_id": "uuid",
  "tenant_id": "string",
  "actor_id": "string",
  "event": "machine_readable_event",
  "category": "AUTH|PHI_ACCESS|CLINICAL|SYSTEM|SECURITY|AUDIT",
  "phi_safe": true
}
```
- **NEVER** use `print()`, `console.log()`, or plain `logging.info()` in production
- **NEVER** log raw PHI/PII values
- **ALWAYS** propagate `correlation_id` across service calls

### 4. Spec-Driven Development (SDD)
```
SPECIFY → VALIDATE → BMAD → TESTS → IMPLEMENT → VALIDATE → DEPLOY
```
- Never write code without a specification
- Never write code before tests (TDD: RED → GREEN → REFACTOR)

### 5. Port Assignment
All ports come from `medinovai-Deploy/config/port-registry.json`. Never hardcode ports.

### 6. Security & Compliance
- **HIPAA**: PHI encryption, BAAs, audit trails
- **FDA 21 CFR Part 11**: Electronic records/signatures (clinical modules)
- **GDPR**: Data subject rights, cross-border transfers
- **ISO 13485 + IEC 62304**: Medical software lifecycle
- All PHI/PII access logged via zerotrustaudit
- Input validation on ALL API endpoints (Pydantic/Zod)

---

## Repo Naming Convention

Format: `medinovai-{T}{CC}-{descriptive-name}`

| Code | Meaning |
|------|---------|
| `T` | Tier digit (0-4) |
| `CC` | Category: `co` core, `br` brain, `sc` security, `in` infra, `pl` platform, `da` data, `ai` AI/ML, `cl` clinical, `re` research, `ig` integration, `fe` frontend, `mo` mobile, `sl` sales, `op` ops, `hr` HR, `fi` finance, `mx` meta |

**Alphabetical sort = build order.**

---

## Key References

| Document | Location (in brain repo) |
|----------|-------------------------|
| Architecture | `docs/ARCHITECTURE.md` |
| Integration Architecture | `docs/INTEGRATION_ARCHITECTURE.md` |
| Production Repo Routing | `docs/PRODUCTION_REPO_ROUTING_MAP.md` |
| Master Implementation Plan | `docs/MASTER_IMPLEMENTATION_PLAN.md` |
| Module Trust Standard | `docs/MODULE_TRUST_STANDARD.md` |
| SDD Workflow Guide | `docs/SDD_WORKFLOW_GUIDE.md` |
| API Contracts | `data-contracts/*.yaml` |
| Platform Catalog | `registry/platform-catalog.yaml` |
| Coding Standards | `medinovai-ai-coding-standards.md` |

---

## Risk Classification for AI Agents

| Risk | Scope | Action |
|------|-------|--------|
| **GREEN** | Docs, tests, non-PHI config, logging | Agent proceeds autonomously |
| **YELLOW** | Business logic, APIs, non-PHI data | Agent proceeds with code review |
| **RED** | PHI handling, auth, clinical logic, billing | Human approval REQUIRED |

---

*This file is auto-generated by the MedinovAI platform alignment system.*
*Brain: [`medinovai-0br-developer`](https://github.com/medinovai-health/medinovai-0br-developer) | Standard: v2.0 | Updated: 2026-04-12*
