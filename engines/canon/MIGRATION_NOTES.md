# Canon Engine current-main materialization notes

This materialization uses PR #28 (`2cc651826025116a76c962b4c725c4a718b28459`) only as a read-only donor of Canon semantics and historical migration evidence.

Current `main` contracts are authoritative. The donor branch is not rebased, merged, or treated as acceptance authority.

## Reconciled defects

1. **Common artifact protocol** — all active durable Canon artifact schemas/templates now carry the shared Project Resolver identity/provenance envelope. Canon does not define a competing identity system.
2. **Workflow roles** — every executable workflow has an explicit executing role, consuming role, required skill set, and upstream requirement set in `MANIFEST.yaml` and in the workflow document.
3. **Progressive disclosure** — the Router selects a Canon capability/workflow and loads all workflow-declared mandatory skills, not one guessed skill and not the global skill library.
4. **Current Resolver** — Canon uses the existing assignment compiler, capability profile, execution route, assignment admissibility, execution proof, and `resolve_spawn()` path. There is no Canon-specific resolver.
5. **Execution prerequisites** — active Canon skills declare a bounded execution contract. They do not imply network, shell, browser, repository, or Research acquisition capabilities.

## Historical inventory disposition

The historical 190/190 source inventory remains evidence. Its current disposition is summarized in root `CANON_ENGINE_MIGRATION_MAP.md`; future Writing, Translation, Interactive, generic Foundation, and other deferred surfaces remain inactive.
