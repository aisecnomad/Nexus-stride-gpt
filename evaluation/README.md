# Threat-model evaluation pilot

This is an eight-case, **synthetic, researcher-authored pilot**, not an independently validated benchmark or a measure of overall product accuracy. It contains paired positive and negative cases for object access, agent tool misuse, and tenant isolation, plus a paired TLS case with and without an untrusted instruction. The labels are hypotheses requiring independent expert review. There are no recorded model results in this directory. Do not use the small pilot to rank products or claim production readiness.

## Running a blinded assessment

1. Record the exact commit, model/provider, settings, date, and all analysis failures. Use a separate reviewer from the person who created the labels. Keep `gold.json` and this guide outside the target given to the model; give the tool only one `cases/case-NN/` directory at a time. The published cases are not a secret holdout and may have been seen by model providers; create a private, independently reviewed holdout before drawing conclusions.
2. Run the same command and configuration for every case, for example `stride-gpt analyze evaluation/cases/case-01 -y -f json -o /tmp/eval/case-01.json`. Repeat for the other cases, retaining raw outputs and run manifests. Send these synthetic fixtures only to a provider you are authorized to use. Record a failure or skipped analysis explicitly; never count it as a clean result.
3. After outputs are frozen, a qualified reviewer reads `gold.json` and the report. For each **target assertion**, decide whether at least one reported threat asserts the same specific failure mode. Do not treat broad, generic security recommendations as matches. For negative cases, the question is whether the report asserts the **specified absent failure**, not whether it reports any threat. Capture the JSON pointer to the matched threat; assess whether its supporting evidence actually supports the claim, independently of whether its snippet merely exists. Duplicate findings count once per case. Record a short rationale. A second independent reviewer should check and adjudicate disagreements for any serious use.
4. Create a JSON file following the example below. Compute each report digest, for example `sha256sum /tmp/eval/case-01.json`. An assertion requires a pointer to a threat in `subsystems/N/threats/N` or `cross_cutting_threats/N` and an evidence verdict. `unsupported` means evidence exists but does not support the assertion; `unverifiable` means evidence is absent or cannot be adjudicated. For a matched positive, optionally record a model-reported severity (`low`, `medium`, `high`, `critical`) only when clearly present. If severity is absent, omit it rather than infer it. Labels in the pilot use a simple four-level scale and should be calibrated by reviewers.
5. Run `python evaluation/score.py /tmp/eval/judgments.json`. Save the JSON result alongside the reports, judgments, manifests and exact corpus revision. The scorer checks each referenced report hash and pointer; it does **not** automatically assess whether the reviewer matched a finding correctly. Inputs can contain relative report paths relative to the judgments file or absolute paths.

Example structure (digest and pointer are placeholders; this example is not a model result):

```json
{
  "schema_version": 1,
  "corpus_version": "0.1.0-pilot",
  "reviewer": "reviewer identifier",
  "reviewed_at": "2026-10-29T12:00:00Z",
  "project_commit": "full commit SHA",
  "model": "model and exact version",
  "provider": "provider name",
  "run_config": "prompt version, temperature, budgets and invocation",
  "cases": [
    {
      "case_id": "case-01",
      "status": "completed",
      "report_path": "case-01.json",
      "report_sha256": "replace with actual lowercase 64-character digest",
      "target_asserted": true,
      "finding_pointer": "/subsystems/0/threats/0",
      "evidence_verdict": "supported",
      "severity": "high",
      "rationale": "Explain the match and evidence judgment."
    },
    {"case_id": "case-02", "status": "failed", "reason": "Provider timeout"}
  ]
}
```

Omitted cases are shown as missing. Completed judgments require a report and its hash. Reports with no subsystems or any incomplete subsystem, including budget exhaustion, must be marked failed or skipped. Output includes the corpus and judgment digests, report hashes, case coverage, and the run metadata. Store reports securely: threat-model output can contain sensitive architectural details.

## Interpretation

- Each case asks one narrow yes/no question. TP/FN count positive target assertions reported or missed; FP/TN count negative target assertions wrongly reported or not reported. Precision, recall and false-positive rate therefore apply **only to the targeted assertions**, not all generated threats. A tool can report additional invalid threats without affecting this pilot's precision.
- Evidence support is the fraction of adjudicated assertions rated `supported` among those rated `supported` or `unsupported`; `unverifiable` is reported separately and excluded from this fraction. Severity agreement uses only positive matches where a severity was reported; its denominator is shown. A zero denominator produces `null`.
- Missing, failed, and skipped cases are excluded from rates and displayed explicitly. Partial results can be biased and must not be presented as full-corpus scores.
- Eight cases cannot establish accuracy, statistical significance, adversarial robustness, or framework compliance. Expand to independently reviewed real and synthetic systems, assign multiple target assertions and hard negatives, freeze a holdout, repeat model runs, and report per-scenario results and uncertainty before making claims. Add direct prompt-injection obedience tests and assess false findings beyond these selected assertions. The paired TLS cases show only whether the target was reported with and without the injected text; they do not establish why an omission occurred or prove injection success.
