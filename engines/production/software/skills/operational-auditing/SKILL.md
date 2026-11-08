---
name: operational-auditing
description: Perform risk-scoped operational diagnosis of repositories, services, workflows and deployments. Use only categories applicable to the actual system and claim.
---

# Operational Auditing

## Purpose

Use this skill to audit a repository, deployment, workflow, or application for operational risk.

## Goal

Find hidden breakage, unsafe assumptions, missing verification, workflow drift, security leaks, deployment mistakes, or incomplete integrations before they become production failures.

## When to use

Use this skill when:

- onboarding into a repository
- reviewing an AI-generated codebase
- preparing deployment
- inheriting a project
- validating a contractor or agent contribution
- checking workflow maturity
- auditing platform or version-control setup actually used by the target

## Inputs

Exact audit target/ref, requested operational claims, existing authoritative decisions, applicable repository/config/runtime evidence, affected failure boundaries, actual access capabilities and non-goals. Do not request secret values.

## Execution contract

- **Source mode:** inspect only the relevant exact repository files, existing CI/PR and operational documents via an authorized repository reader. This can prove source/config claims, not live deployment.
- **Local mode (when required):** a selected local checkout/worktree, shell and actual runtime/dependencies for necessary commands. A repository-only review is not equivalent to an unexecuted build.
- **Provider/deployed mode (only when required):** scoped provider/HTTP/browser read capability and relevant credentials for the claimed live endpoint or UI; an authorized write or production operation requires separate explicit authority.
- **Evidence:** match every finding to a source ref, existing check or observed provider/runtime identity. No universal build, browser QA, new test, deployment or third-party account audit is mandated.
- **Unsupported environment:** missing mandatory capability at assignment is `ASSIGNMENT_NOT_ADMISSIBLE`; lost proven access during execution is `BLOCKED_RUNTIME_DRIFT`. Return `NOT_PROVEN` for unavailable claims, not an invented defect or substitute observation.

## Audit categories

First classify the actual product and requested claims (library, job, API, UI, pipeline, agent, deployed service, etc.), supported runtime, critical side effects and authorized evidence. Apply only relevant categories, not every table row.

| Category | Check when relevant |
|---|---|
| Ownership and boundaries | Canonical data/actions, identity, trust edges and provider coupling |
| Source and build | Exact candidate, dependency and build reproducibility when executable |
| Runtime and delivery | Service/process lifecycle, deployment drift, configuration and credentials |
| State and recovery | Persistence guarantees, backup/recovery, destructive actions and uncertain writes |
| Integrations | API compatibility, auth, limits, timeouts, retries, readback |
| Interaction | Browser, mobile, accessibility and user flows **only for an actual UI** |
| Observability | Signals proportional to defined operational risk, not mandatory analytics |
| Operating instructions | Current recovery and existing commands for the chosen stack |
| Delivery control | Existing Issue/PR, authorizations and evidence integrity when in scope |

Cloudflare, forms, CRM, PostHog, npm and Playwright are examples for matching systems, **never generic prerequisites**.

## Audit scoring

| Score | Meaning |
|---|---|
| Critical | Immediate production or security risk |
| High | Serious operational weakness |
| Medium | Important but survivable issue |
| Low | Cleanup or polish item |

## Procedure

1. Freeze the audit claim and exact target; identify runtime, interaction, state and integration risks that actually exist.
2. Read only relevant source, current evidence, configuration and governing decisions; avoid repository-wide scanning without reason.
3. Compare observations with applicable requirements and official versioned documentation where needed; separate evidence from assumptions.
4. Reuse relevant existing checks/CI. Verification does not itself authorize creating new tests, screenshot harnesses or deployments.
5. Report actionable scoped findings with evidence and severity; unobserved live behavior is NOT_PROVEN, not automatically broken.

## Auditor-to-Executor continuity (Stage 1)
- An operational audit is an authorized **diagnostic Executor phase**, not a permanent universal Auditor role or independent Verification. This skill may be used in the existing Software diagnosis/review workflow with actual admitted observation capabilities.
- Finish the audit with evidence-bound findings, original exact GitHub candidate/base, risks and recommendations before any implementation transition. Findings alone do not authorize their repair.
- Director/Owner selects approved remedies and issues a separate compiled/admitted implementation Assignment. The same Codex/Chat executor instance may continue with the bounded audit context; independent Verification of its implementation must be done by another instance wherever required.
- Do not turn a self-audit into an architecture decision, immediate self-repair mandate, independent acceptance or self-merge. Retain auditable findings in the declared durable system of record.

## Required outputs

- Executive summary
- Applicable categories reviewed, with material exclusions explained
- Findings by severity, if any
- Evidence
- Recommended fixes
- Operational maturity verdict

## Verification checklist

- [ ] The reviewed categories are relevant to the actual product and authorized audit claim.
- [ ] Each material finding has source or observed evidence and a bounded severity.
- [ ] Source-only observations are not presented as deployed/runtime proof.
- [ ] No unrelated tests, external systems, code changes or Owner gates were introduced by the audit.

## Anti-patterns

Avoid:

- generic security theater
- pretending coverage exists when it does not
- praising style while ignoring operational risk
- massive architecture rewrites without justification
- auditing only code and ignoring workflows
