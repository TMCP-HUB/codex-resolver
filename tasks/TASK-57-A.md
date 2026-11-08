# TASK-57-A — Consolidate CAPABILITY_PROFILE into canonical execution-surface advertisement

Status: FROZEN EXECUTION PACKET after this file's materialization commit. Do not modify this file during execution.

Parent: #57 — Execution Surface Profiles and capability brokers
Child issue: #90 — 57-A: consolidate CAPABILITY_PROFILE into canonical execution-surface advertisement
PAC tracker: #77

Starting authoritative main:

`5d38536b544916917cdfce186032dc8ef8aacf03`

Execution branch:

`task-57-a-execution-surface-profile`

## Objective

Materialize the first bounded #57 seam by extending the repository's **existing executability owner** into the canonical provider-neutral execution-surface advertisement/profile equivalent.

Do **not** create a second execution-surface/profile ontology merely to introduce the name `EXECUTION_SURFACE_PROFILE`.

Core law:

```text
EXISTING EXECUTABILITY OWNER
MUST BE EXTENDED
NOT DUPLICATED
```

The implementation must preserve the current semantic separations:

```text
SURFACE / CAPABILITY ADVERTISEMENT
!= SEMANTIC AUTHORITY
!= ASSIGNMENT AUTHORITY
!= RESOURCE AUTHORITY
!= AUTONOMY AUTHORITY
```

and:

```text
RUNTIME / TRUSTED ADAPTER ADVERTISES REALITY
→ CODEX VALIDATES THE ADVERTISEMENT
→ CODEX MAY ADMIT ONLY CURRENT USABLE REALITY
```

## Mandatory baseline audit before mutation

Inspect the actual branch state first. At minimum reconcile the current owners around:

- `contracts/EXECUTABILITY_CONTRACT.md`;
- `schemas/capability-profile.schema.json`;
- `tools/executability.py`;
- `tools/resolver_spawn.py`;
- `tools/resolver_transition.py`;
- current `CAPABILITY_PROFILE` / `CAPABILITY_EVIDENCE` semantics;
- current `EXECUTION_ROUTE` bindings;
- current `ASSIGNMENT_ADMISSIBILITY` semantics;
- directly affected executability/spawn/transition tests.

Do not assume the child issue's suggested field names are automatically missing. Reuse an existing field or exact profile/ref binding when it already owns the required meaning.

The current known baseline already contains equivalents of:

```text
artifact/profile identity
destination_id
runtime_identity
available_capabilities
unavailable_capabilities
capability evidence
freshness boundary
limitations
```

Preserve existing valid behavior and compatibility unless a real contract contradiction is discovered.

## Required semantic result

After 57-A, one canonical profile owner must be sufficient to describe one concrete advertised execution surface/runtime context with concepts equivalent to all of the following:

```text
profile / surface identity
surface class
runtime identity / runtime class as needed
opaque workspace scope
available capabilities
unavailable capabilities
mutation capabilities distinguishable from ordinary/read capabilities
evidence channels
current readiness / provisioning state
freshness sufficient for deterministic stale/drift handling
advertisement provenance / evidence
limitations
```

Exact field names and internal representation are implementation choices unless an existing contract requires them.

### Profile identity

Prefer the existing artifact/profile identity if it already provides exact profile identity. Do not add a redundant `surface_id` merely for naming symmetry.

### Surface class

The model must be provider-neutral and able to represent concrete families such as:

```text
CHATGPT_CHAT
REMOTE_DEV_ENV
CODEX_CLOUD
BROWSER_CONSOLE
DEPLOYMENT_RUNTIME
MANUAL_OPERATOR
```

These names are reference families, not permission to hard-code provider mechanics into universal control law. If a smaller/generalized provider-neutral vocabulary is sufficient, use it and prove the mapping in tests/reference fixtures.

### Workspace scope

Represent an opaque `workspace_scope_ref` or equivalent scoped identity sufficient to distinguish where the advertised surface operates.

Public Codex may know an opaque value such as:

```text
ext-scope:runtime:0184
```

while a future private runtime may map it to a concrete ChatGPT Project, Codespace, provider URL, account project, tab, or other physical object.

Do not expose or promote browser tab IDs, conversation IDs, DOM generations, provider-session IDs, or similar private physical runtime mechanics into semantic authority.

### Readiness / provisioning

Do not overload an existing artifact-lifecycle status such as `status=CURRENT` if that status already has a distinct meaning.

The profile must separately represent, directly or equivalently, whether the surface is usable now versus awaiting setup/authentication. Required semantic distinctions are equivalent to:

```text
READY
DEGRADED
PROVISIONING_REQUIRED
AUTH_REQUIRED
UNAVAILABLE
```

A structurally valid/current profile that is not currently usable must **not** satisfy assignment admission or yield `SPAWN_READY` merely because its account/provider exists.

Do not implement surface ranking/selection in 57-A. Only make a selected/cited profile fail closed when its readiness cannot satisfy execution.

### Mutation capability distinction

Ordinary/read capability must not imply mutation capability.

At minimum the representation/validation must make distinctions such as these mechanically visible:

```text
repository_remote_read != repository_remote_write
ci_read != ci_trigger
provider_log_read != production_mutation
```

Do not infer mutation authority from broad prose or role names. Capability availability still does not create authority to exercise the capability.

If the current capability vocabulary can carry this distinction without duplicating data, reuse it only if the distinction remains deterministic for consumers. Do not add a second list solely for aesthetics. Do not add ad-hoc string-prefix inference as hidden policy.

### Evidence channels

Represent or tightly bind the kinds of evidence the surface can return for governed verification, with provider-neutral concepts equivalent to examples such as:

```text
connector_result
terminal_stdout
unit_test_result
build_log
deployment_status
durable_artifact_ref
chat_completion
```

Reuse existing capability/evidence machinery where it already owns the meaning. Do not create a parallel evidence ontology.

### Freshness / replacement

Preserve the existing freshness-bounded evidence law.

The resulting profile must carry enough exact runtime/profile freshness identity for later control to detect stale advertisements or physical surface replacement. Reuse `runtime_identity`, exact profile identity and the existing freshness boundary if together they are sufficient. Do not introduce #58 logical `SESSION_EPOCH` here.

57-A does not implement the future ticket/claim-time revalidation boundary, but it must leave an exact profile that 57-C and TICKET/CLAIM can safely revalidate later.

## Resource / connector / surface law

The implementation and tests must preserve these distinctions:

```text
GOOGLE DRIVE RESOURCE
!= EXECUTION SURFACE

GITHUB REPOSITORY
!= EXECUTION SURFACE

CONNECTOR / PLUGIN
= CAPABILITY OR EVIDENCE CHANNEL ON A SURFACE
!= A SEPARATE SURFACE BY EXISTENCE
```

A Codespace-like terminal, Codex-Cloud-like environment, ChatGPT-like chat runtime, or browser-console-like context may be represented as a surface because it is an actionable runtime context.

Do not create one surface for every provider/resource/connector.

## Fake/reference advertisements

Provide deterministic provider-neutral test fixtures or reference advertisements sufficient to demonstrate at least:

1. a ChatGPT-like conversational surface with connector capabilities;
2. a remote terminal/dev surface with shell/test capability;
3. a Codex-Cloud-like environment-local code surface;
4. a browser-console-like evidence surface;
5. a surface requiring provisioning/authentication or otherwise unavailable.

These are reference semantics only.

Do not integrate or call real ChatGPT, GitHub Codespaces, GitHub web, Cloudflare, Codex Cloud, MCP, browser automation, or external provider APIs.

## Existing owner integration constraints

Preserve the meanings of:

```text
CAPABILITY_PROFILE
CAPABILITY_EVIDENCE
EXECUTION_ROUTE
ASSIGNMENT_ADMISSIBILITY
```

In particular:

```text
ASSIGNMENT_ADMISSIBILITY = CAN EXECUTE ON THE CITED SURFACE
```

It must not become resource admission, autonomy permission, Owner authority, or execution claim authority.

Do not duplicate exact surface fields into `EXECUTION_ROUTE` when the route's exact profile ref already gives the required binding. Strengthen a binding only if the existing route/profile relation is insufficient to fail closed.

`resolve_spawn()` and `resolve_transition()` may consume the extended profile only as needed to preserve current exact binding/readiness/freshness semantics. Do not move semantic surface selection into either function.

## Stop condition for a true upstream contract gap

If the existing `CAPABILITY_PROFILE` cannot own the required surface semantics without violating a materially different existing responsibility, STOP before creating a new artifact family.

Report:

```text
CONTRACT_GAP_FOUND: YES
EXISTING_OWNER_CANNOT_REPRESENT: <exact responsibility>
WHY DISTINCT PROFILE IS REQUIRED: <bounded non-overlapping reason>
```

Do not create `EXECUTION_SURFACE_PROFILE` simply because #57 uses that conceptual name.

## Explicit non-goals

Do not implement in this task:

- 57-B surface selection/ranking;
- 57-C broker/provisioning workflow or claim-time drift revalidation;
- real capability provisioning;
- PAC/MCP/browser adapters;
- actual Codespaces terminal control;
- actual Codex Cloud control;
- GitHub/Cloudflare/provider integration;
- TICKET-01;
- CLAIM_EXECUTION / resource reservation;
- #58 logical instance or logical session epoch;
- #59 HC/autonomy policy;
- #61 Architecture Health;
- Resource Governance redesign;
- PACK Protocol;
- Start-0 / Project Formation implementation;
- provider SDK dependencies;
- GitHub Actions.

Do not modify this frozen task file.

## Required regressions / proof

Add or update bounded tests proving the resulting existing owner can represent and validate the required semantics without a second profile ontology.

At minimum prove:

1. a ready conversational/connector surface is structurally valid;
2. a ready remote terminal/dev surface is structurally valid;
3. an opaque workspace scope is preserved and exact-profile binding remains deterministic;
4. mutation/read capabilities are distinguishable without conferring authority;
5. evidence channels are represented/bound without creating a parallel evidence authority;
6. `PROVISIONING_REQUIRED` cannot satisfy current execution admission;
7. `AUTH_REQUIRED` cannot satisfy current execution admission;
8. `UNAVAILABLE` cannot satisfy current execution admission;
9. a usable ready profile preserves the current happy path;
10. stale/invalid capability evidence still fails closed;
11. exact `EXECUTION_ROUTE` / assignment/profile binding remains valid after the extension;
12. provider/resource/connector names are not required as universal semantic identifiers.

Retain schema/runtime parity for every changed structured artifact.

Run the directly affected repository unittest modules available on the execution surface. Expected affected families include executability, executability structure/parity, resolver spawn, and resolver transition. Discover the exact current module names from the repository rather than inventing missing modules.

Do not use GitHub Actions for this task.

If the current execution surface cannot honestly run a required local suite, report it as `NOT RUN` and leave merge readiness at independent verification; do not fabricate results and do not weaken acceptance.

## Scope discipline

Use the current branch. One bounded implementation PR only.

Prefer the smallest compatible delta. Do not rewrite unrelated executability code, schemas, resource governance, resolver semantics, or provider infrastructure.

If implementation reveals a true upstream contract conflict, stop and report it instead of expanding scope.

## Completion report

Return at least:

```text
STARTING MAIN
TASK COMMIT / TASK BLOB
FINAL HEAD / TREE
BRANCH
PR
CHANGED FILES

CURRENT OWNER MAPPING BEFORE CHANGE
REUSED SEMANTICS / FIELDS
NEW SEMANTICS / FIELDS
COMPATIBILITY / MIGRATION DECISION
REFERENCE SURFACES PROVEN
TESTS RUN
TESTS NOT RUN

CONTRACT_GAP_FOUND: YES|NO
DUPLICATE_PROFILE_CREATED: NO
57-B: NOT STARTED
57-C: NOT STARTED
MERGE READINESS: <state>
```

Do not merge the PR. Merge requires explicit Owner authorization after independent verification.
