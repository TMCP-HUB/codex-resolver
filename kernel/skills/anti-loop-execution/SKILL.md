# Anti-Loop Execution

## Purpose

Use this skill to keep agent-driven implementation from turning into repeated patching, scope drift, branch proliferation, or tool retries without new evidence.

## Goal

Make execution finite and auditable by freezing the workstream before implementation and allowing exactly one active mode at a time:

- **EXECUTION MODE** — implement the frozen scope;
- **CAUSAL AUDIT MODE** — stop feature work and establish why execution is failing or why the current model is wrong.

This skill governs **workstream execution**, not technical diagnosis. Pair it with `systematic-debugging` when the stop condition is a software defect.

## When to use

Use for:

- non-trivial features or refactors;
- delegated or multi-session work;
- work with CI, deployment, migration, integration, or release gates;
- tasks where multiple agents or branches can diverge;
- any task with repeated failures or failed correction generations.

For a trivial single-edit task, the full artifact may be unnecessary, but the no-loop rules still apply.

## Do not use when

Do not use this skill to:

- decide product architecture;
- diagnose a bug in place of `systematic-debugging`;
- justify refusing a small obvious correction;
- create process ceremony with no meaningful stop condition.

## Inputs

- objective;
- scope;
- non-goals;
- acceptance criteria;
- owner;
- dependencies;
- gates;
- current authoritative working state;
- known risks and stop conditions.

## Required output

A frozen workstream record containing:

```text
objective
owner
scope
non-goals
dependencies
acceptance criteria
gates
initial authoritative state
mode
stop conditions
deferred findings
```

## Procedure

### 1. Freeze before substantial implementation

Before meaningful code changes, make the workstream explicit enough that another agent can tell what belongs and what does not.

A frozen scope is not immutable forever. It means changes to scope must be deliberate and visible rather than smuggled in through implementation.

### 2. Enter exactly one mode

#### EXECUTION MODE

Allowed:

- implement frozen scope;
- run verification;
- make corrections that directly belong to frozen correctness;
- record out-of-scope discoveries.

Not allowed:

- silently add another feature;
- redesign adjacent architecture because it looks cleaner;
- treat a new unrelated finding as permission to expand the PR;
- investigate root cause and keep speculative feature patching at the same time.

#### CAUSAL AUDIT MODE

Enter for the implicated workstream when a genuine blocking stop condition fires. Exhausting a separate optional diagnostic is not a global stop for otherwise admissible implementation.

Allowed:

- inspect evidence;
- reproduce and isolate failure;
- compare assumptions with actual state;
- inspect branch/tool/environment divergence;
- form and test causal hypotheses;
- decide whether the frozen plan itself is invalid.

Not allowed:

- continue feature development;
- stack another point-fix without an established cause;
- start a new workaround branch to avoid understanding the current state.

### 3. Use finite stop conditions

Recommended defaults unless the project explicitly defines stricter rules before execution:

- two sequential failed mutating correction generations on the same candidate/repair boundary, even when their failure classes differ;
- two identical failures of the same tool/process operation without new evidence;
- authoritative working state diverges from intended/reviewed/tested state;
- acceptance requires changing a declared non-goal;
- a dependency contract is missing or contradictory;
- the proposed fix requires guessing which source of truth is authoritative;
- correctness or security cannot be established inside frozen scope.

A correction generation counts when a mutating repair is followed by an actually executed required check or observation that returns red on that same boundary. A check that was not executed, is unavailable, or has an unknown result is not a red result or a failed correction by itself; classify the affected operation separately. Even an executed red check does not by itself prove a product-code defect. The initial red observation and read-only probes are not correction generations. After two such failures, do not issue or make a third mutating correction automatically on that boundary; use the existing causal diagnosis and Director disposition. Changing the error class does not reset this budget. Carry the actual candidate, failed generations and next action in the existing Issue/PR or HANDOFF: a new HEAD, branch, session or Assignment for the same unresolved candidate/repair boundary does not reset it. A different error may still belong to a different failure class and must be classified accurately.

The tool/process retry budget is separate: two identical failures of one operation without new evidence stop that operation, not unrelated authorized work. Two failures of an optional provider/API observation (for example, HTTP 401 twice) stop **that diagnostic** without a third blind retry; they do not require stopping independent code or its GitHub publication. Provider visibility failure alone is not evidence of a code defect. Failed genuinely mandatory validation, publication, authority or safety operations still block the affected required result and must be reported honestly; do not bypass their gates.

Repeated individually green repairs with a proven common causal boundary are a separate defect-cluster signal, not two red correction generations. Consider the shared cause and a scoped architecture review when the evidence warrants it; if the relevant cause and sufficient basis are already clear, continue accordingly. This is not a general audit or automatic gate, and unrelated work may continue.

### 4. Handle new findings without scope leakage

Classify every discovery:

```text
belongs to frozen correctness
→ fix here

directly blocks frozen correctness/security
→ record as blocker and resolve here

adjacent but non-blocking
→ record separately; do not fix here
```

Do not reward discovery with automatic scope expansion.

### An unavailable old worker is not a stop condition

An initial Assignment has **no previous Executor by definition**: the normal action is to create a newly admitted worker using the configured native launch route, not search for or "resume" an unknown historical agent. Reuse is appropriate only for a known live session of this workstream. After a proven terminal/lost attempt, a new admitted worker is legitimate recovery; the "no second Executor" anti-duplicate rule applies while an earlier attempt is still active or its acknowledgement is genuinely uncertain.

The correction and tool-operation limits above stop only the implicated repair or diagnostic, with work preserved. They do not prohibit first-time dispatch, continuation on another independent already-approved stage, or later recovery on genuinely new evidence. Do not turn a missing historical worker or one optional unavailable subagent into a failure of an approved native launch route. Do not retry a known-dead transport or simulate unlimited autonomous scheduling. `WAIT/ESCALATE` retains the workstream cursor; it is not `COMPLETE` and not permission to send the same unresolved Owner choice around indefinitely.

### Preserve already-written source when execution must STOP

A red-run or correction-loop STOP prohibits further speculative implementation **but does not erase the original GitHub publication obligation**. For authorized GitHub-backed code work, publish the existing bounded changes to the **same** approved branch/Draft PR as an explicitly unfinished WIP checkpoint if the current publisher can safely do so, even when mandatory CI or implementation acceptance is still red. No test rewrite, CI bypass, merge or deployment is implied. Independently read back the remote HEAD before claiming the WIP survives session deletion.

When the current publishing route is truly broken, do not start another Executor, recreate the source via chat patches or silently delete the only local copy. Preserve the original workspace/attempt, report the exact `PARTIAL/BLOCKED` publication limitation and current remote HEAD, and stop the affected operation. A local patch, unpushed commit or agent narrative is **not** a durable checkpoint. A stopped correction stream does not automatically stop unrelated authorized work.

### 5. Resume only after the stop condition is resolved

A Causal Audit ends with one of:

- root cause established; return to Execution with a bounded correction;
- scope assumption disproved; explicitly replan/refreeze;
- dependency or upstream defect identified; stop current implementation and hand off;
- environmental/tool failure established; use a different verified execution path;
- task is blocked or invalid; record that instead of manufacturing progress.

## Decision rules

- **New evidence before new code.** Repeated code changes without changed evidence are a loop.
- **One workstream, one authoritative state.** Do not escape a confusing branch by spawning another untracked branch.
- **Scope changes are governance events.** They are not implementation details.
- **Partial completion is a valid result.** Hiding a blocker is not.
- **A stop condition is not failure.** Ignoring one is.

## Anti-patterns

Avoid:

- third/fourth/fifth point-fix because the previous fix was "close";
- rewriting tests to match accidental behavior;
- deleting checks to obtain green CI;
- creating multiple PRs for the same unresolved branch state;
- mixing root-cause investigation with speculative implementation;
- fixing every issue noticed while reading nearby code;
- declaring a tool flaky without bounding the repeated failure;
- treating a new chat/session as a reset of technical state.

## Verification checklist

- [ ] Objective and scope are explicit.
- [ ] Non-goals exist for meaningful adjacent work.
- [ ] Current mode is unambiguous.
- [ ] Stop conditions are finite.
- [ ] Repeated failures have not been converted into repeated guesses.
- [ ] Out-of-scope findings are recorded, not silently implemented.
- [ ] If Causal Audit occurred, the cause or replan decision is recorded before execution resumed.

## Pair with

- `implementation-planning` to create the frozen workstream;
- `systematic-debugging` to perform technical causal diagnosis;
- `authority-mapping` when the cause involves competing sources of truth;
- `exact-state-verification` when state/provenance divergence is suspected;
- `proof-loop-verification` before declaring the workstream complete.
