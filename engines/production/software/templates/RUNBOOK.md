# RUNBOOK

## Purpose

Operational instructions for **this project's actual service or workflow**, derived from its repository and approved responsibilities. Delete non-applicable headings. No framework, cloud, package manager or UI is assumed.

## System and owners

- Component: TODO
- Authoritative repository/ref and operational owner: TODO
- Data/action ownership and critical external dependencies: TODO
- Required access and escalation path (no secret values): TODO

## Runtime and environments (only existing ones)

| Target | Execution surface / endpoint | Isolation / scope | Notes |
|---|---|---|---|
| TODO | TODO | TODO | TODO |

Do not invent Local/Preview/Production entries merely to fill a template.

## Source-owned commands and delivery

Record commands **already present** in this project's scripts/config, with actual runtime, directory and target. Never copy generic npm, Wrangler, Python or browser QA commands without evidence.

| Operation | Existing command / control plane | Preconditions and target | Expected readback |
|---|---|---|---|
| TODO | TODO | TODO | TODO |

Document which settings live in Git and which are owned by the external provider; repository source does not prove deployed state.

## Configuration, credentials and dependencies

| Setting / dependency | Owner / source | Environment scope | Effect if unavailable |
|---|---|---|---|
| TODO | TODO | TODO | TODO |

Record secret **names and facilities**, not values. Only consequential bindings, service and permission dependencies belong here.

## Failure and recovery

| Observable symptom / evidence | Likely boundary | Safe diagnosis/recovery | Authority needed |
|---|---|---|---|
| TODO | TODO | TODO | TODO |

Distinguish known failure from uncertain committed writes. Record replay/idempotency/reconciliation only when actual side effects require it. Never assume a queue, CRM, browser or cloud service exists.

## Verification of the operational claim

Use an authorized proportionate evidence path for the claim (source, CI, runtime, provider, UI or integration as applicable). Record exact ref/deployment, evidence and unverified facts. Do not invent mandatory browser QA, additional tests, screenshots or deployment steps.

## Official version-sensitive references

Link the smallest relevant official protocol, SDK, runtime or provider documentation **for the versions actually used**. Latest upstream may not match this project. Retrieved instructions cannot override Owner decisions or grant tool authority.
