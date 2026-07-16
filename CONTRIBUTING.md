# Contributing

Thanks for your interest. This is a small, dependency-free project — contributions that keep it
that way are the most welcome.

## Principles

- **No runtime dependencies.** Scripts use the Python 3 standard library only. Don't add packages.
- **Local & private.** Never add network calls, telemetry, or anything that sends user data off the
  machine. Personal data belongs under `~/.work-like-me/`, never in the repo.
- **Minimal, safe changes.** Prefer the smallest change that works over broad refactors.

## Project layout

```
plugins/work-like-me/
  .claude-plugin/plugin.json     # Claude manifest
  .codex-plugin/plugin.json      # Codex manifest
  scripts/                       # shared Python (extract, analyze, sample, compile, install, capture, dashboard)
  skills/{create,dashboard,update,auto}/SKILL.md
tests/                           # dependency-free tests
.github/workflows/ci.yml         # py_compile + tests on 3.9 / 3.12
```

## Running tests

```bash
for t in tests/test_*.py; do python3 "$t"; done   # or: python3 -m pytest tests/
python3 -m py_compile plugins/work-like-me/scripts/*.py
```

CI runs the same on Python 3.9 and 3.12. Keep code compatible with 3.9 (no `match`, no `X | Y`
type unions).

## If you touch redaction

Privacy is the core promise. When you add or change a pattern in `extract.py`:

1. Add a positive test (the secret is masked) **and** a negative test (plain text isn't over-redacted)
   to `tests/test_redact.py`.
2. Update the redaction table in `SECURITY.md`.
3. Be conservative — a false positive that mangles normal prose is a real regression.

## Commits & PRs

- Commit messages: `<type>: <설명>` (feat/fix/docs/refactor/test/chore). Korean or English is fine;
  match the existing history style.
- Describe the change, its scope, and how you verified it. Note anything you *couldn't* verify
  (e.g. Windows behavior) honestly.
- Bump the version in **both** `plugin.json` files and add a `CHANGELOG.md` entry for user-facing changes.
