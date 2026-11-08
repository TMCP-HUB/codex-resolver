---
name: mcp-adapter-acceptance
description: Verify only the actual claimed MCP adapter behavior with exact candidate evidence and proportionate independent acceptance.
---

# Purpose
Distinguish a well-formed source adapter from a connected, permitted, deployed and correctly behaving MCP integration.

## Goal
Provide enough evidence for the claimed use, without creating a separate verification engine or universal live-test ritual.

## When to use
An MCP implementation candidate, actual secured client connection, tool contract change, release/deployment or observed coverage regression.

## Inputs
Frozen acceptance scope, exact source/PR SHA, authoritative service/tool mapping, selected protocol/SDK/client versions, existing CI and authenticated runtime only when live claims require it.

## Execution contract
- **Static/source mode:** exact candidate source and any relevant existing CI evidence available for the stated source claim. Source-only CI checks source only; it does not prove a live service, deployed connectivity or particular client behavior.
- **Protocol mode:** actual negotiated MCP protocol/transport and compatible SDK or Inspector when protocol claims require it; an Inspector alone does not prove a particular host/client works.
- **Deployed mode:** actual authenticated endpoint and declared safe actions; mutations only with explicit authorized non-production or controlled test scope.
- If a mandatory channel is unavailable, return `NOT_PROVEN`, not a fabricated PASS.

## Required outputs
Concise claim-to-evidence verdict: service reuse, exposed tools, input/output, authorization, error/readback behavior, exact runtime/release status and client compatibility only where tested.

## Procedure
1. Verify source/service authority and scope before live interaction.
2. For a version-sensitive compatibility claim, ground protocol/SDK behavior in official documentation for the versions actually negotiated or pinned. Reuse relevant existing focused CI/tests when they support the claim; source-only CI is not a live check. Do not automatically write new tests or require external access merely because a claim is abstract or source-only; a specific version-sensitive claim may still need its official source.
3. Exercise a version-appropriate discovery/call flow with a compatible SDK, Inspector or another appropriate supported client only when a claimed behavior requires runtime observation. Static conformance does not prove a particular host/client works.
4. Where provider interchangeability matters, inspect interface and authority seams: replacement must not require copying the provider's business rules or permissions into a central platform. A reasoning review does not prove hot swap or require a gateway.
5. Check deployed identity and authorized write/readback only when required; never surprise-mutate production. Distinguish source correctness, endpoint connectivity and client acceptance.
6. Return exact claim-specific evidence to the existing Verifier/Director. When independent acceptance is required, an available capable assessor separate from the implementer performs the necessary observation; a technical observation does not automatically require a human. The adapter skill does not self-certify or promote.

## Anti-patterns
Claiming deployment from local tests, mandatory screenshots or broad suites, assuming all clients support every version/extension, demanding replaceability universally, new verifier or report ontology.

## Verification
Only evidence-backed claims are PASS. Missing or contradictory proof is NOT_PROVEN/DEFECT with one bounded next action.
