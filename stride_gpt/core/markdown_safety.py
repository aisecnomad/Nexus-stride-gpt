"""Render untrusted model Markdown as a passive, deliberately small subset.

Parse before sanitizing: inline/reference/nested images all become image nodes,
and encoded link destinations never need URL heuristics. Images are omitted and
links retain only their labels. URL-like labels and text use code spans so GFM
cannot turn them back into clickable autolinks. Raw HTML is literal. Regenerating
Markdown from permitted nodes also prevents a second renderer from interpreting
untrusted text as new Markdown syntax. Code stays readable inside safe fences.
"""

from __future__ import annotations

import re

from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode

_PUNCTUATION = re.compile(r"([\\`*_\[\]#!|<>~])")
_BLOCK_MARKER = re.compile(r"(?m)^([ \t]*)([-+=]|[0-9]{1,9}[.)])(?=\s|$)")


def escape_markdown_text(text: str) -> str:
    """Make plain model text inert in Markdown, including HTML and images."""
    escaped = _PUNCTUATION.sub(r"\\\1", text)
    return _BLOCK_MARKER.sub(
        lambda match: match[1] + match[2][:-1] + "\\" + match[2][-1], escaped
    )


def _code_span(content: str, *, table: bool = False) -> str:
    content = content.replace("\n", " ")
    if table:
        # GFM tables split cells before parsing inline code.
        content = content.replace("|", "\\|")
    fence = "`" * max(1, max((len(m) for m in re.findall(r"`+", content)), default=0) + 1)
    padding = " " if (content.startswith("`") or content.endswith("`") or (
        content.startswith(" ") and content.endswith(" ") and content.strip()
    )) else ""
    return f"{fence}{padding}{content}{padding}{fence}"


def _passive_text(content: str, *, table: bool = False) -> str:
    """Literalize possible autolinks without trying to validate their URLs.

    GFM recognizes protocol URLs, ``www.`` domains and email addresses in
    text nodes, even after an explicit Markdown link has been removed. Code
    spans prevent that second interpretation. Conservatively wrap any whole
    non-whitespace run containing an autolink marker; overmatching merely
    changes typography and never deletes source text. This also covers the
    ``mailto:``/``xmpp:`` email forms and entity-decoded markers.

    https://github.github.com/gfm/#autolinks-extension-
    """
    return "".join(
        _code_span(part, table=table)
        if any(marker in part.lower() for marker in ("://", "www.", "@"))
        else escape_markdown_text(part)
        for part in re.split(r"(\s+)", content)
    )


def _inline_children(node: SyntaxTreeNode, *, table: bool = False) -> str:
    rendered = ""
    for child in node.children:
        part = _inline(child, table=table)
        # Newly literalized URLs can sit immediately beside an existing
        # code span. Separate the delimiters so a second parser does not
        # merge them into a different, unterminated span.
        if rendered.endswith("`") and part.startswith("`"):
            rendered += " "
        rendered += part
    return rendered


def _inline(node: SyntaxTreeNode, *, table: bool = False) -> str:
    kind = node.type
    if kind == "text":
        return _passive_text(node.content, table=table)
    if kind in ("softbreak", "hardbreak"):
        return " " if table else "\n"
    if kind == "code_inline":
        return _code_span(node.content, table=table)
    if kind == "image":
        return escape_markdown_text("[Image omitted]")
    children = _inline_children(node, table=table)
    if kind == "strong":
        return f"**{children}**"
    if kind == "em":
        return f"*{children}*"
    if kind in ("link", "inline"):
        return children
    # Raw HTML is disabled in the parser; keep any future token inert too.
    return children or escape_markdown_text(node.content)


def _block(node: SyntaxTreeNode) -> str:
    kind = node.type
    if kind == "root":
        return "".join(_block(child) for child in node.children)
    if kind == "inline":
        return _inline(node)
    if kind == "paragraph":
        return "".join(_block(child) for child in node.children) + "\n\n"
    if kind == "heading":
        return "#" * int(node.tag[1:]) + " " + "".join(_block(c) for c in node.children) + "\n\n"
    if kind in ("fence", "code_block"):
        content = node.content
        fence = "`" * max(3, max((len(m) for m in re.findall(r"`+", content)), default=0) + 1)
        # Only a simple language identifier can enter the opening fence.
        language = node.info.strip().split()[0] if kind == "fence" and node.info.strip() else ""
        if not re.fullmatch(r"[A-Za-z0-9_+-]*", language):
            language = ""
        return f"{fence}{language}\n{content.rstrip(chr(10))}\n{fence}\n\n"
    if kind == "blockquote":
        content = "".join(_block(child) for child in node.children).rstrip()
        return "\n".join("> " + line for line in content.splitlines()) + "\n\n"
    if kind in ("bullet_list", "ordered_list"):
        start = int(node.attrs.get("start", 1)) if kind == "ordered_list" else 1
        parts = []
        for index, item in enumerate(node.children, start=start):
            marker = f"{index}. " if kind == "ordered_list" else "- "
            content = "".join(_block(child) for child in item.children).strip()
            lines = content.splitlines() or [""]
            parts.append(marker + lines[0] + "\n" + "\n".join(" " * len(marker) + line for line in lines[1:]))
        return "\n".join(parts).rstrip() + "\n\n"
    if kind == "table":
        rows = [row for section in node.children for row in section.children]
        rendered = [
            "| " + " | ".join("".join(_inline(c, table=True) for c in cell.children) for cell in row.children) + " |"
            for row in rows
        ]
        if rendered:
            rendered.insert(1, "| " + " | ".join("---" for _ in rows[0].children) + " |")
        return "\n".join(rendered) + "\n\n"
    if kind == "hr":
        return "---\n\n"
    return escape_markdown_text(node.content) + "\n\n"


def sanitize_markdown(text: str) -> str:
    """Keep useful formatting without active links, images, or raw HTML."""
    parser = MarkdownIt("commonmark", {"html": False, "linkify": False}).enable("table")
    return _block(SyntaxTreeNode(parser.parse(str(text or "")))).rstrip() + ("\n" if text else "")
