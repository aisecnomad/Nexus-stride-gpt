#!/usr/bin/env python3
"""Regenerate the control reference cards and docs from the control catalogue.

``stride_gpt/core/controls/catalog.toml`` is the single source of truth. This
script renders it into:

- ``stride_gpt/core/prompts/threat_model/security_controls.md`` and
  ``ai_controls.md`` — the reference cards the agent loads, and
- ``docs/controls-catalog.md`` and ``docs/framework-crosswalks.md``.

Usage::

    python scripts/build_control_catalog.py          # rewrite the files
    python scripts/build_control_catalog.py --check  # exit 1 if any is stale

``tests/test_controls.py`` runs the same comparison, so CI fails when the
catalogue and its renderings drift apart.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from stride_gpt.core.controls.render import generated_files  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="Don't write; exit 1 if any generated file is missing or out of date.",
    )
    args = parser.parse_args(argv)

    stale: list[str] = []
    for relative, content in generated_files().items():
        path = REPO_ROOT / relative
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current == content:
            continue
        stale.append(relative)
        if not args.check:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            print(f"wrote {relative}")

    if args.check and stale:
        print("Out of date — run python scripts/build_control_catalog.py:", file=sys.stderr)
        for relative in stale:
            print(f"  {relative}", file=sys.stderr)
        return 1
    if not stale:
        print("All generated files are up to date.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
