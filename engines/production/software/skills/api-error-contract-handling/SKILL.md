---
name: api-error-contract-handling
description: Map documented HTTP/API errors to faithful client behavior and safe unknown-error fallback. Use for a selected endpoint and client when error semantics are in scope.
---

# API Error Contract Handling

## Purpose and goal

Preserve the actual service's documented error meanings through the client, with useful, safe actions and a truthful fallback for unknown outcomes. This is an optional Software method, not an API registry or a test framework.

## When to use

An API endpoint/client's error handling, contract, behavior or regression is within the accepted scope. It applies to web, mobile, CLI and service clients. Use web QA only for a claimed browser interaction; use focused runtime observations only for claimed running behavior.

## Inputs

Selected endpoint/operation and client; authoritative service contract and actual version (OpenAPI, SDK or service source as applicable); documented statuses, error codes/types, fields, permissions and retry semantics; accepted claims, existing evidence and safe diagnostics policy.

## Execution contract

- **Contract/source mode:** read supplied or authorized actual versioned contracts and relevant client source; no live service, browser, network, build or new tests is implicit. Reasoning about supplied contracts does not require repository access. Source evidence does not prove runtime behavior.
- **Runtime/client mode:** only when the accepted claim needs it, use an authorized capable runtime and the smallest suitable observation, existing check, controlled response or stub. A stub proves only the behavior exercised against that stub; it does not prove the real service or deployment. Real requests or mutations need their own scope and authority.
- **Unavailable evidence:** identify the particular contract, capability or observation missing and mark that claim `NOT_PROVEN`. If genuinely necessary scope/evidence remains ambiguous, ask the existing Control Director for bounded clarification; do not reopen an approved Owner decision.
- **Independence:** where independent acceptance is required, a separate available capable assessor observes the relevant claim; a technical observation does not automatically require a human.

## Required outputs

A concise mapping of relevant documented status and error code/type to distinguishable client behavior, safe message/action and applicable retry/recovery semantics; unknown/malformed/network fallback; exact evidence and any unproven claim. Preserve safe correlation/request IDs where available.

## Procedure

1. Identify the selected service and endpoint, version and authoritative contract; inspect its documented responses, machine-readable codes/types, field validation errors, authorization failures, rate limits, conflicts and retry semantics where relevant. A single status can represent multiple business errors; do not collapse distinct documented codes.
2. Map every documented relevant error to its meaning and an appropriate distinct client behavior, message and next action. Preserve actual HTTP status and service error type/code and safe request/correlation ID for diagnosis. Do not expose credentials, internal stacks or sensitive payloads.
3. For an unknown status, undocumented code, malformed response, network outage, timeout or lost acknowledgement, use a truthful generic fallback with safe diagnostics. Do not invent a business diagnosis or handlers for unknowable future codes. An uncertain write is not a confirmed failure: reconcile or use only the service's documented idempotency/retry rules before any repeat.
4. Prefer the existing service error format. If relevant, consult the official standard/version applicable to that service: [OpenAPI 3.1.2 Responses](https://spec.openapis.org/oas/v3.1.2.html#responses-object), [OpenAPI 3.2.0 Responses](https://spec.openapis.org/oas/v3.2.0.html#responses-object) and [RFC 9457 Problem Details](https://www.rfc-editor.org/rfc/rfc9457.html). OpenAPI's `default` can describe undeclared response codes; it is optional. Problem Details is not mandatory for an existing or unrelated format; when actually used, respect its defined members and type semantics.
5. Select evidence for the actual contract, runtime or user-facing claim. Reuse appropriate existing CI/checks where they prove that claim; verification does not automatically require writing tests, a build, browser inspection or provider calls. Source-only evidence cannot establish a live response or rendered UI.

## Anti-patterns

Flattening documented business errors into a generic known-error message; assuming an undocumented code has a particular meaning; showing raw credentials or stack traces; blindly retrying uncertain writes; requiring one error format, UI framework, test suite or live provider for every API.

## Verification checklist

- [ ] Relevant documented codes/types and field failures have faithful, distinguishable behaviors and safe actions.
- [ ] Unknown or malformed responses and transport failures have a truthful safe fallback; uncertain writes are not blindly replayed.
- [ ] Evidence matches the accepted contract/runtime/browser claim and exact target/version; unsupported claims remain explicit.
- [ ] Existing verification and independence requirements are preserved without introducing a new gate or test-writing mandate.

## Minimal verdict

`ENDPOINT/VERSION | DOCUMENTED MAPPING | UNKNOWN FALLBACK | CLAIM/EVIDENCE | LIMITATIONS`
