# Codex Cloud observation

`observe.py` uses Python 3.9+ and the standard library to read one task page
through an existing Codex CLI installation. Each invocation starts at most one
`codex cloud list --json` process. There are no retries or automatic page reads.

## Prerequisites and usage

Use a CLI version supporting `cloud list --json`, `--env`, `--limit` and
`--cursor`. Flags were checked with installed `codex-cli 0.163.0` help; the
`tasks`/`cursor` JSON shape was checked against the official
[list implementation](https://github.com/openai/codex/blob/main/codex-rs/cloud-tasks/src/lib.rs).
An unsupported CLI fails explicitly; this adapter does not install or update it.

The chosen CLI must already have a ChatGPT login with access to Codex Cloud and
the requested environment. Arrange authentication separately using the CLI's
supported login procedure. The adapter inherits the existing CLI configuration
and process environment; it does not log in, read authentication files, copy
credentials or accept token arguments.

From the repository root:

```sh
python3 adapters/codex-cloud/observe.py --limit 5
python3 adapters/codex-cloud/observe.py --env YOUR_ENVIRONMENT_ID --limit 5 --timeout 30
python3 adapters/codex-cloud/observe.py --codex-bin /path/to/codex --limit 5
```

Windows PowerShell, using an installed native executable:

```powershell
python adapters/codex-cloud/observe.py --codex-bin 'C:\Program Files\Codex\codex.exe' --limit 5
```

Executable paths containing spaces work as one argument. Windows defaults to
`codex.exe`; other platforms default to `codex`. Shell wrappers ending in `.cmd`
or `.bat` are rejected: choose the installed native executable instead.
Arguments are passed without a shell. The page limit is 1–20 (default 20), and
the process timeout is greater than 0 and at most 120 seconds (default 30).
Use `--help` for options. Invalid arguments produce JSON and exit 2.

## Output and pagination

Success exits 0 and returns `{"ok":true,"scope":"single_page","page":...}`.
`page` contains the original validated provider JSON, including all task fields
and unknown fields. IDs, URLs, provider statuses, environment IDs and labels,
summaries and the provider's `cursor` are retained without status translation.
Provider status does not establish project acceptance, verification or merge
authority. Treat task data as private account data when sharing output.

A valid `{"tasks":[],"cursor":null}` page succeeds. Every response describes
one page, never a complete inventory. If `page.cursor` is non-null, pass it
unchanged to a separate invocation with the same environment filter and limit:

```sh
python3 adapters/codex-cloud/observe.py --env YOUR_ENVIRONMENT_ID --limit 5 --cursor='OPAQUE_CURSOR'
```

Quote cursor values for your shell; `--cursor=VALUE` also accommodates a value
beginning with `-`. The adapter does not fetch the next page, infer a total,
or promise a stable snapshot across calls.

Failures exit nonzero with `ok:false`, `error.code`, a fixed safe message and
`provider_exit_code` (null when no exit was obtained). Codes distinguish
`missing_cli`, `unsupported_executable`, `unsupported_command`,
`authentication_failed`, `permission_denied`, `timeout`, `nonzero_exit`,
`invocation_failed`, `malformed_output` and `invalid_arguments`. Unsupported,
authentication and permission classifications use recognized diagnostic markers;
unrecognized failures remain `nonzero_exit`. Raw stdout/stderr diagnostics,
argument values and authentication material are never included in failure output.
Malformed successful CLI output records provider exit 0 but adapter exit 1.

## Local checks and live proof

Syntax, argument parsing and fake-executable checks can exercise forwarding,
pagination preservation, empty pages, timeouts and safe error handling without
Cloud credentials. They do not establish live provider access, account
permissions, Windows execution or current task inventory. Installed CLI help
and official source inspection establish the expected interface, not a live
listing. Live proof requires a separately authorized bounded invocation on an
already authenticated machine; this implementation assignment leaves that read
to Work Control after publication.
