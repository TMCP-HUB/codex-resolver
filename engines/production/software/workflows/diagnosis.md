# Software Workflow — Diagnosis

**Entry:** a software failure or unexplained red signal with bounded target state and destination executability proof for the observations/actions that are mandatory to the diagnostic assignment.

**Primary role:** Executor.

Load `skills/systematic-debugging` and shared `kernel/skills/anti-loop-execution`. Add `exact-state-verification`, authority/dependency skills, or technical QA skills only when their owned question is present and their mandatory execution prerequisites are satisfied.

Before assignment, distinguish what diagnosis actually requires. Static repository inspection, local reproduction, deployed observation, browser/network-console inspection, database inspection, CI observation, and API interaction are different execution modes with different capability requirements. A diagnosis that requires local reproduction is not admissible on a repository-connector-only destination merely because the same agent can read the code.

Preserve failure taxonomy. Provider/environment/not-executed evidence is not automatically a red result or a code defect. Known missing mandatory observation capability before dispatch is `ASSIGNMENT_NOT_ADMISSIBLE`; disappearance of a previously proven capability during investigation is `BLOCKED_RUNTIME_DRIFT`. After two mutating correction generations each followed by an actually executed red required check on the same candidate/repair boundary, do not automatically make a third mutating correction; use bounded causal diagnosis even if the failure classes differ. Two identical failures of one tool/process operation separately stop that operation; unrelated work can continue.

**Audit -> implementation continuation:** A scoped audit/diagnosis may run in the same admitted Codex or Chat Executor instance that later implements its findings, but these are **different Assignments**. First publish the bounded audit findings and evidence to the governed durable record. Director/Owner reconcile the approved corrections and exact current GitHub state, then compile/admit and dispatch a fresh implementation Assignment. The retained audit context cannot grant write rights or turn the Executor into an independent Verifier or merger. A fresh Executor instance is equally valid.

**Exit:** demonstrated root cause and bounded correction path, or explicit PARTIAL / runtime-drift blockage with unresolved causal evidence where the assignment was valid when issued. Emit Executor Result; independent verifier checks completion claims separately and must receive its own destination executability preflight.
