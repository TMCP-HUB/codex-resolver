---
name: web-performance-engineering
description: Diagnose and fix a measured or explicitly requested web performance bottleneck at the smallest justified layer. Use for slow pages, assets, network/API calls, database queries, rendering, background work, or performance monitoring.
---

# Web Performance Engineering

## Purpose

Select and implement performance improvements by an affected user-facing or technical claim, not by indiscriminately applying a long checklist.

## Goal

Improve the relevant latency, responsiveness, throughput, payload, or resource metric without compromising correctness, accessibility, data protection, user workflow, or approved architecture.

## When to use

Use when an Owner asks to optimize web performance, when a concrete slow path/regression is reported, or when an accepted performance claim must be implemented or diagnosed.

Do not invoke merely because a project contains a website, database, API, or cloud deployment. For architecture changes use existing implementation planning; for browser/interaction evidence use `webapp-dogfood-qa` as applicable. Visual design belongs to `design-system-authoring` and the selected UI craft skills; general causal debugging belongs to `systematic-debugging`.

## Inputs

- The known performance concern and affected route, request, query or user task
- Known baseline evidence (RUM, Core Web Vitals, logs, traces, query plans, waterfall, request counts, or explicit reproducible complaint), if available
- Existing stack, source ownership, data boundaries and delivery details only where relevant and available for the selected task
- Applicable non-regression obligations, such as SEO, privacy, accessibility, auth, freshness, consistency and budget
- Specific authorized scope, permitted change surface and target claims/evidence

## Execution contract

**Supported modes and required capabilities:**

| Mode | Mandatory capabilities | Evidence boundary |
|---|---|---|
| Advisory prioritization | Reasoning over supplied project facts and any available measurements | Conditional proposals, not an observed bottleneck or proven speedup |
| Source diagnosis | Relevant supplied files or authorized access to the selected source; exact-ref repository read when that remote state is the selected source; measurements when a measured diagnosis is claimed | Code-level risks and hypotheses; source alone cannot establish production latency |
| Source implementation | Authorized read/write access to the selected local or remote source and any runtime required by the assigned checks | Actual source changes and their observed checks, not a separate publication or measured benefit |
| Publication, when assigned | Authorized publication path and readback of the actual output at the selected destination | Published output and its applicable source checks, not automatically a measured benefit |
| Measured comparison, only when required by the actual claim | Access to the appropriate current browser, runtime, telemetry or data/query measurement surface, with relevant permissions | The specific baseline/after metric and tested conditions, not general performance guarantees |

**Conditional capabilities:** browser/devtools, backend telemetry, database plans, deployment and provider access, a build runtime, and test tools only when necessary for the selected claim. A GitHub/CI check may verify source correctness but cannot establish production response times. Reuse existing current measurements and checks; no default new tests, monitoring service, screenshot suite, profiler installation, queue, database or cache deployment.

**Unsupported environment:** Before dispatch, missing capabilities for a *mandatory* task step imply `ASSIGNMENT_NOT_ADMISSIBLE`; losing a previously proven capability implies `BLOCKED_RUNTIME_DRIFT` with the failing operation. Keep independent completed work. For an unobservable required outcome report `NOT_PROVEN`; never invent improvement numbers.

## Required outputs

The affected task and known bottleneck or hypothesis, relevant recommendations or changes with rationale, affected paths when source was changed, the published output or exact candidate reference when publication was assigned, relevant available evidence, applicable risks, and an honest PASS / PARTIAL / FAIL or NOT_PROVEN outcome for each claim.

## Procedure

1. **Bind scope.** Identify the known user-visible delay, cost or resource pressure and the authorized task. Do not retrofit the entire product to generic performance fashion.
2. **Distinguish observation from hypothesis.** Reuse relevant evidence; inspect the smallest relevant source path when source diagnosis is assigned and the source is available. Advisory work can use supplied facts without repository access. Label unmeasured candidate problems as hypotheses; do not invent a monitoring rollout.
3. **Locate the affected layer as evidence permits.** Separate delivery/assets, browser rendering, network/API, backend execution, database access and infrastructure. Trace only the affected path and keep unknowns explicit.
4. **Choose bounded remedies** from the decision guide below that address the actual task. Prefer suitable existing primitives; reject added infrastructure whose cost exceeds the evidenced benefit.
5. **Preserve affected semantics.** Assess the selected change against its applicable requirements, such as privacy, freshness, error handling, query correctness, accessibility and SEO; prove only the claims actually required.
6. **Implement only when assigned.** Use the authorized source path; publish and read back the output at the selected destination when publication is part of the task. Reuse applicable existing checks. New automation or a test is conditional on a demonstrated gap or explicit acceptance, not a consequence of touching performance.
7. **Validate the actual claim.** Source/CI can confirm code-level outcomes; a speedup or Core Web Vitals change needs comparable performance observations when required. Keep relevant measurement conditions and limitations explicit.

## Optimization decision guide

Select only relevant techniques; none is a universal mandate.

| Observed issue | Candidate method and important caveat |
|---|---|
| Slow or oversized images | Right-size assets; use supported WebP/AVIF with usable fallback where beneficial; lazy-load **below-the-fold** images, not the LCP/hero asset; avoid CLS with known dimensions |
| Perceived loading gap | Skeleton/placeholder only where it helps state comprehension; accessible loading states do not themselves reduce fetch time |
| Static delivery overhead | Existing CDN, correct immutable asset cache headers, browser caching and Brotli/Gzip as supported; inspect actual cache policy and private/public boundaries |
| Font/JS/third-party weight | Limit self-hosted font variants where legal and useful; remove truly unused code/dependencies; defer noncritical scripts; split or reduce JS while keeping necessary interaction |
| Rendering/SEO trade-off | Use SSR/SSG or semantic HTML projections where compatible with content freshness and existing stack; do not assume every interactive route benefits |
| Duplicate or stale client requests | Debounce user-typed search/autocomplete; deduplicate identical in-flight calls; cancel or disregard stale responses; respect explicit submit actions |
| Client interaction latency | Reduce avoidable re-renders; virtualize genuinely long lists; use optimistic updates only for safely reversible operations with rollback, conflict and server-authoritative confirmation |
| AI text latency | Stream output when the provider and UI support it and correct cancellation/error handling exists; don't claim every API can stream tokens |
| Slow API throughput | Set bounded timeouts and correct retry/idempotency rules; parallelize independent requests while respecting limits and dependencies; paginate large results using stable ordering/cursors |
| Repeated database work | Inspect actual query patterns/plans before indexes; eliminate evidenced N+1 calls, select needed columns and use appropriate joins/batches; balance index read gains with write costs |
| DB connection overhead | Use the actual platform's connection-management model; do not assume a traditional connection pool applies to a serverless database |
| Repeated expensive reads | Prefer existing caching layer (CDN, edge, KV or app cache) with explicit TTL/invalidation/privacy; Redis is **conditional**, never the default |
| Long-running noninteractive work | Move truly async jobs to an existing suitable queue when delivery, idempotency and result correlation can be preserved; don't queue synchronous confirmations |
| Saturation or network distance | Diagnose placement and capacity before moving runtime or adding replicas/load balancing; consider existing managed/platform scaling first |
| Unknown backend slowness | Use existing traces/logs/metrics first; add OpenTelemetry or equivalent instrumentation only to answer a real accepted measurement need |
| Unknown real-user experience | Use existing RUM/Core Web Vitals sources where available; add monitoring only when authorized and useful, with privacy/retention considered |

## Stack-sensitive defaults

For a Cloudflare Workers/D1/KV/Queues application, check the already-used provider capabilities before proposing Redis, a VM-side connection pool, another queue processor, a new reverse proxy or an extra load balancer. These are **engineering choices**, not blanket vendor restrictions. For other stacks, select their actual available primitives. Do not change the hosting architecture without the governing implementation decision.

## External methodology and ownership

- User-supplied web optimization checklist (2026-11-08) is a **menu of candidate optimizations**, not an instruction to implement all of them.
- [Matt Pocock's engineering skills](https://github.com/mattpocock/skills/tree/4ae2317ddb22b046e26455e4f9c9b3aaaf62212d/skills/engineering) inform constrained design/diagnosis/review methods, not a required TDD or agent orchestration pipeline.
- See [Software Engine external-method map](../../docs/EXTERNAL_SKILL_METHODS.md) for ownership and source references. Do not vendor or execute external skill libraries as a side effect.

## Anti-patterns

- Adding Redis, queues, OpenTelemetry, replicas or SSR because they appear in a checklist
- Optimistically confirming payments, bookings, lead creation or irreversible operations before the server
- Lazy-loading the first-screen hero/LCP asset or delaying a required user action behind skeletons
- Blindly adding indexes, changing query semantics, caching private data as public, or bypassing freshness
- Parallelizing dependent writes, retrying non-idempotent requests, or suppressing errors to boost metrics
- Claiming performance improvement from a green build without relevant measurement

## Verification checklist

- [ ] Affected task and baseline/observation boundary are explicit.
- [ ] Chosen remedies target the evidence or a clearly labeled hypothesis.
- [ ] Existing stack and Owner/Canon/architecture decisions are preserved.
- [ ] Safety, privacy, accessibility, SEO and consistency implications are checked where relevant.
- [ ] The actual result and relevant evidence are recorded; the published output is identified when publication was assigned, and measured gains are not invented.
- [ ] No unrelated dependencies, tests, infra or recurring monitoring were introduced.

## Minimal verdict format

- Bottleneck or hypothesis
- Selected remedies and scope
- Actual output, including published reference if assigned
- Evidence (source / existing CI / measured before and after, separately)
- Unproven claims and residual risks
- PASS / PARTIAL / FAIL / NOT_PROVEN
