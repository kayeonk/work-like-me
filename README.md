# my-persona

> Turn your real AI coding-session history into a personal, **directive system prompt** —
> generated and installed **locally**, privacy-first.

`my-persona` reads your local Claude Code / Codex session logs, extracts *your* messages,
and induces your working style — values, judgment heuristics, communication style, and
do/don'ts — then writes a directive system prompt and installs it into your global AI
config so **every project inherits how you actually work**.

Unlike fictional "persona" skills or one-off "summarize my chat history" prompts, this is:

- **Data-driven** — built from your real sessions, with frequency evidence per rule.
- **Local & private** — no network calls; secrets are redacted before any analysis.
- **Directive** — produces an installable system prompt (`You must… / Do not…`), not a description.
- **Manageable** — rules live in a registry you can favorite / pause per-rule via a local dashboard.
- **Self-evolving (opt-in)** — a SessionEnd hook accumulates new signals and *proposes* updates.

## Privacy

- Runs **100% locally**. Your logs never leave your machine.
- Secrets/PII (emails, API keys, tokens, long hashes) are **redacted before** anything is sampled.
- Company/project names are anonymized in the output by default.

## Requirements

- [Claude Code](https://claude.com/claude-code) (the skill host)
- Python 3
- Optional: Codex CLI session logs

## ⚡ Install

Works as a plugin in **both Claude Code and Codex** (one repo, one command set).

**Claude Code** (slash commands, or the `/plugin` UI → Marketplaces):
```text
/plugin marketplace add kayeonk/work-like-me
/plugin install my-persona@kayeon-plugins
/reload-plugins
```

**Codex** (terminal):
```bash
codex plugin marketplace add kayeonk/work-like-me
codex plugin add my-persona@kayeon-plugins
```

Then just say: **"내 페르소나 만들어줘"** (or `make my persona`). The skill walks you through
source selection → a short interview → review → install. Nothing leaves your machine.

> **Local development:** `/plugin marketplace add ~/path/to/my-persona`, then install as above.
> Your personal data lives in **`~/.my-persona/`** — outside the plugin — so it survives
> updates and is never shipped.

## Commands

After installing, these slash commands are available (namespaced by the plugin):

| Command | What it does |
|---------|--------------|
| `/my-persona:create` | Generate your persona from session logs and install it |
| `/my-persona:dashboard` | Open the local dashboard to favorite / pause rules and apply |
| `/my-persona:update` | Review newly accumulated signals and propose rule updates |
| `/my-persona:auto` | Turn auto-suggested persona updates (over time) on/off |

You can also just say **"내 페르소나 만들어줘"** (or "make my persona") to start.

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
- **Proposal-based evolution** — register `capture.py` as a `SessionEnd` hook. It accumulates
  new (redacted) signals in `.pending/`; when enough pile up it flags for review. Say
  *"my-persona 업데이트"* to see **proposed** rule changes — nothing is applied without your OK.

> Your personal data (`rules.json`, `.msgs.jsonl`, `.pending/`) lives in **`~/.my-persona/`** —
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
