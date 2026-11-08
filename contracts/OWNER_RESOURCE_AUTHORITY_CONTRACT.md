# Owner-Approved Resource Authority Contract

This contract is a bounded semantic extension of `contracts/RESOURCE_GOVERNANCE_CONTRACT.md`. It freezes how the existing `OWNER_DECISION_RECORD` artifact may act as the durable authority source for a `RESOURCE_GRANT` whose `authority_source.authority_type` is `OWNER_APPROVED_RESOURCE_AUTHORITY`.

It introduces no new artifact type, resource runtime, reservation mechanism, autonomy semantics, or Resolver behavior.

## Architectural law

```text
OWNER IDENTITY
!= OWNER RESOURCE AUTHORIZATION
```

```text
OWNER_DECISION_RECORD EXISTS
!= RESOURCE AUTHORITY
```

```text
RESOURCE_GRANT MAY REFERENCE AUTHORITY
BUT MAY NOT CREATE OR REINTERPRET AUTHORITY
```

A resource-authority decision must first be a fully schema-valid `OWNER_DECISION_RECORD` under `schemas/owner-decision-record.schema.json`. Structural validity is necessary but not sufficient. Resource authority exists only when the cross-artifact binding rules below are also proven.

## Canonical conditional vocabulary

The conditional Owner decision class is:

```text
decision_kind = OWNER_APPROVED_RESOURCE_AUTHORITY
```

This reuses the already-frozen Resource Governance authority-source vocabulary instead of inventing a second resource-authority decision family.

For an answer to presented options, the affirmative canonical Owner selection within this decision class is:

```text
selected_option = AUTHORIZE_RESOURCE_AUTHORITY
```

`AUTHORIZE_RESOURCE_AUTHORITY` must be one of the exact `options_presented` on the record. A resource-authority decision may still be a valid durable Owner record when its selected option is rejection, deferment, or another non-affirmative presented choice. Such a record does not authorize resource consumption.

An unambiguous direct Owner resource instruction may instead use
`resource_input_mode: DIRECT_INSTRUCTION` with the exact original Owner words
in `resource_interpretation.source_text`. It does not claim a question was
asked or options were presented and must not contain the option-response fields.
The actual authorized finite terms still bind the same grant below. A mere
mention or discussion of an amount is not permission to spend. Owner Interface
must not infer additional authority, attempt limits, expiry or route restrictions
from its own normalization; a narrower task scope must follow the actual
authorized work.

The resource-authority decision class conditionally requires:

```text
produced_by_role = owner-interface
status = RECORDED
authority_role = OWNER_K0
non_transitive = true
```

The `owner-interface` records the Owner's choice. It does not acquire Owner authority by producing the record.

## Structured finite authority binding

An affirmative resource-authority decision must bind the intended grant identity and every authority-bearing grant term needed to prevent Control from widening the Owner's choice after recording it.

The conditional `OWNER_DECISION_RECORD` fields are:

```text
authorized_resource_grant_ref : non-empty string
authorized_scope              : non-empty string
authorized_candidate_ref      : string | null
authorized_route_ref          : string | null
authorized_resource_classes   : non-empty unique RESOURCE_CLASS array
authorized_resource_limits    : non-empty RESOURCE_GRANT limit array
authorized_attempt_limit      : integer >= 1 | null
authorized_valid_until        : date-time string | null
authorized_finalization_policy: RESOURCE_GRANT finalization policy
```

Its common `assignment_id` and `input_state_ref` must be non-null, non-empty strings. Provenance and related-artifact lineage must be non-empty.

These fields freeze the finite resource authority itself. The Owner decision does not need an already-authorized `RESOURCE_GRANT` to exist first. Control may materialize the intended grant after the Owner decision, but only if the resulting grant matches the structured authority exactly. This avoids the invalid circular rule in which an already-authorized grant would be required to prove the authority needed to authorize itself. The explicit correction path below addresses an already registered grant that was recorded incorrectly.

`authorized_resource_grant_ref` binds the exact intended `RESOURCE_GRANT.artifact_id`; it is not, by itself, sufficient authority.

## Exact target and context equality

For a grant `G` and Owner decision `D`:

```text
D.authorized_resource_grant_ref == G.artifact_id
D.assignment_id                 == G.assignment_id
D.input_state_ref               == G.input_state_ref
D.authorized_scope              == G.scope.scope_ref
D.authorized_candidate_ref      == G.scope.candidate_ref
D.authorized_route_ref          == G.scope.route_ref
```

The equality above includes `null`: the Owner record and the grant must carry
the same candidate and route values. For an established Owner authority, a
`null` candidate or route means that field adds no separate candidate or route
restriction within the actual authorized scope. It does not authorize work
outside that scope or remove other grant conditions. A concrete non-null value
continues to bind that field exactly.

Owner Interface must use the actual Owner source and authorized work to
determine the scope. A genuinely unresolved material candidate or route
condition belongs in the existing `unresolved_constraints` or
`unresolved_qualifications`, rather than being treated as general authority.
Do not invent a restriction or repeat an Owner decision merely because a
restriction was not stated. Neither `null` nor empty unresolved arrays prove
that arbitrary Owner language was correctly understood.

The current admission path requires a concrete route and state identity. A
`null` grant field does not express an operation with exactly no route or
candidate.

Resource-class equality is set equality because order carries no authority meaning:

```text
set(D.authorized_resource_classes)
==
set(G.scope.resource_classes)
```

Resource-limit equality is semantic equality keyed by:

```text
(resource_class, dimension)
```

Each side must contain at most one limit for a key. For every key, `limit_mode`, `ordinary_limit`, and `finalization_reserve` must be equal. Reordering the array does not change authority; duplicate or competing keys fail closed.

Before Owner binding is considered, the grant itself must satisfy the frozen Resource Governance authority-shape semantics. In particular, every limit resource_class belongs to scope.resource_classes:

```text
{limit.resource_class for limit in G.limits}
⊆
set(G.scope.resource_classes)
```

A declared scope class does not need its own limit entry. The inverse is forbidden: a limit may not introduce a resource class that the grant scope did not declare. A structurally schema-valid grant that violates this invariant cannot establish Owner resource authority, even if the Owner record mirrors the same invalid limit.

The remaining finite terms must match exactly:

```text
D.authorized_attempt_limit       == G.attempt_limit
D.authorized_valid_until         == G.valid_until
D.authorized_finalization_policy == G.finalization_policy
```

For `authorized_finalization_policy.allowed_purposes`, equality is set equality. `protected` must remain `true` as required by the grant schema. Validity timestamps compare the same UTC instant, regardless of equivalent offset spelling.

The authority decision therefore binds the grant's finite amount, enforcement modes, protected finalization reserve, allowed finalization purposes, resource classes, attempts, lifetime, assignment, input state, scope, candidate, and route. `RESOURCE_GRANT` envelope fields already fixed by its schema (`produced_by_role`, `issued_by`, and `status`) are not duplicated into the Owner record.

## Cross-artifact authority predicate

For a `RESOURCE_GRANT` `G` to derive authority from an Owner decision `D`, every statement below must be true:

1. `G` is structurally valid under `schemas/resource-grant.schema.json` and satisfies the complete frozen Resource Governance semantic invariants relevant to its authority shape, including unambiguous `(resource_class, dimension)` limit keys and the rule that every `G.limits[*].resource_class` belongs to `G.scope.resource_classes`.
2. `G.authority_source.authority_type == OWNER_APPROVED_RESOURCE_AUTHORITY`.
3. `G.parent_grant_ref == null`; delegated child authority belongs to `PARENT_RESOURCE_GRANT`.
4. `G.authority_source.authority_ref` resolves to exactly one durable artifact `D`.
5. `D` is structurally valid under the current `schemas/owner-decision-record.schema.json`; reduced fixtures or prose-only substitutes are not authority.
6. `D.artifact_type == OWNER_DECISION_RECORD`.
7. `D.produced_by_role == owner-interface`.
8. `D.status == RECORDED`.
9. `D.authority_role == OWNER_K0`.
10. `D.decision_kind == OWNER_APPROVED_RESOURCE_AUTHORITY`.
11. Either the actual response selects `AUTHORIZE_RESOURCE_AUTHORITY` from the presented options, or it is an unambiguous direct resource instruction using the conditional direct form and preserving the exact source text.
12. `D.non_transitive == true`.
13. `D.authorized_resource_grant_ref == G.artifact_id`.
14. `D.assignment_id == G.assignment_id`.
15. `D.input_state_ref == G.input_state_ref`.
16. `D.authorized_scope == G.scope.scope_ref`.
17. `D.authorized_candidate_ref == G.scope.candidate_ref`.
18. `D.authorized_route_ref == G.scope.route_ref`.
19. `D.authorized_resource_classes` equals `G.scope.resource_classes` under the set-equality rule above.
20. `D.authorized_resource_limits` equals `G.limits` under the keyed semantic-equality rule above.
21. `D.authorized_attempt_limit == G.attempt_limit`.
22. `D.authorized_valid_until == G.valid_until`.
23. `D.authorized_finalization_policy` equals `G.finalization_policy` under the rule above.
24. `D.related_artifacts` contains `G.artifact_id`.
25. `G.authority_source.authority_ref == D.artifact_id`.
26. A decision with non-empty constraints or qualifications requires an interpretation, either recorded with the original decision or separately linked as described below. Without an interpretation, constraints are empty and qualifications are absent or empty. The interpretation used for admission has empty `unresolved_constraints` and `unresolved_qualifications`; any condition removed from the original interpretation is linked to its confirmed assessment and evidence as described below.

Failure or inability to prove any one of these statements means the Owner-approved resource authority is not established.

## Owner constraints and qualifications

`owner_constraints` and `qualifications` remain faithful records of the Owner's words, not an implementation language for hidden resource authority.

For resource authority, Owner Interface may preserve the original words and original constraints while recording a `resource_interpretation`: structured authorized scope/limits carry the faithfully represented terms, and its two unresolved arrays carry the remaining conditions and qualifications. A direct instruction requires this interpretation. Without an interpretation, the legacy empty-constraints rule remains. Admission rejects a non-empty unresolved array in the interpretation it uses; an earlier source may retain its original entries as described below.

Only when the Owner actually authorizes a single total across resource classes, the interpretation may contain `shared_limits`: the limit identity, dimension, covered classes, total and optional protected finalization reserve. A total covering the whole task includes all actually authorized classes in that dimension and their relevant child operations; a narrower set requires the Owner's actual scope. An omitted reserve is zero, and a specified reserve is part of the total. These entries do not change a registered grant or create a second budget. The existing ledger must bind the recorded total before reservations can enforce it.

When an already-recorded decision needs normalization, preserve that original
record and its ID. A separate derived `OWNER_DECISION_RECORD` uses a different
ID, links the original in `related_artifacts`, and preserves all original fields
apart from record identity, lineage and the derived interpretation. An absent
optional `qualifications` and an empty array have the same canonical meaning;
equivalent JSON numbers retain the same value. Authorized resource classes,
keyed limits and allowed purposes use the existing set/key equality rules, and
equivalent expiry timestamps denote the same UTC instant. Its `resource_interpretation`
is supplied to the existing admission path via optional
`resource_interpretation_ref`. Admission resolves and compares both records;
the grant's original authority reference and registered budget remain unchanged.
The derived record is not a new Owner approval or another resource grant.
One complete linked interpretation may contain several Owner-authorized shared
groups. Admission evaluates each applicable group separately and the existing
ledger selects that complete interpretation in one transaction. Initial
normalization preserves structured original groups; another technical ID
does not establish an additional limit.
If normalization is needed, the existing Owner Interface prepares one complete
interpretation from the original words; `resource_interpretation_ref` identifies
it. Different dimensions and genuinely authorized overlapping limits remain
distinct groups. A previously bound ref remains usable from the ledger.
If the responsible Owner Interface or Director finds that the selected view
misstates the same original decision, they may prepare a corrected complete
linked interpretation after reviewing that real source. The ledger exposes the
selected snapshot and source fingerprint and replaces the view only when both
still match in its write transaction. An explicitly corrected empty set is a
selection too. The selected and prior source/view refs are retained as lineage;
the grant and recorded Owner words are not rewritten. This path relies on the
responsible actor's source assessment and does not itself interpret the words.
To correct an already registered per-class limit, the responsible actor checks
the same real Owner source and chooses a complete corrected view. If the
original structured Owner limits are right, that record can supply them; if
they are wrong too, a linked interpretation may correct those specific terms
after the actor assesses the original source. It preserves the original words,
other authority terms, conditions and selected shared groups. The original
Owner record and grant remain unchanged.

The existing ledger records the prior and corrected per-class values and source
lineage in its selected Owner view. It compares the reviewed original grant,
source, previous selection, active limits and candidate view in one write
transaction, then uses the corrected limits with the original grant identity
and all existing reservations and consumption. Admission compares the original
grant artifact with its registered original and checks the Owner authority
against that same effective ledger view. A correction does not create another
budget or automatically enlarge child grants. The recorded assessment and
fingerprints cannot establish the source's authenticity or interpret its words.
Do not rewrite an already-recorded decision under the same ID to add an
interpretation; a newly recorded option response may include its initial
interpretation. Admission cannot itself tell initial content from a replacement.

This relies on the existing durable resolver to supply the authentic original
record. A selected view retains fingerprints of the supplied source and view;
these support consistency and correction, but do not authenticate the record or
prove that an earlier supplied source was authentic.

An unresolved condition is not satisfied by a reference alone. The existing owner of the applicable fact must establish it before the semantic intake records it as resolved, with the real evidence retained. The code compares typed grant terms and checks the unresolved arrays; it cannot prove from an empty array or an inline quotation that a model correctly understood every condition in arbitrary Owner language. Ambiguous, unrepresented or genuinely unresolved conditions remain non-admissible rather than being discarded.

An original interpretation may already list a condition that was later
established. Its linked interpretation can identify that exact original entry
using `condition_resolutions`: the condition kind (`CONSTRAINT` or
`QUALIFICATION`), zero-based index in the corresponding original array, and
the relevant non-empty `evidence_refs`. The responsible Owner Interface actor
records an entry only after establishing that this particular condition is
satisfied. An optional note can preserve the rationale. Indexes refer to the
unchanged original record, so identical text in two entries does not merge them.
Every removed original entry needs a link; any remaining unresolved entry
continues to block admission.

Where an existing Director review or Verification result is actually used,
the entry may additionally carry its `review_ref` and `claim_id` together.
Admission checks the confirmed review, claim, evidence references, and the
review's own Executor-result identity. An assessment made for another
assignment need not share the grant's task or state identity. A separate
Executor result or Verifier is not required for a direct Owner Interface
assessment.

The responsible actor must inspect the actual sources and establish their
applicability and freshness for the condition. Admission reuses that assessment;
it does not reread source payloads, establish the identity of the actor, or
prove the meaning or truth of external data or Owner language. A reference or
an entry alone does not establish that the underlying fact was actually read
or correctly assessed. If fresh/durable readback or a separate Verifier was
already required for that fact, its existing responsible actor fulfills that
requirement. No new Owner question, verifier or service is introduced.

Provenance text, consequence prose, question wording, or generic strings must never be parsed to manufacture missing resource authority.

## Fail-closed semantics

The following never constitute Owner-approved resource authority:

- an unresolved, fake, ambiguous, or non-unique `authority_ref`;
- a schema-invalid or partial Owner decision object;
- an Owner record produced by another role;
- a non-`RECORDED` Owner record;
- a record without `OWNER_K0` authority role;
- an unrelated Owner decision, including Canon, deployment, architecture, human-research, or another resource grant;
- an option-response resource decision whose selected option is not `AUTHORIZE_RESOURCE_AUTHORITY`;
- a decision targeting another resource grant;
- assignment or input-state mismatch;
- scope, candidate, or route mismatch, including `null` versus non-`null` mismatch;
- a grant limit whose `resource_class` is not declared by `scope.resource_classes`;
- resource-class, finite-limit, attempt-limit, validity, or finalization-policy mismatch;
- duplicate/ambiguous limit keys;
- missing structured resource-authority binding;
- a non-empty unresolved condition/qualification, or legacy constraints without a valid interpretation;
- provenance/question/consequence text that merely claims Owner approval;
- a `RESOURCE_GRANT` referring to itself as authority.

`RESOURCE_GRANT` is never permitted to satisfy the `OWNER_DECISION_RECORD` side of this predicate. A grant may cite authority but may not bootstrap that authority from its own existence, status, provenance, or fields.

## Non-transitivity and parent grants

An Owner decision of this class authorizes only its exact `authorized_resource_grant_ref` with exactly the structured finite authority recorded above. It is non-transitive.

Delegated child resource authority must continue to use the already-frozen `PARENT_RESOURCE_GRANT` authority-source family and satisfy the Resource Governance parent/child monotonicity laws. A child grant must not reuse the root Owner decision as if the Owner had independently authorized the child.

## Compatibility

This is a conditional specialization of the existing `OWNER_DECISION_RECORD` schema. It does not make every Owner decision a resource decision.

Existing non-resource Owner decision records remain valid under their existing rules. Canon, human-research, deployment, architecture, and other Owner decision flows do not gain resource authority merely because they are valid Owner records.

No prose field, provenance string, generic `question_ref`, generic `authorized_scope`, or artifact existence by itself may be reinterpreted as resource authority.

## Downstream ownership

`tools/resource_admission.py` and `tools/resolver_spawn.py` consume this
predicate. This contract does not itself perform reservation, spending,
estimation, provider execution, or implement PAC, TICKET, or autonomy envelopes.

If a downstream validator cannot prove the predicate from exact durable artifacts, it must return a non-admissible/fail-closed result under the Resource Governance contract rather than infer Owner authorization.
