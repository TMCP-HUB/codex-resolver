# Legacy Schema Adoption

> Classification: **Solution Pattern — optional**. This is one way to bring an existing manually-created or historically migrated database under a modern migration system without pretending its past was cleaner than it was.

## Problem class

A production database already has tables/indexes/data before the current migration tool/history exists. The project needs to adopt that real baseline safely and then continue with native migrations.

## Production trace

This pattern came from a deployment where legacy tables had been created before native migration history was authoritative. The safe transition required proving the actual SQLite constraints and adopting only a recognizable contiguous historical prefix before future migrations could proceed normally.

## Assumptions

- an existing production schema must be preserved;
- the migration tool has its own history mechanism;
- the legacy baseline is finite and can be described precisely;
- schema introspection is available;
- malformed/partial historical states must fail safely.

## Use when

Use when:

- migrations are being introduced after manual production changes;
- a previous deploy process applied schema without native history;
- the database must not be recreated from scratch;
- multiple environments may contain slightly different historical states;
- one-time adoption can be isolated from future migration behavior.

## Do not use when

Prefer simpler approaches when:

- the database can safely be rebuilt;
- migration history is already trustworthy;
- a vendor-supported baseline/import command solves the problem;
- the historical schema is too inconsistent to prove safely and a deliberate data migration/cutover is clearer;
- production downtime allows an explicit export/recreate/import path.

## Pattern

### 1. Describe the historical baseline exactly

Record the expected legacy prefix:

```text
legacy migration 1
legacy migration 2
legacy migration 3
```

Also record the actual schema invariants those migrations imply.

Do not rely only on migration filenames that were never recorded in production.

### 2. Introspect the real schema

Verify structural facts such as applicable:

- table/column existence;
- primary-key order;
- nullability;
- unique constraints;
- indexes and partial predicates;
- foreign keys;
- check constraints;
- expected legacy columns.

Use the database's actual introspection facilities rather than parsing CREATE TABLE text when stronger structured metadata exists.

### 3. Accept only a contiguous recognized prefix

If the real schema proves legacy states 1..N, adopt exactly that prefix into native migration history.

Reject cases such as:

```text
legacy 1 exists
legacy 2 missing
legacy 3 appears partially applied
```

Do not fill migration history merely because the current tables look close enough.

### 4. Fail closed on malformed variants

Build negative fixtures/cases for the dangerous near-matches:

- wrong PK order;
- missing UNIQUE;
- partial index masquerading as table-wide uniqueness;
- wrong nullability;
- wrong predicate;
- unexpected extra legacy column when that matters.

Adoption logic should prove identity, not similarity.

### 5. Make adoption one-way and finite

Once native migration history extends beyond the historical adopted prefix:

```text
legacy schema proof no longer governs future migration semantics
```

Future migrations may intentionally reshape old tables without forcing the adopter to keep recognizing every new schema.

### 6. Test fresh and adopted paths

Prove both:

```text
fresh empty database
→ native migrations
→ current schema
```

and

```text
recognized legacy database
→ adopt prefix
→ remaining native migrations
→ current schema
```

### 7. Prove replay safety

Re-running the migration command should not duplicate history or reapply already adopted work.

## Why it works

It treats the real production schema as evidence that must be proven before inventing migration history. After one finite bridge, the project returns to normal native migration ownership instead of carrying permanent legacy special cases.

## Trade-offs

- baseline proof can be database-specific;
- exact constraint inspection takes effort;
- malformed historical environments may require manual remediation;
- adoption tests must be maintained until the bridge is retired;
- very large/divergent legacy schemas may be better handled by explicit cutover.

## Alternatives

Consider instead:

- rebuild/reseed the database;
- vendor migration-baseline/import commands;
- export → new schema → transform/import;
- blue/green database cutover;
- one-off manual migration with explicit operational certification;
- dual-read/write migration for systems that cannot stop.

## Failure modes

- writing native migration history without proving schema;
- checking only table names while constraints differ;
- allowing non-contiguous historical prefixes;
- adoption code remains coupled forever to current/future schemas;
- migration smoke tests use only fresh databases and never the real legacy shape;
- concurrent local migration tests create tool/database-lock noise mistaken for schema defects.

## Verification

- fresh database reaches current schema;
- exact recognized legacy baseline adopts safely;
- malformed near-matches fail closed;
- migration history is contiguous and replay-safe;
- future native migration beyond legacy prefix no longer requires the old baseline verifier to understand the reshaped schema;
- production deployment path uses the same migration source/order tested in CI or local proof.

## Related Core Principles

- `exact-state-verification` — adoption claims must match the real schema state;
- `evidence-and-authority` — migration history labels are not enough without mechanical schema evidence;
- `irreversible-boundary-reasoning` — production migration/cutover has real rollback boundaries;
- `dependency-ownership` — one migration owner should govern the shared schema transition.
