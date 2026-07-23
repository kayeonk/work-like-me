# Security & Privacy

`work-like-me` reads your local AI coding-session logs to model your working style. Because that
input is sensitive, privacy is a first-class design goal — but it is **best-effort, not a guarantee**.
Read this before using the tool on logs that may contain secrets.

## Privacy model

- **100% local.** The scripts make **no network calls**. Your logs, samples, and generated rules
  never leave your machine. There is no telemetry.
- **Personal data stays outside the repo.** Your induced rules, sampled messages, and pending
  signals live under `~/.work-like-me/` (override with `WORK_LIKE_ME_DATA`) — never inside the plugin,
  so they are never committed or shipped. Only generic tooling + `rules.example.json` are in the repo.
- **Redaction before sampling.** User messages are redacted *before* anything is written to disk
  for review or shown to the induction step.

## What gets redacted

`extract.redact()` masks these patterns (see `plugins/work-like-me/scripts/extract.py`):

| Category | Examples |
|----------|----------|
| Emails | `foo@bar.com` → `<email>` |
| API keys | OpenAI `sk-…`, Google `AIza…`, AWS `AKIA…`, Slack `xox…` → `<key>` / `<aws-key>` / `<token>` |
| Tokens | GitHub `ghp_…` / `github_pat_…`, JWTs, `Bearer …` headers → `<token>` / `<jwt>` |
| `.env` secrets | `API_KEY=…`, `*SECRET*=…`, `*PASSWORD*=…` (value masked, key kept) → `NAME=<secret>` |
| Hashes | 32+ hex chars → `<hash>` |
| Home paths | macOS `/Users/<name>`, Linux `/home/<name>`, Windows `C:\Users\<name>` → `<home>` (hides OS username) |
| IPs | IPv4 → `<ip>` |

Redaction rules are covered by `tests/test_redact.py`.

## What can still leak (honest limitations)

Redaction is **regex pattern matching**, not a semantic secret scanner. It cannot catch everything:

- **Unusual/custom secret formats** (non-standard key prefixes, base64 blobs, DB connection strings
  without a recognized key name).
- **Secrets embedded in prose** ("the password is hunter2") without an `=`/`:` assignment.
- **Injected-context lines** from other tools/plugins that occasionally appear in session logs.
- **Phone numbers** are intentionally *not* redacted (high false-positive rate against IDs/versions).

**Mitigation:** the flow always shows you the compiled prompt (`compile.py`) before install, and
install runs a `--dry-run` preview first. **Review the output before applying**, especially if your
logs touch credentials. If you find a secret in a generated file, delete it and open an issue about
the missing pattern.

## What the tool writes to

- Global config (only inside a marked block, with a one-time `.bak` backup):
  `~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`.
- A `SessionEnd` hook (declared in the plugin's own `hooks/hooks.json`, Claude-only) runs on by
  default. It only accumulates redacted signals **locally** under `~/.work-like-me/`; it makes no
  network calls and applies nothing without your review. It does **not** modify your
  `~/.claude/settings.json`. Turn it off with the `auto` skill (writes a `~/.work-like-me/.auto-off` flag).

## Reporting a vulnerability

Found a redaction gap or other privacy issue? Please open a GitHub issue (omit the actual secret —
describe the *format*), or contact the maintainer listed in `README.md`. There is no bounty program;
this is a personal open-source project.
