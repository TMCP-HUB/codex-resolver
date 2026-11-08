# State Mutation, Revalidation, and Architecture Gate Protocol

## Controlled mutation

A role may propose state change only within its assignment. Acceptance requires the authority of the affected state domain and a durable mutation/decision record.

```text
CURRENT STATE
→ STATE_MUTATION_PROPOSAL
→ authority/evidence check
→ ACCEPT | REJECT | QUALIFY | OWNER_GATE
→ resulting durable state reference
```

No carrier edit, implementation result, verifier opinion, or chat message silently becomes accepted state.

## Shared-state revalidation invariant

Relevant shared-state change invalidates affected evidence/preconditions until one of the following is established:

- fresh verification against the new exact relevant state;
- explicit equivalence proof for the affected claim;
- rebuild/rebase/re-materialization as required;
- explicit stop/abandonment when correctness cannot be re-established.

Only affected proof is invalidated; unrelated evidence need not be discarded mechanically.

A universal exclusive lease is **not** required. A lease or serialization mechanism is an optional Solution Pattern when an operation's assumptions genuinely require exclusivity.

## Architecture reconsideration

Classify failures before reopening architecture:

1. **IMPLEMENTATION FAILURE** — architecture assumptions still hold; execution is wrong.
2. **LOCAL ARCHITECTURE DEFECT** — a seam/boundary/dependency is wrong without invalidating the whole architecture.
3. **INVALIDATED ARCHITECTURE ASSUMPTION** — evidence shows a foundational assumption is false.

Architecture Reconsideration Gates may be:

- **Reactive** — repeated evidence shows invalidated assumptions, persistent authority/scope leakage, unacceptable coupling, or temporary workarounds becoming permanent authority;
- **Planned** — before hard-to-reverse commitment such as durable production state/schema, public API, major cutover, or prototype→production transition.

Implementation difficulty alone is not a gate. Unexpected major conceptual change required by a bounded workstream is a stop and gate candidate, not permission for the Executor to redesign the system.
