# Engine — Verification

The Verification Engine independently evaluates completion/evidence claims. It consumes exact assignments, primary Executor Results, and direct evidence/state where required.

It does not implement or repair the candidate, rewrite the Executor Result, choose Owner/Canon meaning, or acquire product mutation authority. Its output is a separate `VERIFICATION_RESULT` with claim-by-claim verdicts.
