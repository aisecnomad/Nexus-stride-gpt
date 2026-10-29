"""The pilot scorer must not turn failed runs into negative findings."""
from __future__ import annotations

import hashlib
import json

import pytest

from evaluation.score import InvalidEvaluationError, score


def test_adjudicated_scores_preserve_missing_cases_and_evidence_limits(tmp_path):
    gold = {
        'schema_version': 1,
        'corpus_version': 'test',
        'cases': [
            {'case_id': 'a', 'target_present': True, 'severity': 'high'},
            {'case_id': 'b', 'target_present': False, 'severity': None},
            {'case_id': 'c', 'target_present': True, 'severity': 'medium'},
            {'case_id': 'd', 'target_present': False, 'severity': None},
        ],
    }
    report_bytes = json.dumps({'subsystems': [{'outcome': 'completed', 'threats': [{'Scenario': 'example'}]}]}).encode()
    (tmp_path / 'report.json').write_bytes(report_bytes)
    report_hash = hashlib.sha256(report_bytes).hexdigest()
    submission = {
        'schema_version': 1, 'corpus_version': 'test', 'reviewer': 'test reviewer',
        'reviewed_at': '2026-01-01', 'project_commit': 'commit', 'model': 'test model',
        'provider': 'test', 'run_config': 'test',
        'cases': [
            {'case_id': 'a', 'status': 'completed', 'target_asserted': True,
             'rationale': 'matched', 'report_path': 'report.json', 'report_sha256': report_hash,
             'finding_pointer': '/subsystems/0/threats/0', 'evidence_verdict': 'unverifiable',
             'severity': 'high'},
            {'case_id': 'b', 'status': 'completed', 'target_asserted': False,
             'rationale': 'not asserted', 'report_path': 'report.json', 'report_sha256': report_hash},
            {'case_id': 'c', 'status': 'failed', 'reason': 'timeout'},
        ],
    }
    gold_path = tmp_path / 'gold.json'
    judgments_path = tmp_path / 'judgments.json'
    gold_path.write_text(json.dumps(gold))
    judgments_path.write_text(json.dumps(submission))
    result = score(gold_path, judgments_path)
    assert result['counts'] == {'tp': 1, 'fp': 0, 'tn': 1, 'fn': 0}
    assert result['cases_scored'] == 2
    assert {item['case_id'] for item in result['incomplete']} == {'c', 'd'}
    assert result['evidence_supported_fraction'] is None
    assert result['severity_agreement'] == 1
    assert result['severity_agreement_n'] == 1

    (tmp_path / 'report.json').write_text('{}')
    with pytest.raises(InvalidEvaluationError, match='hash mismatch'):
        score(gold_path, judgments_path)


def test_invalid_finding_pointer_cannot_claim_an_evidence_match(tmp_path):
    gold = {'schema_version': 1, 'corpus_version': 'test', 'cases': [
        {'case_id': 'a', 'target_present': True, 'severity': 'high'},
    ]}
    report_bytes = json.dumps({'subsystems': [{'outcome': 'completed', 'threats': []}]}).encode()
    (tmp_path / 'report.json').write_bytes(report_bytes)
    submission = {
        'schema_version': 1, 'corpus_version': 'test', 'reviewer': 'r', 'reviewed_at': 'now',
        'project_commit': 'c', 'model': 'm', 'provider': 'p', 'run_config': 'config',
        'cases': [{'case_id': 'a', 'status': 'completed', 'target_asserted': True,
                   'report_path': 'report.json', 'report_sha256': hashlib.sha256(report_bytes).hexdigest(),
                   'finding_pointer': '/subsystems', 'evidence_verdict': 'supported', 'rationale': 'x'}],
    }
    (tmp_path / 'gold.json').write_text(json.dumps(gold))
    (tmp_path / 'judgments.json').write_text(json.dumps(submission))
    with pytest.raises(InvalidEvaluationError, match='pointer must identify a threat'):
        score(tmp_path / 'gold.json', tmp_path / 'judgments.json')
