---
name: mcp-tool-contracts
description: Specify thin, typed MCP tools over authoritative business service contracts, existing or co-designed, preserving permission and write semantics.
---

# Purpose
Make business actions understandable and safe for AI clients without rebuilding the product inside MCP.

## Goal
Define stable business-intent operations with concise schemas, permissions and honest results, without creating a second domain model in MCP.

## When to use
Real MCP tool implementation or an intentional change to an existing tool contract. Not for an unrelated Admin UI feature.

## Inputs
Authorized existing or newly designed service operations, request/response schema, permissions, write semantics, negotiated MCP version, SDK/client support, pagination and failure semantics.

## Execution contract
- **Design mode:** use supplied or readable relevant business contracts and draft the selected tool contract; purely abstract reasoning needs no live endpoint, SDK or network. Concrete compatibility claims require the actual version and applicable evidence.
- **Implementation mode:** separately authorized source write/publication and whatever implementation, runtime and focused validation capabilities the selected method and accepted claim actually require; an SDK is not mandatory for a justified compatible alternative.
- **Evidence:** match the service/tool pairing, schema, permissions and result to the claim; source review cannot establish runtime behavior. When a required source or runtime is unavailable, report `NOT_PROVEN` and the exact missing capability, not a substitute claim.
- If the business service is new, co-design its minimum domain contract with the business owner; never invent an MCP-owned second authority.

## Required outputs
In-scope named tools with description, typed inputs/outputs, read/write effect, authorization, authoritative API mapping, bounded output and truthful error/unknown-outcome handling.

## Procedure
1. Prefer small business-intent tools, not a generic arbitrary-code executor or a mirror of every HTTP route.
2. Prefer an official MCP SDK compatible with the target runtime and negotiated version, with typed/structured output supported by the actual client. A justified alternative, including an independently implemented protocol stack, is acceptable when its relevant conformance and interoperability are evidenced; disclose unsupported features or clients. If no supported path is evidenced, report `NOT_PROVEN`, not an invented fallback. Do not infer protocol behavior from old examples.
3. Map the authenticated resource principal to the service's real business permissions. Enforce authorization, validation and atomicity at the authoritative business owner; an MCP connection is not permission for all operations.
4. Avoid default queues and automatic retries. An uncertain write result is not proof of failure; use backend idempotency/reconciliation only where needed.
5. Confirm actual transport, version and extension support before selecting tool features; not every host supports the same revision.
6. Keep backward-compatible optional changes simple; introduce a new tool only when business meaning changes materially.

## Anti-patterns
MCP-only SQL/data mutations, an unjustified or unverified bespoke protocol stack, speculative locks/queues, unsafe blind write replay, duplicate business validation.

## Verification
Assess the claimed shared semantics, permissions and version-appropriate contracts against their evidence. Source review alone cannot prove that runtime unauthorized writes fail; mark unobserved behavior unproven. Preserve honest unknown outcomes and avoid requiring MCP for the base business operation.
