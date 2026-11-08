# Versioned Signed State Envelope

> Classification: **Solution Pattern — optional**. This is one proven way to carry compact trusted state through an untrusted client. It is not the default persistence architecture for every application.

## Problem class

A client must carry a small amount of state between requests, but the client must not be able to forge or silently rewrite the trusted parts of that state.

Typical examples include compact session provenance, bounded workflow coordinates, authority flags, version identifiers, or references to larger server/local state.

## Production trace

This pattern was extracted from a long-lived stateful web flow where a signed client-carried envelope evolved across several schema revisions while multiple subsystems needed to preserve one another's fields and the total transport size had a hard upper bound.

## Assumptions

- the client is allowed to possess the state but not forge trusted fields;
- the trusted payload is compact and bounded;
- server-side signing/verification material is available;
- the application can define explicit schema versions and migration/normalization rules;
- replay/confidentiality requirements are addressed separately if needed.

## Use when

Use this pattern when:

- stateless or mostly-stateless request handling is valuable;
- trusted state is small enough to fit the chosen transport safely;
- the server wants to avoid a lookup for every request;
- old client-carried state may survive deployments and needs deterministic normalization;
- several features share one compact envelope and field preservation matters.

## Do not use when

Prefer another design when:

- the state is large, unbounded, or document-like;
- confidentiality is required but the chosen envelope is only signed, not encrypted;
- immediate server-side revocation is essential and cannot be modeled separately;
- the data changes frequently from multiple writers;
- a normal server-side session/database lookup is simpler;
- the state is merely a non-sensitive user preference and does not need integrity protection.

## Pattern

### 1. Define one current normalized shape

All supported input versions normalize into exactly one current in-memory representation before mutation.

```text
encoded vN
→ verify integrity
→ decode
→ normalize to CURRENT
→ perform typed mutation
→ encode CURRENT
→ sign
```

Do not let feature code mutate arbitrary historical shapes directly.

### 2. Version explicitly

Include an explicit schema/envelope version.

For every supported previous version:

- define deterministic field mapping;
- define defaults for fields that did not exist;
- never pretend an old version carried provenance it could not have known;
- fail safely on unknown/incompatible versions.

### 3. Keep field ownership typed

Each subsystem mutates only the fields it owns and preserves unrelated fields from the normalized current shape.

Bad pattern:

```text
feature A reconstructs the entire envelope from its local partial interface
→ fields owned by B/C disappear
```

Preferred:

```text
normalize full current envelope
→ apply A-owned mutation
→ preserve B/C fields
```

### 4. Keep the envelope compact

Store authority/provenance/references, not arbitrary runtime history.

Good envelope candidates:

- current revision/position;
- compact flags;
- immutable release/config identity;
- short bounded pending state;
- references/hashes to larger durable state.

Poor candidates:

- full transcripts;
- entire navigation/history trees;
- large documents;
- unbounded queues;
- arbitrary cached API responses.

### 5. Measure worst-case transport size

Budget for the largest supported valid envelope, including signing/encoding/header overhead where relevant.

Fail or degrade **before** transport serialization becomes unreliable.

### 6. Separate integrity from other properties

A signature proves integrity/authenticity under the signing key. It does not automatically provide:

- confidentiality;
- freshness;
- revocation;
- single-writer semantics;
- replay prevention.

Add those only if the problem requires them.

## Why it works

- every mutation starts from one canonical normalized representation;
- explicit versioning makes old state semantics inspectable rather than guessed;
- signatures prevent undetected client tampering with trusted fields;
- typed field ownership prevents unrelated features from erasing each other;
- hard size boundaries prevent convenience state from growing into an accidental database.

## Trade-offs

- payload size travels with requests;
- signing key management becomes security-critical;
- revocation can be harder than with server-only state;
- schema evolution requires disciplined normalization tests;
- many independent writers can make a client-carried envelope awkward;
- confidentiality requires encryption or a different design.

## Alternatives

Consider instead:

- opaque session ID + server-side session store;
- database-backed workflow/session state;
- encrypted tokens/envelopes when confidentiality is required;
- short-lived bearer tokens with server-side state elsewhere;
- unsigned local preferences for non-sensitive, non-authoritative UI state;
- stateless recomputation from durable source data.

## Failure modes

- envelope silently becomes an unbounded runtime database;
- feature mutation drops fields it does not own;
- version migration invents provenance that old versions never possessed;
- unknown versions are interpreted optimistically;
- cookie/header/token limits are tested only for happy-path size;
- signed state is mistaken for secret/encrypted state;
- stale signed state is allowed to overwrite newer authoritative state without reconciliation.

## Verification

- round-trip current encode/decode;
- normalize every supported historical version;
- unknown/incompatible version fails safely;
- cross-feature mutation preserves unrelated fields;
- tampering fails verification;
- worst-case encoded size remains below the declared transport budget;
- tests prove large runtime/history payloads are not serialized into the envelope;
- stale/concurrent behavior is covered separately if relevant.

## Related Core Principles

- `authority-mapping` — decide which fields are truly authoritative before signing them;
- `exact-state-verification` — bind the envelope to immutable release/config identities when needed;
- `irreversible-boundary-reasoning` — do not use envelope retry semantics to replay already-committed effects;
- `evidence-and-authority` — signing success proves integrity, not all business correctness.
