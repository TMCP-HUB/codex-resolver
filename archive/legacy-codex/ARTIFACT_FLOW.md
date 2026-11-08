# Artifact Flow

This repository uses artifact-driven agent workflows.

Agents should communicate through durable artifacts instead of relying on chat memory.

## Goal

Make development:

- reproducible
- reviewable
- resumable
- multi-agent compatible
- token efficient

## Core principle

An agent should not say work is complete.

An artifact should prove the state.

## Artifact lifecycle

```text
PLAN
  ↓
IMPLEMENTATION
  ↓
QA
  ↓
REVIEW
  ↓
MERGE
  ↓
HANDOFF / CHRONICLE
```

## Artifact directories

```text
artifacts/
  plans/
  qa/
  reviews/
  audits/
  spikes/
  handoffs/
  chronicle/
```

## Standard artifacts

| Artifact | Producer | Consumer |
|---|---|---|
| PLAN.md | planner | implementer |
| QA_REPORT.md | qa agent | reviewer |
| REVIEW.md | reviewer | merge manager |
| AUDIT.md | auditor | architect |
| SPIKE_REPORT.md | spike agent | planner |
| HANDOFF.md | current session | future session |
| CHRONICLE.md | architect/lead | entire team |

## Agent role contracts

### Planner

Produces:

- scope
- constraints
- phases
- verification
- acceptance criteria

Must not:

- implement production code
- approve its own plan

### Implementer

Consumes:

- PLAN

Produces:

- code
- evidence
- implementation notes

Must not:

- approve its own merge
- silently change scope

### QA

Consumes:

- PLAN
- diff
- preview environment

Produces:

- QA report
- screenshots
- traces
- console/network evidence

Must not:

- rewrite architecture
- merge code

### Reviewer

Consumes:

- diff
- QA
- verification evidence

Produces:

- review verdict
- blockers
- warnings

Must not:

- silently rewrite unrelated code

## Single-agent mode

Even with one agent:

- keep artifacts separate
- separate planning from implementation mentally
- separate QA from implementation
- separate review from implementation

The same model can perform multiple roles, but artifacts must still exist.

## Verification hierarchy

Strongest evidence first:

1. tests
2. build/typecheck/lint
3. Playwright/browser evidence
4. logs and traces
5. screenshots
6. manual notes
7. claims without evidence

## Token efficiency rules

- load only relevant skills
- load only current artifacts
- avoid loading entire histories
- summarize stale artifacts into chronicles
- use progressive disclosure

## MCP rules

Allowlisted MCP only.

Recommended:

- GitHub
- Filesystem
- Context7
- Postgres
- Cloudflare
- Browser/Puppeteer

Avoid unrestricted marketplace installs.

## Safety boundaries

No autonomous:

- production deploy
- billing mutation
- payout execution
- irreversible migration
- secret rotation
- merge to protected branch

without explicit human approval.
