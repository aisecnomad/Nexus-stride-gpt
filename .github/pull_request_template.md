## What and why

<!-- What does this change, and what problem does it solve? Link the issue, e.g. "Closes #12". -->

## Lane

- [ ] `contrib/*`: headed upstream, branched from upstream's `master`
- [ ] `feat/*` or `fix/*`: this repository only, branched from `main`
- [ ] Sync: `upstream-master` into `main` (merge with **Create a merge commit**)

## Upstream

<!-- contrib/* only: link the upstream issue or pull request, or say when you'll open it. -->

## How I tested it

<!-- Commands you ran, and anything you checked by hand: CLI output, a sample report, the web UI. -->

## Checklist

- [ ] `uv lock --check`, `uv run ruff check .` and `uv run pytest` pass locally
- [ ] Tests added or updated; LLM traffic in tests goes through `ScriptedLLM`, never a real provider
- [ ] Follows AGENTS.md (for example, no `litellm` calls outside `core/llm.py`)
- [ ] `CHANGELOG.md` updated under **Unreleased** for user-visible changes (`feat/*` and `fix/*` only)
- [ ] No secrets, real API keys or real system details in code, tests, fixtures or screenshots
- [ ] No details of an undisclosed vulnerability (see *Security* in `docs/nexus-workflow.md`)
