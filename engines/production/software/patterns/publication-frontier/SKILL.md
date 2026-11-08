# Publication Frontier

> Classification: **Solution Pattern — optional**. This is one way to enforce that data already delivered or prefetched is not yet allowed to become user-visible/published state. It is unnecessary when delivery itself already enforces the disclosure boundary.

## Problem class

A client may already possess future data for efficiency, batching, offline support, or protected delivery, but later items must not appear in the observable UI/DOM/state before the application reaches the corresponding publication boundary.

Core distinction:

```text
DELIVERED != PUBLISHED
```

## Production trace

This pattern came from a reader/runtime where one protected packet could physically contain later content while the current scene still owned the visible publication boundary. Correctness required exactly one active frontier lease and a fail-closed audit against premature future markup.

## Assumptions

- delivery/prefetch may legitimately precede visibility;
- premature publication is a correctness, privacy, reveal, or workflow defect;
- the application has explicit semantic units or steps;
- presentation completion can be observed well enough to release the frontier.

## Use when

Use when:

- content is prefetched in larger packets than it is revealed;
- a wizard/workflow must not expose future steps despite local availability;
- progressive disclosure matters for exams, games, training, protected documents, or staged UI;
- later state may exist in memory but not yet in DOM/public projection;
- one current unit should exclusively own the publication boundary.

## Do not use when

Prefer a simpler design when:

- the server sends only the exact next authorized unit;
- future data may safely be visible as soon as delivered;
- encryption/key release already enforces the boundary;
- the whole dataset is intentionally public and disclosure order is presentation-only;
- adding client-side frontier state would merely duplicate a stronger server-side gate.

## Pattern

### 1. Separate delivery eligibility from publication eligibility

Track them independently.

```text
packet/unit received
→ DELIVERED

semantic/application boundary satisfied
→ eligible to claim publication frontier
```

Do not infer publication from network completion.

### 2. Use one explicit active frontier owner

Represent the current publication lease, for example:

```text
frontier.active_unit_id = X
```

Rules may include:

- one unit claims at a time;
- re-claim by the same unit may be legal for retry/continuation;
- a different unit fails closed while the frontier is occupied.

### 3. Claim before publishing observable state

Before creating future-visible DOM/projection/output:

```text
claim frontier
→ publish current unit
→ complete required presentation lifecycle
→ release frontier
```

If claim fails, do not publish and hope to reconcile later.

### 4. Release only after the real completion boundary

Domain execution being ready may not mean presentation is complete.

Choose the boundary the product actually requires:

- DOM mounted;
- animation/typing settled;
- user acknowledgement completed;
- accessibility announcement committed;
- external presentation side effect finished.

Pair with `presentation-completion-barrier` when this distinction is non-trivial.

### 5. Audit the observable surface

Where premature disclosure is important, inspect the actual public surface—not only internal state.

Examples:

- DOM subtree;
- serialized client projection;
- public API payload;
- rendered accessibility tree proxy/test;
- generated static artifact.

Reject known future semantic IDs/content appearing before their frontier.

### 6. Define retry/resume behavior

A failed current unit may reuse/reset its existing frontier rather than append a duplicate.

Resume may need to reconstruct minimal presentation context without reconstructing or publishing unreached content.

### 7. Define consumption separately from completion

If completed units later collapse/remove from DOM for performance, do that under a separate consumption rule. Do not equate "presentation complete" with "delete immediately" unless that is the intended UX.

## Why it works

The pattern makes publication a first-class state transition instead of an accidental side effect of delivery. The lease serializes disclosure while allowing transport/prefetch to remain efficient.

## Trade-offs

- adds client/application coordination state;
- presentation failures need recovery semantics;
- DOM/public-surface audits can be brittle if based on unstable positions;
- prefetch still exposes bytes to a sufficiently privileged client unless stronger protection is used;
- one-frontier serialization may be too restrictive for independently publishable regions.

## Alternatives

Consider instead:

- server-side incremental delivery of only currently authorized data;
- per-unit encryption/key release;
- independent region-specific publication gates;
- route/page-level navigation where each page fetches its own data;
- fully public preload with no semantic disclosure restriction;
- streaming protocols that never transmit future units early.

## Failure modes

- delivered packet contents are rendered wholesale before frontier checks;
- a second unit publishes while the first still owns the frontier;
- runtime/domain completion releases frontier before presentation actually finishes;
- retry appends duplicate visible units;
- resume reconstructs future content to rebuild context;
- internal "published" flag is green while future DOM/projection already leaked;
- frontier is treated as a security boundary even though future bytes are already readable by the client.

## Verification

- one delivered packet containing multiple semantic units exposes only the reached/current unit;
- competing unit cannot publish while frontier is owned;
- same-unit retry does not duplicate observable output;
- frontier releases only after declared presentation completion;
- forced completion failure prevents next unit publication;
- observable-surface audit detects injected future unit/metadata;
- resume/reload follows declared reconstruction policy without revealing unreached content;
- tests/documentation state clearly whether this is a presentation boundary or a confidentiality/security boundary.

## Related Core Principles

- `authority-mapping` — define who decides publication eligibility;
- `stable-semantic-identifiers` — optional pattern for durable unit references;
- `irreversible-boundary-reasoning` — publication may become an observable effect that recovery must respect;
- `exact-state-verification` — audits should target the actual candidate surface.
