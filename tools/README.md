# Validation Tools

Run `python tools/validate_structure.py` for the current deterministic Project Resolver structural gate. It checks root/engine references (including active Foundation), role shape, schema syntax, bounded skill namespaces, duplicate active skill IDs, optional-pattern classification, Research policy/regressions, and preservation/removal of key legacy runtime surfaces. A structural PASS does not establish live-provider behavior, architecture acceptance or business completion.

`python -m unittest tests.test_structure` wraps the same gate for standard-library test runners. No external orchestration framework is required.
