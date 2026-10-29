# Contributing to STRIDE-GPT

Thanks for helping. Pull requests are welcome; for a large change, open an issue first so we can agree on the approach. If you are an AI coding agent, read [AGENTS.md](AGENTS.md) before you start: it covers the architecture, the conventions, and the things not to do.

## Development setup

STRIDE-GPT uses [uv](https://docs.astral.sh/uv/), and `uv.lock` is the single source of truth for dependencies.

```bash
git clone https://github.com/mrwadams/stride-gpt.git
cd stride-gpt
uv sync                      # CLI, web UI and dev dependencies
uv run stride-gpt --version
uv run streamlit run apps/web/main.py
```

## Before you open a pull request

CI runs the same checks on Python 3.12, 3.13 and 3.14:

```bash
uv run ruff check .          # lint
uv run pytest -q             # tests (a few seconds; no network, no API keys)
uv lock --check              # pyproject.toml and uv.lock agree
python scripts/build_control_catalog.py --check   # generated cards and docs are current
```

- **Tests never call a real LLM.** Drive anything that sends LLM traffic with `ScriptedLLM` from `tests/fakes.py`; it also checks that the conversation is one a strict provider would accept.
- **Assert structure, not prose.** For prompts and cards, check that a code, field or column is present, not exact wording.
- **Dependencies** go in `pyproject.toml`, then `uv lock`. The CLI's runtime dependencies stay lean; web-only packages belong in the `web` dependency group.

## Common changes

| Change | Where | Remember to |
|--------|-------|-------------|
| A reference card (new threat lens) | `stride_gpt/core/prompts/threat_model/<name>.md` with YAML frontmatter | If it adds a field, accept it in `report_threat` (`agent/tools.py`) and render it (`core/report_utils.py`); see AGENTS.md |
| A control, domain or framework | `stride_gpt/core/controls/catalog.toml` | Run `python scripts/build_control_catalog.py` and commit the regenerated cards and `docs/` pages. Never reuse or renumber a published control ID |
| MITRE catalogues | `scripts/refresh_mitre_cards.py` | Regenerate from upstream data; never hand-edit the technique lists |
| An LLM provider or model | `stride_gpt/models.py`, `core/llm.py:_build_litellm_kwargs` | Every call goes through `core/llm.py` |
| A report format | `agent/report.py`, `cli.py:OutputFormat` | Keep the live and from-JSON renderers identical |

### Control catalogue conventions

- **Objectives are prompt text.** The model reads each control's one-sentence `objective` on every analysis, so keep it specific and short.
- **Guidance is for people.** It appears only in the docs. Cite the standard behind each recommendation (an RFC, NIST SP, OWASP ASVS chapter).
- **Map conservatively.** Add a framework reference only where the control directly helps satisfy the requirement; an honest gap is better than a stretched mapping. Every reference must exist in that framework's registry, or the loader rejects the catalogue.
- **Cite verifiable sources.** Framework registries hold identifiers and titles as published. When a standard revises its numbering, update the registry and the framework's `version`.

## Commits and pull requests

- Keep each pull request focused on one change, and explain *why* in its description.
- Update `CHANGELOG.md` under **Unreleased** for anything user-visible.
- Releases are cut by the maintainer from tags; see [RELEASING.md](RELEASING.md).

## Security issues

Please don't open public issues for vulnerabilities. Use GitHub's [private vulnerability reporting](https://github.com/mrwadams/stride-gpt/security/advisories/new); see [SECURITY.md](SECURITY.md).
