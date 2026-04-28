# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Status

v0.1 is implemented. Source lives under `src/gitsummarizer/`, tests under `tests/`. The package is installable via `pip install -e .` (see `pyproject.toml`); after that, `python -m gitsummarizer` boots the aiogram polling loop. Note that the README's installation steps (`pip install -r requirements.txt`, `python app.py`) are out of date — use `pip install -e .` and `python -m gitsummarizer` instead.

`specs/PRD.md` is still the source of truth for the output contract (Initiative schema, Markdown layout, filename format).

## Common Commands

```bash
python -m venv .venv && .venv/Scripts/activate    # Windows; use bin/activate on POSIX
pip install -e .                                   # installs runtime + dev deps via pyproject
pytest tests/                                      # all unit tests (~0.2s, no network)
pytest tests/test_schema.py -v                     # single file
pytest tests/test_window_parsing.py::test_one_week # single test
python -m gitsummarizer                            # boot the bot (requires .env)
```

## Product Overview

GitSummarizer AI is a Telegram bot that pulls commit history from a GitLab repo over a window (e.g. `/report 1w`, `/report 1m`), uses an LLM to **group related commits into single "Initiatives"**, and returns a Markdown roadmap as a document attachment in the same chat.

Output filename convention: `engineer_roadmap_ddmmyyyy_<repo_name>.md`.

Target latency per `/report`: under 15 seconds.

## Intended Stack

- **Python 3.10+**
- **LangChain** for prompt management and chains
- **OpenAI GPT-4o mini** as the LLM (chosen for reasoning/cost ratio — do not silently swap models)
- **python-gitlab** for commit retrieval
- **python-telegram-bot** or **aiogram** for the bot interface
- Dockerized deployment is the recommended target

## Architecture

Four layers, one module each, all under `src/gitsummarizer/`:

1. **Telegram interface** (`bot.py`, `__main__.py`, `windows.py`) — aiogram Router with `/report <window> [project]`. `windows.py` parses `1w` / `7d` / `1m` / `30d` into a `timedelta`. The `/report` handler runs the sync GitLab call through `asyncio.to_thread`. Handles "No commits found in this period." explicitly. `__main__.py` boots polling.
2. **GitLab client** (`gitlab_client.py`) — sync `fetch_commits(project, since)` returning `CommitData` (sha, message, author, committed_at, **changed_files**). The changed-file list is filename-only (no patches) and is what lets the LLM estimate Weight/Difficulty — never strip it.
3. **LLM chain** (`llm_chain.py`) — `ChatPromptTemplate` + `PydanticOutputParser(pydantic_object=Roadmap)` + `ChatOpenAI`. The parser is the contract; the prompt text is the hint. `summarize()` is async.
4. **Markdown writer** (`markdown_writer.py`) — `render_markdown(roadmap)` and `write_roadmap(roadmap, output_dir)`. Filename: `engineer_roadmap_<ddmmyyyy>_<repo_slug>.md` where the date is `period_end` and the slug replaces `/` with `_`.

`schema.py` holds the `Initiative` and `Roadmap` Pydantic models plus the four enums. `config.py` exposes `get_settings()` (lazy, `lru_cache`'d) — never instantiate `Settings()` at import time, since tests import sibling modules without env vars set.

## Initiative Schema (the output contract)

Every row the LLM produces must conform to these fields. Treat this as the canonical schema for the Pydantic model:

| Field | Allowed values / notes |
| :--- | :--- |
| Initiative | Free text — business reason / high-level purpose |
| Description | Free text — technical-but-readable summary |
| Category | One of: OKR, Improve Soft Skill, Improve Hard Skill, System Performance, Efficiency, Operational, System Design, Security, Database, AI, Standardization, Others |
| Weight | Fibonacci-style estimate: 1, 2, 3, 5, 8 |
| Status | Open, In Progress, Closed, Canceled, On Hold |
| Priority | Low, Medium, High |
| Finish Date | Date of the latest commit in the group |
| Output | Tangible result (e.g. "New API endpoint") |
| Difficulty | Used in sample output (Easy/Hard) — present in the Markdown table even though the field table in the PRD omits it |

The rendered Markdown must start with `# Engineering Roadmap: [Repository Name]` and a `**Period:** dd/mm/yyyy - dd/mm/yyyy` line, followed by the table (see `specs/PRD.md` §5 for the exact sample).

## Required Secrets

The bot needs at minimum:
- Telegram bot token (from `@BotFather`)
- GitLab Personal Access Token (PAT) with read access to the target repo(s)
- OpenAI API key

No `.env` template exists yet — when adding configuration, create one and document required variables here.

## Key Implementation Notes from the PRD

- **Commit grouping is an LLM responsibility, not a heuristic.** The PRD explicitly says to feed the raw commit list to GPT-4o mini and ask it to "group related commits into single initiatives." Don't pre-group on the Python side.
- **Difficulty/Weight inference depends on changed-file volume.** The GitLab fetcher must include the changed-files list per commit, or the LLM cannot estimate these correctly.
- **Pydantic parsing is mandatory** to prevent format hallucination — bypassing it (e.g. asking the LLM to emit Markdown directly) violates the reliability requirement.
