# Assignment Compilation Contract

Assignment compilation is the deterministic Control-layer boundary between a
Director decision and destination executability. It consumes structured control
intent; it does not infer policy from natural-language prompt text.

```text
DIRECTOR DECISION
→ classify target authority and movability
→ classify execution-context fact authority
→ validate identity gates and responsibility ownership
→ check the supported execution envelope
→ COMPILED_ASSIGNMENT
→ derive authorized mandatory actions and capabilities
→ route and exact-destination admissibility
→ executable ASSIGNMENT
```

## Authority and context classes

Every compiled assignment has exactly one `ASSIGNMENT_AUTHORITY_CLASS`:
`FROZEN_CANDIDATE`, `MOVING_PR`, `MOVING_BRANCH`, `POST_MERGE_STATE`, or
`LIVE_REMOTE_STATE`. Every context fact used for admission or stopping is
classified as `PLATFORM_PROVIDED`, `RESOLVER_BOUND`, `EXECUTOR_RESOLVED`, or
`REMOTE_LIVE`.

Freeze only what must remain immutable. Resolve legitimately moving state at
execution time. In particular, an observed HEAD is not an implicit immutable
gate for a moving PR or branch. Platform-provided context is not assigned to an
Executor for remote reauthentication unless the actual claim independently
requires remote provenance.

## Responsibility and envelope boundaries

Compiled obligations are partitioned among `EXECUTOR`, `CONTROL`, and
`PLATFORM`. Only Executor obligations contribute assignment-semantic required
capabilities. Every obligation cites an authorized structured claim; a supported
operation class or requested capability is never authority by itself. A
platform-provided fact authorizes reliance, not Executor reauthentication,
unless a distinct Resolver-bound independent-verification claim requires it.
An `IMMUTABLE_INVARIANT` claim resolves by `target_ref` to exactly one compiled
invariant, and its classification and responsibility must match that invariant;
a typed but unbacked claim grants no authority.
Before exact-destination admission, each realization/evidence
obligation must belong to the bounded supported Surface Portfolio. Portfolio
`UNSUPPORTED` is a compilation rejection; it is not destination
`ASSIGNMENT_NOT_ADMISSIBLE`.

`COMPILED` authorizes normalized mandatory actions and their exact capability
union. `REJECTED` authorizes no capabilities and cannot proceed to route,
profile selection, admissibility, or assignment. The reference compiler and
validator are `tools/assignment_compiler.py`.

Moving-target exact-identity exceptions require a resolved `FREEZE_AUTHORITY`
record whose authority role, target, movability class, explicit freeze grant,
and exact candidate identity all match. A non-empty reference alone grants no
authority. Execution-envelope support likewise resolves through an exact local
`EXECUTION_ENVELOPE` artifact. The compiled artifact retains that envelope ref;
a caller-supplied capability or obligation set cannot broaden it.

## Semantic contract and execution hints

The frozen semantic contract and environment-local execution mechanics are
separate surfaces. `COMPILED_ASSIGNMENT.execution_hints` may carry bounded,
structured executor-local guidance such as a known command, path, wrapper,
discovery suggestion, or implementation note. Hints are structurally validated
and preserved, but their contents are not interpreted as authority or semantic
obligations.

Execution hints contribute zero authority, mandatory actions, evidence
requirements, required capabilities, acceptance requirements, invariants, or
semantic stop conditions. In particular, a hint that names a capability or says
"stop" does not enter capability closure or STOP ownership. Failure or absence
of a hinted mechanism is therefore not itself compilation failure when the
semantic contract remains satisfiable by another supported mechanism.

This distinction does not weaken exact mechanics that are already represented
as real mandatory actions, evidence requirements, invariants, authority gates,
or acceptance requirements. Those remain inside the existing compilation and
admissibility closure.

The current resolver spawn result exposes the exact `compiled_assignment`
alongside the executable `assignment`, so #55-A does not duplicate hints into
the final `ASSIGNMENT` artifact. The Executor can receive the preserved hints
from the compiled artifact without expanding the final assignment schema or
creating a second obligation system.

## Binding chain

`ASSIGNMENT_ADMISSIBILITY` and executable `ASSIGNMENT` both cite the exact
`COMPILED_ASSIGNMENT`. Changed compiled semantics require a new compiled
artifact and a new admissibility decision. The downstream executability layer
continues to validate capability evidence, freshness, destination/runtime,
subset, route, and proof-chain parity; it does not parse assignment prose.
Final admissibility requirements must contain every compiled authorized
capability. They may additionally contain selected mandatory workflow/skill
realization prerequisites only when those additions remain fully accounted for
by the admissibility record's mandatory-action union.
