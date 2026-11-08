---
name: provider-late-binding
description: Use a provider-neutral seam and a fake when staged provider integration fits the actual feature and claim.
---

# Provider Late Binding

> Classification: **Solution Pattern — optional**. This is one way to keep an external provider from becoming the first dependency of a feature. It is useful when deterministic integration can be proven behind a provider-neutral seam, but it is not a rule that every third-party integration must be added last.

## Problem class

A feature depends on an external provider—CAPTCHA, payment, identity, SMS, email, storage, AI, maps, or another service—but most application semantics can be developed and tested without the live provider. Integrating the real provider too early can make business/runtime debugging inseparable from credentials, network behavior, provider UI, rate limits, and environment-specific configuration.

## Production trace

This pattern came from a human-verification entry flow where the application contract, consent boundary, session behavior, test traversal, and failure semantics could all be proven through a provider-neutral seam before the live verification widget/script/network/secret was enabled in production.

## Assumptions

- the application can define a provider-neutral contract around the external capability;
- a deterministic fake/test implementation can reproduce the outcomes needed for most integration work;
- the real provider adds operational/network/UI behavior beyond the core domain contract;
- evidence for an actual provider claim will require the appropriate real provider observation when that claim is within the accepted scope; a fake-stage result can be complete on its own.

## Use when

Use when:

- external provider credentials are unavailable or undesirable in ordinary CI;
- provider UI/network behavior would make early debugging noisy;
- most application logic depends on provider outcomes, not provider internals;
- you want a deterministic full-flow soak before enabling production-only integration;
- switching providers later is a realistic possibility.

## Do not use when

Integrate the real provider earlier when:

- provider behavior fundamentally defines the product workflow;
- the provider API itself is the unknown risk being investigated;
- no realistic fake can exercise critical semantics;
- compliance/certification requires the live provider throughout development;
- provider-specific latency, callback ordering, redirects, or embedded UI are central to architecture.

## Pattern

### 1. Define the capability seam first

Model what the application needs, for example:

```text
verifyHuman(challengeContext) -> verified / rejected / unavailable
```

or

```text
capturePayment(command) -> accepted result / declined / uncertain
```

Do not expose provider SDK objects throughout the domain/application layer unless necessary.

### 2. Implement a deterministic test provider

The fake should support the meaningful outcome classes, including failures.

Examples:

- success;
- explicit rejection;
- transient unavailable;
- timeout/uncertain result where relevant;
- malformed provider response if the adapter must handle it.

A fake or stub is a valid completed deliverable when that is the accepted stage. Evidence from it can establish only the exercised application contract around its simulated outcomes; it does not prove a real provider integration.

### 3. Observe the accepted fake-stage claim

For a runtime claim, exercise only the paths and outcome classes needed to support it. For a source/design claim, inspect the applicable contract and implementation without implying execution. Full-flow, restart, concurrency, UI/mobile or accessibility observations are not automatic. Record evidence and its limits; this may reduce unknowns before any separately authorized live integration.

### 4. Add the real provider adapter when it is in scope

Implement only the applicable in-scope adapter-specific concerns:

- SDK/script/network wiring;
- secrets/config;
- callback mapping;
- provider error normalization;
- CSP/origin requirements;
- production environment setup.

Keep application semantics behind the same seam.

### 5. Assess a claimed real provider integration

Only where a real-provider claim is accepted, obtain evidence for the relevant behavior the fake cannot prove. Do not add a live call, release, test suite or production credential use to a fake-only assignment. Potential claim-specific concerns include:

- production credentials/config;
- browser/widget behavior;
- redirects/callbacks;
- network failure;
- origin/CSP constraints;
- provider-specific retry/idempotency;
- actual accessibility behavior where applicable.

### 6. Keep fallback policy explicit

Decide what happens if the provider is unavailable:

- block safely;
- fail open;
- retry;
- offer alternative provider/path;
- degrade functionality.

This is a product/security decision, not something the pattern chooses universally.

## Why it works

It isolates domain/application correctness from provider-specific operational complexity. By the time the real provider is attached, most failures can be classified as adapter/provider issues rather than unknown whole-system behavior.

## Trade-offs

- a fake can diverge from real provider behavior;
- maintaining a seam adds abstraction;
- late discovery of provider constraints can still force redesign;
- some provider-specific UX cannot be tested until late;
- over-generalizing the seam can create unnecessary indirection.

## Alternatives

Consider instead:

- integrate the provider immediately and use its sandbox/test environment throughout;
- run contract tests against a provider emulator;
- use a local proxy/record-replay harness;
- accept provider lock-in and design directly against its SDK;
- perform a short spike with the real provider first, then decide whether a seam is valuable.

## Failure modes

- fake models only success and hides real failure classes;
- application starts depending on fake-only fields;
- provider adapter leaks SDK objects into all layers;
- team treats fake soak as production provider certification;
- live integration happens so late that untested hard constraints appear at release time;
- fallback behavior is accidentally defined by provider SDK defaults;
- provider-specific security checks are abstracted away incorrectly.

## Verification

- Evidence supports the accepted fake/stub-stage outcomes and intended seam; a fake-stage PASS does not assert a real adapter exists.
- Only when in scope, verify real adapter mapping, provider-specific behavior and fallback policy through the appropriate authorized observations. Source or fake evidence alone cannot prove live-provider behavior.
- Verify replacement semantics only where replacement is actually claimed; reuse relevant existing checks without automatically authoring new tests.

## Related Core Principles

- `dependency-ownership` — external provider is a dependency with its own integration/release gate;
- `authority-mapping` — define which provider outcome is authoritative and what the application owns;
- `irreversible-boundary-reasoning` — some provider calls may create non-repeatable effects;
- `evidence-and-authority` — fake integration evidence and live-provider evidence prove different claims.
