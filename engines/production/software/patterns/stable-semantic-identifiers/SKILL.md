# Stable Semantic Identifiers

> Classification: **Solution Pattern — optional**. This is one way to keep references stable across rendering, translation, storage, rebuilds, and refactors. It is unnecessary when positional identity is genuinely stable and local.

## Problem class

Several systems need to refer to the same logical item, but physical positions such as line number, DOM index, array offset, database auto-increment order, or translated text are unstable.

## Production trace

This pattern came from a multilingual content/runtime system where delivery chunks, presentation metadata, gates, history, diagnostics, and later translations all needed to point to the same logical blocks without matching prose or DOM positions.

## Assumptions

- logical entities survive representation changes;
- multiple consumers need durable references;
- positional identity can drift;
- identifiers can be assigned/generated deterministically enough for the project.

## Use when

Use when:

- translated/localized variants must share topology;
- UI metadata references content across renders;
- history/checkpoints need durable anchors;
- generated artifacts are rebuilt from source;
- multiple systems bind to the same conceptual object;
- refactors should not invalidate external references.

## Do not use when

Prefer simpler positional references when:

- the reference is strictly local and ephemeral;
- the collection order is itself the authoritative identity;
- consumers and producer are rebuilt atomically and no durable reference escapes;
- assigning semantic IDs would create meaningless bureaucracy.

## Pattern

### 1. Identify the semantic object

Name what survives representation changes:

- section;
- scene;
- field;
- command;
- checkpoint;
- media cue;
- domain entity;
- configuration item.

Do not create an ID for every line merely because IDs are fashionable.

### 2. Assign identity at the authoritative source boundary

Prefer IDs that originate where the logical object is defined, not inferred later from rendered output.

Bad:

```text
find paragraph containing exact sentence X
→ attach metadata
```

Better:

```text
source block id = content.chapter-03.section-02
→ renderer/translation/storage preserve binding
```

### 3. Keep identity independent from display text

Labels, translations, titles, CSS selectors, and DOM positions may change while semantic identity stays stable.

### 4. Define namespace and uniqueness rules

Specify:

- namespace/prefix if useful;
- uniqueness scope;
- case/normalization rules;
- whether IDs are human-authored, generated, or hashed;
- whether renaming is allowed;
- alias/migration policy for legacy IDs.

### 5. Validate references fail closed

Where references carry correctness:

- unknown IDs fail validation;
- duplicate IDs fail validation;
- references to the wrong entity type fail when types are available;
- ordering constraints are verified separately if order matters.

### 6. Keep physical coordinates diagnostic

Line number, DOM position, byte offset, storage row, or array index can still be useful for debugging. Treat them as location metadata, not durable identity unless the system explicitly guarantees stability.

## Why it works

It decouples logical identity from presentation/storage position, allowing multiple representations to evolve without forcing consumers to scrape unstable output.

## Trade-offs

- IDs become part of long-lived compatibility surface;
- renaming requires discipline;
- generated IDs need deterministic rules;
- humans may need tooling to avoid duplicate/missing identifiers;
- over-identifying tiny objects can add noise.

## Alternatives

Consider instead:

- natural domain keys already present in the data;
- content hashes when identity should change with content bytes;
- database primary keys for strictly database-local entities;
- JSON Pointer/path references when structural path is stable by contract;
- positional offsets for ephemeral one-process work;
- explicit mapping tables between independently owned schemas.

## Failure modes

- IDs are derived from translated/display text;
- auto-increment IDs leak into a contract where rebuild order can change;
- duplicate IDs silently resolve to first match;
- consumer reconstructs identity from DOM/prose because provider omitted IDs;
- an ID is reused for a semantically different object;
- ID stability is assumed but no migration policy exists.

## Verification

- rebuild/reorder that should preserve semantics preserves IDs;
- translation/display changes do not break references;
- unknown/duplicate/mistyped references fail validation where required;
- consumer can bind without prose/DOM matching;
- deliberate semantic replacement either gets a new ID or follows explicit migration policy;
- identifiers are not more stable than the project actually promises.

## Related Core Principles

- `authority-mapping` — assign IDs at the source that owns the semantic object;
- `dependency-ownership` — providers expose stable references consumers can depend on;
- `exact-state-verification` — distinguish stable semantic identity from immutable content identity.
