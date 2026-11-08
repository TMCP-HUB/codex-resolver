---
name: mcp-adapter-intake
description: Choose the smallest MCP-ready boundary for an existing or new service, including a no-MCP option and conditional local or shared adapter routes.
---

# Purpose
Design a reusable MCP interface without duplicating existing domain authority or committing to a runtime prematurely.

## Goal
Keep every intended client (UI, REST, MCP or other adapter) over the service's authoritative business contracts, whether an existing service is reused or a new one is co-designed.

## Strategy 2030

Apply `kernel/STRATEGY_2030.md`: authoritative business functions come first and MCP is an adapter to them. MCP capabilities may precede or exceed UI functions; do not impose UI parity or a UI-first release sequence. A bounded no-MCP decision does not waive an explicit product requirement or remove its planned implementation.

## When to use
When MCP design or a material service/API integration is in scope. For unrelated UI/API work, assess a future interface seam only if material; do not implement MCP by default.

## Inputs
Authorized business capability, existing or planned service owner, identity/permissions, target clients and constraints. For a concrete MCP compatibility claim, include actual protocol/SDK/runtime versions and deployment context.

## Execution contract
- **Design mode:** read only relevant current architecture/contracts; no network, shell or credential is universally required. If current repository or API facts must be inspected, prove the corresponding read capability.
- **Implementation mode:** separately admitted Software assignment with exact write/publication and validation capabilities.
- **Evidence:** identify the existing or explicitly planned authoritative service owner and decision. For an actual adapter/version or compatibility claim, include its route, applicable protocol/source version and supported/unsupported client assumptions. Abstract and `NOT_NEEDED_YET` decisions need no live MCP, network or invented version.
- **Unavailable evidence:** mark unknown/not-proven; do not claim connected tools or a deployed MCP endpoint.

## Required outputs
Concise decision: `NOT_NEEDED_YET`, `PRODUCT_LOCAL`, or `OPTIONAL_SHARED_GATEWAY`; authoritative business-service seam, actual client needs, smallest next step and non-goals.

## Procedure
1. Identify who owns each business operation, authoritative data, validation and permissions. For a new service, design its domain contract alongside an optional MCP adapter, without making MCP the source of domain truth.
2. Check that UIs, APIs and agents reuse the business contract rather than copying business rules into adapters or central platforms.
3. Choose `NOT_NEEDED_YET`, `PRODUCT_LOCAL` or `OPTIONAL_SHARED_GATEWAY` based on real routing needs. Neither a Queue, separate Worker/service nor Gateway is mandatory; a clean boundary may be inside one deployment.
4. Only for a concrete version-sensitive MCP choice or claim, consult the relevant current official MCP protocol/SDK documentation for the actual target/negotiated versions, transport and client support. Prefer a compatible maintained official SDK; a reasoned compatible alternative is allowed, not a blanket custom-stack ban. If required documentation is unavailable, mark that claim `NOT_PROVEN`; a no-MCP or abstract design does not require live sources.
5. Where interchangeability matters, ask whether replacing/removing the provider changes the consumer's business logic, data owner or permissions. Do not demand a provider-independent interface where the product deliberately binds to a provider.
6. Select other MCP skills only for in-scope contract, authorization, coverage or acceptance questions.

## Anti-patterns
New MCP-owned business database, universal API mirror, extra user directory, mandatory MCP deployment, speculative transport/retry engines, duplicated feature catalog, central platform storing individual providers' business rules.

## Verification
Can the business capability operate without MCP? Is its authority independent of adapters? Are extra components justified, and provider dependencies known? Unsupported compatibility claims remain explicit.
