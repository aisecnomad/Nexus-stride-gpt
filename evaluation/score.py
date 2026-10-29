"""Score human-adjudicated target assertions against a small synthetic corpus.

This is not an automatic semantic judge: each judgment must cite a JSON report
and a JSON pointer to the finding the reviewer matched to the target assertion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


class InvalidEvaluationError(ValueError):
    """Input is incomplete or does not match the corpus contract."""


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _ratio(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 4) if denominator else None


def _pointer(document: Any, pointer: str) -> Any:
    """Resolve an RFC 6901 JSON pointer; reject malformed indices and escapes."""
    if not isinstance(pointer, str) or not pointer.startswith('/'):
        raise InvalidEvaluationError('finding pointer must be a nonempty JSON pointer')
    value = document
    for token in pointer[1:].split('/'):
        if re.search(r'~(?![01])', token):
            raise InvalidEvaluationError('invalid pointer escape')
        token = token.replace('~1', '/').replace('~0', '~')
        try:
            if isinstance(value, list):
                if not re.fullmatch(r'0|[1-9][0-9]*', token):
                    raise InvalidEvaluationError('invalid array index')
                value = value[int(token)]
            elif isinstance(value, dict):
                value = value[token]
            else:
                raise InvalidEvaluationError('pointer traverses a scalar')
        except (IndexError, KeyError) as exc:
            raise InvalidEvaluationError('pointer does not exist') from exc
    return value


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def score(gold_path: Path, judgments_path: Path) -> dict[str, Any]:
    """Validate provenance and score only completed, adjudicated cases."""
    gold = json.loads(gold_path.read_text(encoding='utf-8'))
    submission = json.loads(judgments_path.read_text(encoding='utf-8'))
    if gold.get('schema_version') != 1 or submission.get('schema_version') != 1:
        raise InvalidEvaluationError('unsupported schema version')
    if submission.get('corpus_version') != gold.get('corpus_version'):
        raise InvalidEvaluationError('corpus version mismatch')
    for key in ('reviewer', 'reviewed_at', 'project_commit', 'model', 'provider', 'run_config'):
        if not _nonempty(submission.get(key)):
            raise InvalidEvaluationError(f'missing run metadata: {key}')
    cases = gold.get('cases')
    entries = submission.get('cases')
    if not isinstance(cases, list) or not cases or not isinstance(entries, list):
        raise InvalidEvaluationError('invalid cases array')
    lookup: dict[str, dict[str, Any]] = {}
    for case in cases:
        if not isinstance(case, dict) or not _nonempty(case.get('case_id')):
            raise InvalidEvaluationError('invalid case ID in gold')
        case_id = case['case_id']
        if case_id in lookup or type(case.get('target_present')) is not bool:
            raise InvalidEvaluationError('duplicate ID or invalid label in gold')
        if case['target_present'] and case.get('severity') not in {'low', 'medium', 'high', 'critical'}:
            raise InvalidEvaluationError('positive gold case lacks severity')
        lookup[case_id] = case
    seen: set[str] = set()
    counts = {'tp': 0, 'fp': 0, 'tn': 0, 'fn': 0}
    evidence = {'supported': 0, 'unsupported': 0, 'unverifiable': 0}
    severity_eligible = severity_agree = 0
    incomplete = []
    sources = []
    for entry in entries:
        if not isinstance(entry, dict) or entry.get('case_id') not in lookup:
            raise InvalidEvaluationError('unknown or invalid case')
        case_id = entry['case_id']
        if case_id in seen:
            raise InvalidEvaluationError(f'duplicate case: {case_id}')
        seen.add(case_id)
        status = entry.get('status')
        if status in {'failed', 'skipped'}:
            if not _nonempty(entry.get('reason')):
                raise InvalidEvaluationError(f'{case_id}: incomplete case requires a reason')
            incomplete.append({'case_id': case_id, 'status': status, 'reason': entry['reason']})
            continue
        if status != 'completed' or type(entry.get('target_asserted')) is not bool:
            raise InvalidEvaluationError(f'{case_id}: invalid completed judgment')
        if not _nonempty(entry.get('rationale')):
            raise InvalidEvaluationError(f'{case_id}: rationale is required')
        report_name = entry.get('report_path')
        if not _nonempty(report_name) or not re.fullmatch(r'[0-9a-f]{64}', str(entry.get('report_sha256', ''))):
            raise InvalidEvaluationError(f'{case_id}: report path and SHA-256 are required')
        report_path = judgments_path.parent / report_name
        if _hash(report_path) != entry['report_sha256']:
            raise InvalidEvaluationError(f'{case_id}: report hash mismatch')
        report = json.loads(report_path.read_text(encoding='utf-8'))
        if not isinstance(report, dict) or not isinstance(report.get('subsystems'), list):
            raise InvalidEvaluationError(f'{case_id}: expected an analyze JSON report')
        if not report['subsystems'] or any(
            not isinstance(subsystem, dict) or subsystem.get('outcome') != 'completed'
            for subsystem in report['subsystems']
        ) or (report.get('metadata') or {}).get('status') == 'cancelled':
            raise InvalidEvaluationError(
                f'{case_id}: incomplete report must be recorded as failed or skipped'
            )
        sources.append({'case_id': case_id, 'report_sha256': entry['report_sha256']})
        asserted = entry['target_asserted']
        present = lookup[case_id]['target_present']
        counts['tp' if present and asserted else 'fn' if present else 'fp' if asserted else 'tn'] += 1
        if asserted:
            pointer = entry.get('finding_pointer')
            # Limit references to threat arrays, not arbitrary report strings.
            if not isinstance(pointer, str) or not re.fullmatch(
                r'/subsystems/(0|[1-9][0-9]*)/threats/(0|[1-9][0-9]*)|/cross_cutting_threats/(0|[1-9][0-9]*)', pointer
            ) or not isinstance(_pointer(report, pointer), dict):
                raise InvalidEvaluationError(f'{case_id}: pointer must identify a threat')
            verdict = entry.get('evidence_verdict')
            if verdict not in evidence:
                raise InvalidEvaluationError(f'{case_id}: evidence verdict is required')
            evidence[verdict] += 1
            if present and entry.get('severity') is not None:
                if entry['severity'] not in {'low', 'medium', 'high', 'critical'}:
                    raise InvalidEvaluationError(f'{case_id}: invalid severity')
                severity_eligible += 1
                severity_agree += entry['severity'] == lookup[case_id]['severity']
    incomplete.extend({'case_id': case_id, 'status': 'missing'} for case_id in sorted(lookup.keys() - seen))
    tp, fp, tn, fn = (counts[k] for k in ('tp', 'fp', 'tn', 'fn'))
    return {
        'corpus_version': gold['corpus_version'],
        'gold_sha256': _hash(gold_path),
        'judgments_sha256': _hash(judgments_path),
        'metadata': {key: submission[key] for key in ('reviewer', 'reviewed_at', 'project_commit', 'model', 'provider', 'run_config')},
        'report_hashes': sources,
        'cases_total': len(lookup), 'cases_scored': len(sources), 'incomplete': incomplete,
        'counts': counts,
        'target_precision': _ratio(tp, tp + fp),
        'target_recall': _ratio(tp, tp + fn),
        'target_false_positive_rate': _ratio(fp, fp + tn),
        'evidence_verdicts': evidence,
        'evidence_supported_fraction': _ratio(evidence['supported'], evidence['supported'] + evidence['unsupported']),
        'severity_agreement': _ratio(severity_agree, severity_eligible),
        'severity_agreement_n': severity_eligible,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('judgments', type=Path, help='human adjudication JSON')
    parser.add_argument('--gold', type=Path, default=Path(__file__).with_name('gold.json'))
    args = parser.parse_args()
    try:
        print(json.dumps(score(args.gold, args.judgments), indent=2))
    except (OSError, ValueError, TypeError, KeyError) as exc:
        parser.exit(2, f'evaluation error: {exc}\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
