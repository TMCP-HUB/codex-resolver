# Architectural Dependency Fence

> Classification: **Solution Pattern — optional**. This is one proven way to make a high-value architectural prohibition executable with a narrow negative guard. It is not a reason to encode every design preference as a brittle static rule.

## Problem class

An architecture depends on a negative invariant such as "presentation must not import the canonical store", "observer code must not call mutation services", or "module A must not depend on module B". Documentation and review alone can drift because the forbidden path remains mechanically possible.

## Production trace

This pattern came from production systems where authority boundaries were clear in design but broad technical capability/import paths still made bypass possible. Small executable guards that failed on forbidden dependencies made the architecture's negative space observable before runtime defects or ownership drift accumulated.

## Assumptions

- the prohibited dependency/capability is stable enough to state precisely;
- violating it would materially weaken correctness, security, ownership, or maintainability;
- the forbidden relation can be detected with a reasonably stable mechanical signal;
- the guard can avoid coupling to irrelevant formatting/implementation detail;
- there is an explicit exception/change process when the architecture legitimately evolves.

## Use when

Use when:

- a non-owner module must not directly access an authoritative store/service;
- read-only/observer layers must not gain mutation dependencies;
- package/module boundaries are central to correctness;
- generated/runtime code must not depend on a forbidden layer;
- a regression has already shown that prose-only boundaries are too easy to bypass.

## Do not use when

Prefer another approach when:

- the rule is a temporary preference rather than an invariant;
- the mechanical signal is too brittle and would create constant false positives;
- the architecture intentionally permits the dependency under ordinary conditions;
- an existing compiler/package/module system already enforces the boundary reliably;
- the guard would freeze a specific file layout rather than the semantic prohibition.

## Pattern

### 1. State the semantic prohibition first

Example:

```text
Observer code may read detached snapshots but may not depend on mutation-capable domain services.
```

Do not start from a grep rule and infer architecture from it.

### 2. Identify the narrowest reliable signal

Possible signals include:

- forbidden import/package dependency;
- disallowed runtime binding/capability;
- forbidden API symbol/type;
- dependency graph edge;
- generated manifest relation;
- build target linkage.

Choose the signal that best represents the semantic rule with the least incidental coupling.

### 3. Add a negative guard

The guard should fail when the forbidden relation appears and pass when it is absent from the declared observation universe.

Examples:

- dependency graph assertion;
- package lint boundary;
- static import scan;
- configuration/binding allowlist;
- architecture test.

### 4. Declare the observation universe

Record what the guard actually scans:

```text
all source modules under X
all production bindings in Y
all package dependencies in Z
```

"No match" only proves absence inside the checked universe.

### 5. Keep exceptions explicit

If an exception is genuinely required, change the architectural rule or encode a narrow documented exception. Do not teach developers to bypass/disable the guard locally.

### 6. Keep the guard semantic

Prefer durable package/module/capability relations over fragile line text when possible.

When text scanning is the only practical option, include tests/fixtures that demonstrate both allowed and forbidden cases so the guard's meaning remains visible.

### 7. Pair with positive ownership evidence

A negative fence proves a forbidden edge is absent; it does not by itself prove the remaining architecture has the correct owner. Use `authority-mapping` / `dependency-ownership` for the positive relation.

## Why it works

It turns an important "must not" rule into repeatable evidence and shortens the feedback loop when architecture drifts. The fence preserves an already-chosen ownership boundary without becoming the owner of that boundary.

## Trade-offs

- guard maintenance as architecture evolves;
- false positives if the signal is too syntactic;
- false confidence if the observation universe is incomplete;
- too many fences can make refactoring unnecessarily rigid;
- exception processes can become cumbersome.

## Alternatives

Consider instead:

- package/module visibility controls;
- capability removal at deployment/runtime level;
- type-system restrictions;
- dependency-injection interfaces;
- code ownership/review rules;
- runtime authorization checks;
- architecture decision record only, when mechanical enforcement is not justified.

## Failure modes

- guard checks a string but not the real dependency path;
- scan excludes generated, test, alternate, or dynamically loaded paths that matter;
- developers disable the check rather than change the architecture;
- an allowlist grows until the prohibition becomes meaningless;
- the fence is treated as proof that ownership is correct everywhere;
- file rename/layout refactor breaks the guard although semantics are unchanged;
- architecture legitimately changes but the guard remains frozen accidentally.

## Verification

- a representative forbidden dependency makes the guard fail;
- representative allowed dependencies pass;
- the declared observation universe covers the paths relevant to the architectural claim;
- the guard survives non-semantic refactors where promised;
- exceptions are explicit and narrow;
- the positive owner/interface still exists and is verified separately;
- CI or local verification runs the fence at the point where it can prevent regression.

## Related Core Principles

- `authority-mapping` — defines the owner/non-owner relationship the fence protects;
- `dependency-ownership` — defines allowed provider/consumer dependency edges;
- `evidence-and-authority` — prevents a negative guard from being overclaimed beyond its observation universe;
- `proof-loop-verification` — incorporates the fence into acceptance evidence for work that changes the boundary.
