# SBC Runtime Context Contract

`SBC_RUNTIME_CONTEXT` is an explicit runtime observation supplied to a fresh Liaison by the future SBC Browser. It is not semantic authority, an execution ticket, a capability profile, or proof that any external action is authorized.

## V0 fields

- `artifact_type: SBC_RUNTIME_CONTEXT`
- `present: true`
- `runtime_version`: non-empty runtime version string
- `pak_state`: `OFF`, `MANUAL`, or `AUTO`
- `available_browser_operations`: unique opaque operation identifiers

Absence of this object means `ORDINARY_CHAT`. A supplied malformed object is `INVALID_CONTEXT`; it must not silently degrade to ordinary absence and must never be upgraded to SBC mode by guesswork.

Operation identifiers are observations only. Their names do not create semantic, Owner, routing, mutation, or dispatch authority.

Provider IDs, tab IDs, conversation IDs, DOM/CDP state, provider authentication state, capability-profile fields, and authority claims are outside this V0 context.
