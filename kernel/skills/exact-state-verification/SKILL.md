# Exact-State Verification

## Purpose

Use this skill whenever a claim of correctness, review, compatibility, or readiness depends on a particular version of an artifact or system state.

## Goal

Prevent evidence from being silently carried from one state to another.

The central rule is:

```text
Evidence is evidence for the exact state that produced it.
```

Git commits are one common identity mechanism, but this skill is deliberately broader than Git.

## When to use

Use for:

- PR and branch verification;
- generated artifacts;
- database schemas and migration states;
- deployment candidates;
- container images;
- model/data versions;
- API/schema contracts;
- content/config bundles;
- compiled binaries;
- infrastructure plans;
- any workflow where "it passed earlier" can become misleading after state changes.

## Do not use when

Do not use this skill to:

- demand cryptographic identity for trivial local edits where simpler identity is sufficient;
- confuse reproducibility with correctness;
- replace semantic review;
- assume a commit SHA alone captures external dependencies or environment.

## Inputs

- claim being made;
- artifact/system under verification;
- available identity/version information;
- environment and external dependencies relevant to the claim;
- verification evidence.

## Required output

An evidence binding such as:

```text
claim
artifact identity
relevant dependency/input identities
environment
verification performed
result
state changes since verification
current validity
```

## Procedure

### 1. Identify the artifact precisely

Use the strongest practical identity already natural to the system, for example:

- Git commit SHA;
- content hash;
- build digest;
- schema version + migration history;
- immutable release ID;
- generated-file source revision;
- model + tokenizer/data revision;
- deployment revision;
- package lock digest.

Do not invent complexity when a stable version is already sufficient.

### 2. Bind evidence to the state actually tested

Record what was verified and against which exact state.

Bad:

```text
CI is green on this branch.
```

Better:

```text
CI run X succeeded for commit Y with lockfile Z.
```

Bad:

```text
Migration works.
```

Better:

```text
Fresh schema and upgrade path both passed through migration revision N.
```

### 3. Track material state changes

After evidence is collected, ask whether any change could invalidate the claim:

- code changed;
- dependency lock changed;
- generated artifact changed;
- schema changed;
- base branch changed materially;
- deployment configuration changed;
- external contract version changed;
- test itself changed;
- artifact was rebuilt from different inputs.

If yes, mark old evidence stale for the affected claim until revalidated.

### 4. Distinguish equivalent state from merely similar state

Two branches may point to the same tree/commit and therefore share some evidence.
Two deployments may use the same code but different config and not share runtime evidence.
Two schemas may have the same version label but different actual structure and not be equivalent.

Define equivalence for the claim being made rather than assuming it.

### 5. Verify integration state when relevant

For merge/release claims, branch-local proof may be insufficient if target/base state moved.

Delegate Git-specific provenance and merge drift mechanics to `git-branch-integrity` and `merge-preview-check`, but retain the broader law: the final claim must point to the exact candidate being accepted.

### 6. Treat test changes as evidence changes

A green run after weakening or changing the test is not the same proof as the earlier contract.

When verification logic changes, record whether the claim became:

- stronger;
- equivalent;
- weaker;
- different.

## Decision rules

- State identity must be strong enough for the claim, not maximally complicated.
- A changed artifact requires fresh evidence for claims affected by the change.
- "Same branch name" is not exact-state identity.
- "Same version string" is not enough if the system allows mutable contents under that version.
- Reused evidence is valid only when state equivalence is explicit and relevant.
- Review evidence, test evidence, and deployment evidence may bind to different state dimensions.

## Anti-patterns

Avoid:

- merging a different HEAD than the one reviewed/tested without revalidation;
- claiming a regenerated artifact is verified because its source once passed;
- treating a mutable `latest`/`active` pointer as immutable provenance;
- changing tests and quoting the old green run;
- assuming local and production configurations are equivalent without proof;
- carrying certification across a material dependency or schema change.

## Verification checklist

- [ ] The claim names the exact artifact/state.
- [ ] Relevant external inputs/config are included when they matter.
- [ ] Evidence is attached to that state, not only to a branch/name.
- [ ] Material changes since verification are known.
- [ ] Any reused evidence has an explicit equivalence argument.
- [ ] Final accepted/released state matches the state actually verified.

## Pair with

- `git-branch-integrity` for Git provenance;
- `merge-preview-check` for target-branch integration risk;
- `proof-loop-verification` for task completion evidence;
- `evidence-and-authority` for what the evidence can legitimately prove.
