# Kernel

The kernel owns cross-engine control decisions: what transition is admissible next, which engine owns the work class, whether authority/evidence is sufficient, and when execution must stop or escalate.

It does not contain permanent agent personalities and does not execute domain work merely because no other engine is available. Shared reasoning skills under `kernel/skills/` are loaded only when a workflow requires their owned decision process.

The kernel preserves the diagnostic ladder:

1. RUNTIME / MODEL FAILURE
2. BAD CONTEXT SLICE
3. BAD ASSIGNMENT
4. ROLE CONTRACT DEFECT
5. ATOMIC SKILL DEFECT
6. WORKFLOW DEFECT
7. LOCAL ARCHITECTURE DEFECT
8. INVALIDATED ARCHITECTURE ASSUMPTION

One malfunctioning agent is not an Architecture Reconsideration Gate. Patch a durable role/skill when that is the defect, start a fresh role instance, and rerun the bounded case.