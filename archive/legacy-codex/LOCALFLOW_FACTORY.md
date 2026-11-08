# LocalFlow Factory

## Philosophy

Do not build one super-agent.

Build a repository-native development factory:

- agents
- skills
- artifacts
- contracts
- QA
- review
- browser evidence
- deterministic workflows

## Minimal stack

### Core executor

- Codex

### Architecture and review

- Claude Code

### Repository law

- AGENTS.md

### Skills and workflows

- `.agents/skills/`

### Durable state

- `artifacts/`

### Browser verification

- Playwright dogfood harness

### Docs and live API context

- Context7
- allowlisted MCP

## Recommended MCP

Only allowlisted MCP servers:

- GitHub
- Filesystem
- Context7
- Postgres
- Cloudflare
- Browser/Puppeteer

## Recommended architecture

```text
Laravel core
  ↓
Filament admin
  ↓
Queues / Horizon
  ↓
Cloudflare edge runtime
  ↓
Public sites / QR / redirects / tracking
```

## Laravel contract-first architecture

The database, API, frontend, admin panel, and Cloudflare runtime must share contracts.

Do NOT:

```text
invent frontend interfaces first
then try to attach backend later
```

Instead:

```text
business rules
  ↓
database schema
  ↓
DTO / request / resource
  ↓
API contract
  ↓
generated frontend types
  ↓
UI implementation
```

## Laravel source-of-truth rules

Laravel owns:

- orgs
- users
- billing
- ledgers
- permissions
- audit trail
- integrations
- AI orchestration
- queues
- admin operations

Cloudflare consumes runtime-safe subsets.

## Required backend contracts

Important systems should maintain:

```text
DATABASE_CONTRACT.md
API_CONTRACT.md
UI_BINDING_CONTRACT.md
SCHEMA_DRIFT_CHECK.md
```

## Frontend type rules

Avoid manually inventing interfaces for server-owned data.

Prefer:

- OpenAPI-generated types
- DTO-generated types
- schema-generated types
- explicit drift checks

## Database rules

Every important table should define:

- keys
- indexes
- constraints
- tenant boundaries
- audit strategy
- deletion strategy
- timestamp policy

Money should never use float types.

## Filament rules

Filament is the operational control plane.

It should expose:

- audit history
- org management
- queue state
- billing review
- fraud review
- AI usage
- payouts
- support tools

Sensitive operations require:

- permissions
- confirmations
- activity logs

## Cloudflare rules

Cloudflare should handle:

- redirects
- QR runtime
- public tracking
- CDN/cache
- browser rendering
- public edge APIs

Cloudflare should NOT become:

- the ledger database
- the permission system
- the billing source-of-truth
- the primary org/user system

## Agent roles

| Role | Main responsibility |
|---|---|
| Planner | scope and contracts |
| Implementer | code changes |
| QA | browser and flow verification |
| Reviewer | operational and security review |
| Auditor | system-level analysis |
| Docs | operational documentation |

One model may perform multiple roles.
Artifacts must still separate them.

## Conveyor workflow

```text
Task
  ↓
PLAN
  ↓
Implementation
  ↓
Dogfood QA
  ↓
REVIEW
  ↓
Merge
  ↓
HANDOFF / CHRONICLE
```

## Cloudflare usage philosophy

Cloudflare should NOT become the entire backend.

Use Cloudflare for:

- edge runtime
- redirects
- tracking
- CDN
- cache
- browser rendering
- public runtime
- lightweight APIs

Keep durable business logic in Laravel.

## Laravel usage philosophy

Laravel handles:

- billing
- auth
- audit
- queues
- orgs
- permissions
- AI orchestration
- integrations
- admin systems

## Filament philosophy

Filament is not a toy admin.

Use it as:

- operational console
- audit viewer
- fraud review
- payout management
- queue monitor
- support dashboard
- AI usage control plane

## Skills philosophy

Skills are:

- reusable
- reviewable
- composable
- token-efficient

Avoid giant prompts.
Use progressive disclosure.

## Cost governance

Always optimize:

- selective skill loading
- artifact-based context
- diff-based review
- small plans
- small PRs
- cheap models for simple work
- expensive models only for architecture/review

## Anti-patterns

Avoid:

- autonomous production deploys
- giant agent swarms
- one huge AGENTS.md
- random MCP installs
- mixing planning/review/QA into one step
- Cloudflare-only monoliths
- vibe-coding without artifacts or verification
