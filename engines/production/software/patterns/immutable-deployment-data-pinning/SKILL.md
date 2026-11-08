# Immutable Deployment Data Pinning

> Classification: **Solution Pattern — optional**. This is one way to keep executable code, external data, and interpretation rules version-compatible. It is not required when data is intentionally mutable and backward-compatible.

## Problem class

A deployed executable interprets external content/config/data whose structure or meaning may evolve. If the executable follows a mutable global pointer such as `active`, `latest`, or current database state, a deployment can accidentally interpret data produced for a different code revision.

## Production trace

This pattern came from a deployment flow where content and delivery topology could change independently from the web application. Correctness required every deployment to select the immutable release and interpretation plan it was built to understand rather than whatever release happened to be globally active later.

## Assumptions

- code and data can be versioned independently;
- incompatible combinations are possible;
- immutable data/config identities can be generated and resolved;
- old sessions/jobs may outlive a deployment and need compatibility handling.

## Use when

Use when:

- application code interprets versioned content, rules, schemas, models, manifests, or generated data;
- deployment rollback must also restore compatible data interpretation;
- mutable aliases can move independently from code;
- long-lived workflows need to know which interpretation plan they started under;
- staging data before code deployment should not affect the currently live deployment.

## Do not use when

Prefer a simpler design when:

- all data changes are guaranteed backward-compatible by contract;
- the application intentionally reads live mutable configuration;
- data is embedded into the build artifact already;
- schema negotiation handles compatibility dynamically;
- pinning would prevent an explicitly required real-time update model.

## Pattern

### 1. Give deployable data an immutable identity

Use an identity natural to the system:

- release ID;
- content hash;
- manifest digest;
- model/version digest;
- ruleset revision;
- schema bundle ID.

The identity should refer to immutable contents or a verifiably immutable snapshot.

### 2. Bind code to the identity it expects

The executable deployment carries or resolves its expected data identity.

```text
DEPLOYMENT A
→ expects DATA RELEASE A

DEPLOYMENT B
→ expects DATA RELEASE B
```

A mutable global alias may exist for operators/discovery, but runtime correctness must not depend on it unless that mutability is itself the intended contract.

### 3. Pin interpretation topology when data identity is insufficient

Sometimes identical payload bytes can be interpreted differently when routing/topology/rules change.

In that case also pin an interpretation-plan fingerprint, for example:

```text
plan_id = hash(canonical normalized interpretation topology)
```

Only add this if topology compatibility is a real problem; do not hash everything by reflex.

### 4. Treat historical state explicitly

If persisted/signed jobs/sessions contain an older release/plan identity:

- continue under compatible historical interpretation if supported;
- explicitly restart/reconcile if safe;
- fail closed if the current code cannot interpret the old state safely.

Do not silently pretend historical state was created under the current plan.

### 5. Stage before activation

A useful rollout shape is:

```text
stage immutable data B
→ verify B
→ publish code deployment B pinned to B
```

If publication fails, deployment A still selects A; staged B remains unused.

### 6. Verify code/data agreement during build/deploy

Fail deployment if:

- expected release does not exist;
- required language/partition/assets are incomplete;
- embedded pin and deployment manifest disagree;
- topology fingerprint does not match canonical plan.

## Why it works

It replaces an implicit temporal dependency—"whatever is active when this request runs"—with explicit provenance between executable and interpreted data.

This makes rollback, staging, long-lived workflow compatibility, and deployment failure behavior easier to reason about.

## Trade-offs

- historical releases may need retention;
- operators must manage immutable artifacts and cleanup;
- pin changes become part of deployment workflow;
- live mutable configuration becomes less immediate;
- compatibility/restart policy for old state must be designed.

## Alternatives

Consider instead:

- embed the data entirely into the executable artifact;
- strict backward/forward-compatible data contracts with a mutable active pointer;
- runtime schema/version negotiation;
- feature/config service with explicit compatibility rules;
- blue/green databases or environment-level isolation;
- migrations that atomically update code and data when the platform truly supports it.

## Failure modes

- `latest`/`active` accidentally re-enters runtime selection;
- release ID is immutable but interpretation topology is not;
- old workflow/session state is interpreted under current rules without compatibility proof;
- data B becomes live merely because staging succeeded;
- rollback restores code but not compatible data;
- pins exist in documentation but deployment does not verify them.

## Verification

- deploy A continues selecting A after staging B;
- failed publication of B does not affect live A;
- successful B selects exactly B;
- rollback returns to compatible A selection;
- missing/incomplete pinned data fails before serving traffic;
- incompatible historical state follows the declared restart/reject/compatibility rule;
- any topology fingerprint is recomputed from canonical source rather than trusted from a copied value.

## Related Core Principles

- `exact-state-verification` — the deployment/data relation is an exact-state claim;
- `authority-mapping` — define who owns release selection and interpretation rules;
- `irreversible-boundary-reasoning` — staging, publishing, and activating may have different rollback semantics;
- `dependency-ownership` — data producer and deployment consumer need a stable contract without circular ownership.
