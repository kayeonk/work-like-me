# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/); this project uses semantic-ish versioning.

## [0.7.0]

### Changed
- **Auto-suggestion is now on by default.** The SessionEnd hook is declared in the plugin's own
  `hooks/hooks.json` (native), so it's active on install without touching your `~/.claude/settings.json`.
  It only accumulates redacted signals locally; nothing is applied without review. Turn it off with
  the `auto` skill, which writes a `~/.work-like-me/.auto-off` opt-out flag (the hook no-ops when set).
- Removed the old settings.json-mutating hook install/uninstall in favor of the opt-out flag.

### Added
- `dashboard` skill documents how to stop a running dashboard server.
- README install block includes `/reload-plugins`.

## [0.6.4]

### Fixed
- Confidence badge now localizes too. Values are normalized to canonical `high/med/low` (accepting
  Korean `상/중/하` or English inputs) so the dashboard shows the label in the persona's language
  with the correct color, regardless of how the value was stored.

## [0.6.3]

### Added
- **UI/prompt localization via `meta.lang`** (`ko`/`en`, default `en`). The dashboard chrome and the
  compiled prompt's fixed labels now follow the persona's language; rule content and category names
  stay in whatever language the induction produced. `create` sets `meta.lang`; `compile.py` and
  `dashboard.py` read it. Covered by tests.

## [0.6.2]

### Added
- Hardened redaction: GitHub fine-grained PATs, Slack/Google API keys, `Bearer` headers,
  `.env`-style secret assignments, IPv4, and **cross-OS home-path masking** (macOS/Linux/Windows),
  so the OS username no longer leaks.
- Test suite (`tests/`, no external deps): redaction, install idempotency, compile output.
- GitHub Actions CI running `py_compile` + tests on Python 3.9 and 3.12.
- `SECURITY.md` documenting the privacy model and honest limits.
- README dashboard screenshot, install troubleshooting, and a "not a guaranteed scrubber" note.

## [0.6.1]

### Fixed
- Evolution now works on Codex, not just Claude. Signal collection is decoupled from the
  Claude-only `SessionEnd` hook: the `update` skill runs `capture.py --scan` to ingest recent
  **Claude + Codex** sessions on demand. The auto-badge hook remains Claude-only (documented).
- `create` stamps a review baseline after install so the first `update` doesn't re-ingest history.

### Changed
- `extract.py` parsing extracted into a shared `iter_user_utterances()` generator (reused by `--scan`).

## [0.6.0]

### Changed
- Genericized: removed developer/Korean hardcoding. `compile.py` emits **all** categories the
  induction produces (category names become section titles); the prompt header is domain-neutral.
- `analyze.py` demoted to an optional, clearly-labeled Korean/dev heuristic; the primary induction
  is the LLM reading a redacted sample (language- and domain-agnostic).
- Different work *modes* (e.g. a full-stack dev's FE vs BE checkpoints) are modeled as situational
  rules within one persona rather than separate personas.

## [0.5.0]

### Changed
- Split the single skill into four (`create`, `dashboard`, `update`, `auto`); shared scripts moved
  under `scripts/`.

## [0.4.0]

### Added
- Codex support — restructured into a monorepo (`plugins/work-like-me`) with `.codex-plugin` and
  `.agents` manifests alongside the Claude `.claude-plugin` manifest.
