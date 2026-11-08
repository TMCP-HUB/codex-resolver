# Strategy 2030 — agent-first products

## Authority and scope

Owner direction, 2026-11-07: the current name is **Strategy 2030**, not Strategy 2050. This is the overarching product-development strategy in Resolver. It guides product foundations, architecture, planning and delivery; it does not replace Owner authority, accepted product Canon, authorization, security boundaries or independent verification.

The product's domain capabilities, data and business contracts are primary. All interfaces are secondary projections or adapters. A website, admin panel, mobile UI or chat surface must not be the only owner of a business operation. Secondary does not mean dispensable: retain required usability, accessibility and existing user workflows.

## Capability-first implementation

- Keep business rules, validation, state and permissions in their authoritative domain/service boundary. UI, HTTP/API, MCP and A2A reuse it.
- Build capabilities independently of interface release order. MCP functions may precede and exceed UI functionality; UI parity is neither a prerequisite nor a ceiling.
- Prefer a small MCP adapter over existing authoritative functions rather than duplicating the domain in an agent platform. A new service may co-design this seam from the start.
- Reuse existing runtime and identity boundaries. Strategy does not require a separate service, database, queue, gateway or deployment per adapter.

## Required AI-search visibility and HTML projections

AI-search optimization is mandatory for public product information intended to be discovered. Provide useful, crawlable, semantic HTML projections of authoritative product information, stable canonical URLs, clear headings and descriptions, discoverable links and appropriate structured data consistent with visible content. Keep projections current with their source rather than maintaining a divergent second truth.

Use actual crawler/indexing requirements and inspect the delivered HTML/content where the assignment implements this surface. Preserve private data, authorization, robots and indexing choices. Private operations do not become public for SEO. Do not promise rankings, citations or inclusion in model answers. llms.txt can be a supplementary experiment, not a universal indexing requirement or a replacement for HTML, sitemaps and sound SEO.

## Required A2A direction

A2A implementation is a strategy-wide requirement for applicable agent-enabled products, not an optional aspiration. Product planning must include the real independent-agent capabilities, existing or planned A2A boundary and a bounded implementation stage. An unimplemented applicable A2A requirement remains open; writing an Agent Card or saying “agent-ready” does not satisfy it.

Use the existing a2a-agent-interoperability skill for actual discovery, messages, tasks, auth and evidence. Keep MCP tool/data access distinct from A2A communication between independent agents. Internal subagents and ordinary HTTP APIs are not automatically A2A. A documentation-only repository or unrelated repair does not need a dummy A2A server; applicability and any deferred product rollout belong in the existing plan/result, not a new approval ceremony.

Advertise real capabilities only. Compatibility and completion claims require the applicable protocol/binding and exact implementation or runtime evidence. This strategy alone does not authorize contacting a third party, provisioning infrastructure or deploying a product.

## Site-to-agent interoperability: reuse before invention

“Site-to-Agent” describes the desired capability, not an established new standard owned by this project. Source review on 2026-11-07 found existing overlapping approaches:

- [WebMCP](https://webmachinelearning.github.io/webmcp/) lets web applications expose JavaScript tools to agents. It is a W3C Community Group draft, explicitly not a W3C Standard or Standards Track specification.
- [MCP](https://modelcontextprotocol.io/specification/latest) connects agent clients to tools and data through servers.
- [A2A](https://a2a-protocol.org/v1.0.0/) covers independent-agent interoperability.
- [NLWeb](https://github.com/nlweb-ai/NLWeb) is an existing project for conversational access to web information.

These are different layers, not interchangeable names. No absence of a suitable site-to-agent approach has been established merely because there is no single universal standard with that exact name. Browser support and protocol versions must be checked for each actual integration.

The Owner's conditional direction is retained: if existing approaches cannot cover the required site-to-agent capability, create a distinct project in a separate repository for that demonstrated gap. First state the exact missing capability and how existing approaches fall short. Prefer an interoperable extension/profile or implementation over an invented competing wire protocol. Do not create a redundant repository or claim standard status, novelty or universal adoption without evidence. This Resolver change creates no separate protocol repository.

## Applying the strategy without another bureaucracy

Use existing foundation/Canon decisions, Software planning and result records. For affected product work, state the domain seam, selected adapter/projection changes, applicable AI-search/HTML work and A2A implementation stage with actual evidence or remaining work. No new artifact schema, role, test suite, global deployment gate or mandatory UI-parity matrix is introduced.

A strategy-policy change proves only the Resolver instructions changed. It does not prove that downstream products have deployed MCP, A2A, WebMCP or HTML projections. Continue bounded authorized work without silently expanding it into unrelated migrations.

Official SEO reference: [Google Search guidance for AI features](https://developers.google.com/search/docs/appearance/ai-features), reviewed 2026-11-07. Existing SEO fundamentals apply; no special AI markup or guaranteed inclusion is claimed.
