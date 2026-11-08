---
name: mcp-authentication-reuse
description: Reuse existing authentication and authorization for secure MCP endpoints without creating a second identity system.
---

# Purpose
Select the minimum verified identity and credential path for the actual MCP client and service.

## Goal
Authenticate the remote client and enforce the existing business principal, permissions and scopes for every operation.

## When to use
A secured MCP connection, new client, changed permission boundary, credential rotation or revocation requirement is actually in scope.

## Inputs
Existing identity authority, service authorization, actual MCP transport/protocol version, client capabilities, target resource identifier, credential lifetime and relevant revocation requirements.

## Execution contract
- **Design mode:** use supplied or permitted auth contracts and known client support; abstract design needs no live client or secret. Concrete compatibility claims require the actual client, transport and version evidence. Never request or print live secrets.
- **Integration mode:** requires separately authorized access to auth configuration/secret facility and appropriate test destination.
- **Evidence:** map the chosen principal and service permissions. Support any claimed per-client mechanism, denied access or permitted access with the appropriate source or observed evidence; an abstract design does not prove live authentication or authorization.
- Missing client compatibility or auth capabilities means `NOT_PROVEN` or an exact incompatibility, not a fallback to bypassing auth.

## Required outputs
Selected client authentication flow, backend authorization mapping, secret location, supported session/rotation behavior and residual limitations.

## Procedure
1. Separate client-to-MCP authentication, the MCP resource's validated principal, and MCP-to-business-service authorization. Reuse existing identity and permission owners, not a shadow user database.
2. Identify the **actual transport and protocol revision**. The MCP HTTP authorization profile uses OAuth resource-server semantics where applicable; stdio normally uses environment-supplied credentials and does not need mandatory HTTP OAuth. Verify client support before choosing.
3. For MCP OAuth on HTTP, follow the applicable official authorization profile for Protected Resource Metadata, authorization-server discovery, resource indicators and token audience/issuer validation. A token must target this MCP resource, not a neighbor or unrelated tenant. Non-OAuth compatibility modes such as Basic over HTTPS or product-issued service tokens may be used only where authorized and supported by the actual client and service; they do not establish OAuth-only client interoperability. Enforce each operation's business rights in every mode.
4. Never blindly forward an incoming MCP client token to upstream services or use an unscoped super-token. Obtain distinct upstream authority via an authorized service credential, delegation or token exchange as appropriate; same principal does not mean same token audience.
5. Keep secrets in the established facility, not source/plaintext caches. Scope/permission denial, expiry, rotation, revocation and least privilege belong to the real service owner; KV freshness is not atomic revocation.
6. Verify scoped client/transport and permitted/denied operations only as claimed. Missing source access or client evidence is `NOT_PROVEN`, never permission to disable authorization.

Current official reference (select the version actually used): https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization . This URL is not proof of the project's negotiated version.

## Anti-patterns
Shadow user database, shared unscoped super-token, blind upstream token passthrough, accepting wrong-audience tokens, forcing HTTP OAuth on stdio, equating login with permission for all mutations.

## Verification
Report only evidenced transport-appropriate authentication, target-resource token validation where relevant and per-operation least privilege, with exact limits. Source reasoning does not prove actual permitted or denied access; do not invent session persistence guarantees.
