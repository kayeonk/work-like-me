# work-like-me

> Turn your real AI coding-session history into a personal, **directive system prompt** —
> generated and installed **locally**, privacy-first.

`work-like-me` reads your local Claude Code / Codex session logs, extracts *your* messages,
and induces your working style — values, judgment heuristics, communication style, and
do/don'ts — then writes a directive system prompt and installs it into your global AI
config so **every project inherits how you actually work**.

Unlike fictional "persona" skills or one-off "summarize my chat history" prompts, this is:

- **Data-driven** — built from your real sessions, with frequency evidence per rule.
- **Local & private** — no network calls; secrets are redacted before any analysis.
- **Directive** — produces an installable system prompt (`You must… / Do not…`), not a description.
- **Manageable** — rules live in a registry you can favorite / pause per-rule via a local dashboard.
- **Self-evolving (opt-in)** — a SessionEnd hook accumulates new signals and *proposes* updates.

![work-like-me dashboard — favorite / pause induced rules, then apply](docs/dashboard.gif)

> The local dashboard: each induced rule with its category, confidence, and evidence count.
> Favorite (★) or pause rules — the unsaved-changes badge appears — then **Apply** to recompile
> and reinstall. *(Sample developer persona; UI follows the persona's language. No real data.)*

## Privacy

- Runs **100% locally**. Your logs never leave your machine.
- Secrets/PII are **redacted before** anything is sampled: emails, API keys (OpenAI/Google/AWS/Slack),
  GitHub tokens, JWTs, `Bearer` headers, `.env`-style secret assignments, long hashes, IPs, and
  **home-directory paths on macOS/Linux/Windows** (so your OS username never leaks).
- Company/project names are anonymized in the output by default.
- **Not a guaranteed scrubber.** Redaction is best-effort pattern matching — review the compiled
  prompt before installing. Unusual secret formats or injected-context lines can still slip through.

## Requirements

- [Claude Code](https://claude.com/claude-code) (the skill host)
- Python 3
- Optional: Codex CLI session logs

## ⚡ Install

Works as a plugin in **both Claude Code and Codex** (one repo, one command set).

**Claude Code** (slash commands, or the `/plugin` UI → Marketplaces):
```text
/plugin marketplace add kayeonk/work-like-me
/plugin install wlm@kayeonk
```
Then **restart Claude Code** so the new skills load. (`/reload-plugins` exists in some builds but
isn't available everywhere — a fresh session always works. Type `/` and you should see
`/wlm:create` etc.)

**Codex** (terminal):
```bash
codex plugin marketplace add kayeonk/work-like-me
codex plugin add wlm@kayeonk
```
Codex has no in-session hot-reload — **start a new session** to pick up the plugin. Codex loads
skills only (no slash commands); invoke with `$create`, the `/skills` picker, `@wlm`, or
plain language.

Then just say: **"내 페르소나 만들어줘"** (or `make my persona`). The skill walks you through
source selection → a short interview → review → install. Nothing leaves your machine.

> **Local development:** `/plugin marketplace add ~/path/to/work-like-me`, then install as above.
> Your personal data lives in **`~/.work-like-me/`** — outside the plugin — so it survives
> updates and is never shipped.

### Troubleshooting

- **Skills don't appear after install** → restart the CLI (Claude and Codex load plugins at session
  start). Confirm the marketplace is registered: `/plugin marketplace list` (Claude) /
  `codex plugin marketplace list` (Codex).
- **`Not loaded — the name "wlm" is already taken`** → an older copy is still installed.
  Remove it first (`/plugin uninstall wlm@<old-marketplace>`), then reinstall.
- **Updating to a new version** → `/plugin marketplace update kayeonk` then reinstall, and
  start a fresh session. Codex: `codex plugin marketplace upgrade` + `codex plugin add …`.
- **`python3` not found** → the scripts need Python 3 on your `PATH`.

## Skills

The plugin provides four skills — they work in **both** Claude Code and Codex.

| Skill | What it does |
|-------|--------------|
| `create` | Generate your persona from session logs and install it |
| `dashboard` | Open the local dashboard to favorite / pause rules and apply |
| `update` | Review newly accumulated signals and propose rule updates |
| `auto` | Turn auto-suggested persona updates (over time) on/off |

The persona is **language- and domain-agnostic**: categories are whatever the induction produces
(the tool doesn't hardcode developer-specific sections), and different work *modes* — e.g. a
full-stack dev's front-end vs back-end checkpoints — are captured as **situational rules within one
persona**, not separate profiles.

How to invoke:
- **Claude Code** — type `/` and pick `/wlm:create` (skills show as `/name` shortcuts).
- **Codex** — type `$create`, use the `/skills` picker, or `@wlm`.
- **Either** — just say **"내 페르소나 만들어줘"** (or "make my persona"); the matching skill activates from its description.

## How it works

```
0 detect sources → 1 extract (+redact) → 2 stats + sample → 3 sample-size guard
→ 4 LLM induction → rules.json (registry)  → 5 situational drill-down interview
→ 6 compile & review → 7 install (preview → apply)
→ 8 manage (dashboard: favorite / pause)  → 9 evolve (proposal-based hook)
```

The heavy lifting (scanning logs, redaction, cheap stats) is done by scripts; the actual
*judgment modeling* is done by the LLM reading a redacted sample — so it works regardless
of language or person. Rules are stored in a **registry** (`rules.json`) and compiled into
the installed prompt; install is idempotent (writes only inside a marked block, backs up first).

## Manage & evolve

- **Registry** — every rule (title, directive text, confidence, evidence, enabled, favorite)
  lives in `rules.json`. `compile.py` turns *enabled* rules into the installed prompt.
- **Dashboard** — `python3 dashboard.py` opens a local (127.0.0.1) page to **favorite (★)**
  or **pause (toggle off)** rules and re-install with one click. CLI works too (edit `rules.json`).
- **Proposal-based evolution** — say *"wlm 업데이트"* (the `update` skill) to review
  **proposed** rule changes; nothing is applied without your OK. On each run it scans your recent
  Claude **and** Codex sessions directly (`capture.py --scan`), so review works regardless of tool.
- **Optional auto-badge (Claude only)** — the `auto` skill registers `capture.py` as a Claude
  `SessionEnd` hook that quietly accumulates signals and raises a dashboard badge when enough pile
  up. Codex has no session-end hook, so this convenience is Claude-only — but `update` self-scans
  both tools, so nothing is missed on Codex.

> Your personal data (`rules.json`, `.msgs.jsonl`, `.pending/`) lives in **`~/.work-like-me/`** —
> outside the plugin, so it survives plugin updates and is never shipped. The repo/plugin
> carries only generic tooling + `rules.example.json` (a format template).

## Known limitations (honest)

- **Quality scales with log volume.** Under ~100 messages → low confidence (you'll be warned).
- **Session logs are a "correction fingerprint."** They over-represent what you *push back on*
  and under-represent what you silently approve. Treat the output as a strong draft to **edit**, not a finished profile.
- The bundled `analyze.py` frequency patterns are Korean-tuned **heuristics (supplementary only)**;
  the primary induction is LLM-driven and language-agnostic.
- Installs to Claude (`~/.claude/CLAUDE.md`) and Codex (`~/.codex/AGENTS.md`) global config.
- Some injected-context lines can occasionally leak into the sample.

## License

MIT — see [LICENSE](./LICENSE).
