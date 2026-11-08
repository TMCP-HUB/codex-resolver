"""Read one Codex Cloud task page without assigning project meaning to status."""

import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


MESSAGES = {
    "invalid_arguments": "Invalid arguments; see --help. No provider request made.",
    "missing_cli": "Codex executable not found. Select an existing installation.",
    "unsupported_executable": "Select a native executable, not a .cmd or .bat wrapper.",
    "unsupported_command": "Installed CLI does not support the requested command or options.",
    "authentication_failed": "CLI reported an authentication failure. Check the existing login.",
    "permission_denied": "Access was denied. Check executable and Cloud account permissions.",
    "timeout": "CLI exceeded the configured timeout; no page is returned.",
    "nonzero_exit": "CLI exited unsuccessfully; no page is returned.",
    "invocation_failed": "CLI could not be started; no page is returned.",
    "malformed_output": "CLI did not return a valid UTF-8 task-page JSON object.",
}


def failure(code, provider_exit_code=None, exit_code=1):
    payload = {
        "ok": False,
        "error": {"code": code, "message": MESSAGES[code]},
        "provider_exit_code": provider_exit_code,
    }
    sys.stdout.buffer.write((json.dumps(payload) + "\n").encode("utf-8"))
    return exit_code


class Parser(argparse.ArgumentParser):
    def error(self, message):
        # argparse diagnostics can echo supplied values. Never publish them.
        raise SystemExit(failure("invalid_arguments", exit_code=2))


def options(argv):
    parser = Parser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--codex-bin", default=None,
                        help="Installed executable name or path; Windows: native codex.exe")
    parser.add_argument("--env", help="Provider environment identifier (optional filter)")
    parser.add_argument("--limit", type=int, choices=range(1, 21), default=20,
                        metavar="1-20", help="Tasks per page (default: 20)")
    parser.add_argument("--cursor", help="Opaque cursor from a previous page")
    parser.add_argument("--timeout", type=float, default=30, metavar="SECONDS",
                        help="Process timeout, greater than 0 and at most 120 (default: 30)")
    args = parser.parse_args(argv)
    if not math.isfinite(args.timeout) or not 0 < args.timeout <= 120:
        parser.error("timeout out of range")
    for value in (args.codex_bin, args.env, args.cursor):
        if value is not None and (not value or "\x00" in value):
            parser.error("empty or NUL-containing argument")
    return args


def classify_failure(diagnostics):
    # Classification is best effort; diagnostics themselves never leave this process.
    text = diagnostics.decode("utf-8", errors="replace").lower()
    if any(marker in text for marker in (
        "unrecognized subcommand", "unknown subcommand", "unknown command",
        "unexpected argument", "unknown option", "unrecognized option",
        "not a valid subcommand",
    )):
        return "unsupported_command"
    if re.search(r"\b403\b", text) or any(marker in text for marker in (
        "forbidden", "permission denied", "access denied", "insufficient scope",
    )):
        return "permission_denied"
    if re.search(r"\b401\b", text) or any(marker in text for marker in (
        "not signed in", "not logged in", "unauthorized", "authentication",
        "login required", "log in", "sign in", "token expired", "invalid token",
    )):
        return "authentication_failed"
    return "nonzero_exit"


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON member")
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError("non-JSON constant")


def validate_page(raw):
    text = raw.decode("utf-8")
    page = json.loads(text, object_pairs_hook=unique_object,
                      parse_constant=reject_constant)
    if not isinstance(page, dict) or not isinstance(page.get("tasks"), list):
        raise ValueError("missing task array")
    if "cursor" not in page or not (page["cursor"] is None or isinstance(page["cursor"], str)):
        raise ValueError("missing or invalid cursor")
    for task in page["tasks"]:
        if not isinstance(task, dict):
            raise ValueError("invalid task")
        for key in ("id", "url", "status"):
            if not isinstance(task.get(key), str) or not task[key]:
                raise ValueError("missing task identity or status")
        if "environment_id" not in task or not (
            task["environment_id"] is None or isinstance(task["environment_id"], str)
        ):
            raise ValueError("missing or invalid environment identity")
    # Emit the validated original JSON, retaining unknown fields and numeric spelling.
    return text.strip()


def main(argv=None):
    args = options(argv)
    requested = args.codex_bin or ("codex.exe" if os.name == "nt" else "codex")
    if Path(requested).suffix.lower() in (".cmd", ".bat"):
        return failure("unsupported_executable")
    try:
        executable = shutil.which(requested)
        if executable is None:
            return failure("missing_cli")
        if Path(executable).suffix.lower() in (".cmd", ".bat"):
            return failure("unsupported_executable")
        command = [executable, "cloud", "list", "--json", "--limit=" + str(args.limit)]
        if args.env is not None:
            command.append("--env=" + args.env)
        if args.cursor is not None:
            command.append("--cursor=" + args.cursor)
        result = subprocess.run(command, shell=False, stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                timeout=args.timeout, check=False)
    except FileNotFoundError:
        return failure("missing_cli")
    except PermissionError:
        return failure("permission_denied")
    except subprocess.TimeoutExpired:
        return failure("timeout")
    except OSError:
        return failure("invocation_failed")
    if result.returncode != 0:
        code = classify_failure(result.stderr + b"\n" + result.stdout)
        return failure(code, provider_exit_code=result.returncode)
    try:
        page = validate_page(result.stdout)
    except (ValueError, UnicodeError, RecursionError):
        return failure("malformed_output", provider_exit_code=0)
    sys.stdout.buffer.write(
        ('{"ok":true,"scope":"single_page","page":' + page + '}\n').encode("utf-8")
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
