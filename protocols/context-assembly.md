# Context Assembly Protocol

**CONTEXT IS ASSEMBLED, NOT INHERITED.** A fresh role instance receives an explicit bounded packet; prior chat history is never canonical state by itself.

## Assembly order

1. minimal system/root instructions;
2. current relevant state slice;
3. selected engine manifest;
4. selected workflow;
5. role contract;
6. exact assignment;
7. required skills only;
8. referenced artifacts/evidence needed by the role.

Do not add the global repository or entire skill library "just in case".

## Role context contract fields

Every durable role defines:

- **READ** — state/artifacts it may read by default;
- **REQUEST** — additional bounded information it may request;
- **EMIT** — artifacts it may produce;
- **HANDOFF** — permitted recipients and required transfer fields;
- **PRESERVE** — information that must survive compression/turn boundaries;
- **SUMMARIZE** — information that may be reduced and at what fidelity;
- **DO_NOT_PROPAGATE** — irrelevant/sensitive/noisy context that must not spread automatically;
- **OWNER_SURFACE** — what is transformed into human-readable Owner communication.

## Loss-aware compression

Compression may remove narrative redundancy, but it must never silently lose material control state. Preserve at minimum:

- authority and authority limits;
- accepted decisions and exact decision identity;
- Owner constraints/protected values/non-goals relevant to the work;
- blockers and unresolved contradictions;
- exact candidate/base/environment identity when claims depend on them;
- failed acceptance criteria;
- stale or invalidated evidence status;
- material deferred findings;
- active assignment/result recipients and baton owner.

If fidelity cannot be preserved, emit a HANDOFF/CONTEXT_GAP and request the missing source rather than reconstructing it from memory.

## Cross-Assignment Director continuity

For a current Owner-approved multi-step workstream, assemble the existing Issue/plan ref, final outcome boundary, current-stage cursor, accepted PR/merge HEADs, remaining dependencies, exact current remote main, blockers and Control baton owner. Do not carry unrelated transcripts or full source payloads. Child Assignment completion never erases still-authorized workstream stages.

## Reuse and re-verification

Previously assembled evidence/context may be reused when exact source state, trust boundary, and relevant authority are unchanged. Re-read/reverify only when actual drift or risk affects the claim; do not perform redundant repository-wide forensic rereads by habit.
