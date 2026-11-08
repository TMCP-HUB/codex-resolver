---
name: mcp-capability-parity
description: Map selected business capabilities across service clients and MCP, including new co-designed services, only when coverage is in scope.
---

# Purpose
Avoid silently losing required business operations or exposing internal administrative controls as unrestricted tools.

## Goal
Derive MCP coverage from authoritative business service contracts (existing or co-designed), not a parallel feature registry.

## When to use
New MCP adoption, a business-operation change that affects declared MCP coverage, or a proven parity defect. Not required when merely making an Admin UI future-ready.

## Inputs
Exact authorized existing/planned business operations, authoritative schemas, permissions, read/write semantics, selected MCP/client versions and evidence.

## Execution contract
- **Read-only mapping:** needs access to relevant current contracts/code and any existing tool catalog; no source mutation.
- **Implementation:** separate authorized Software execution path if a gap must be fixed.
- **Evidence:** exact current service operations and the corresponding claimed MCP tools; missing source access is `NOT_PROVEN`, not coverage.

## Required outputs
A small mapping only for in-scope business capabilities: operation, authoritative service, permission, query/mutation, MCP tool or justified exclusion, proof/status.

## Procedure
1. Identify the business action independently of presentation routes.
2. Reuse published API/OpenAPI/operation definitions and current permissions where possible. For a new service, use its co-designed authoritative domain contract; do not create a second catalog inside MCP.
3. Map only in-scope capabilities to MCP tools supported by the actual client/protocol version; keep internal maintenance operations excluded unless authorized.
4. Classify real gaps without auto-generating a tool per endpoint.
5. Delegate implementation of missing operations to the business API owner, not to an MCP-owned second service.

## Anti-patterns
A second truth table for all product features, equality by endpoint counts, generic execute-anything tools, parity paperwork for unrelated Admin edits.

## Verification
Every claimed MCP capability resolves to an authorized service operation, including permissions, side effects and client compatibility. Mark excluded or unproven coverage honestly.
