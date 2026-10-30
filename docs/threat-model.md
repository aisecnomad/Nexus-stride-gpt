# Threat Model of STRIDE-GPT

This document is a lightweight STRIDE threat model of the STRIDE-GPT tool itself. It covers the CLI agent, the shared core, the Streamlit web UI, and the operational environment in which either may be deployed. It is intended for operators, reviewers, and contributors who need to understand the residual risks of running an LLM-powered agent with filesystem access.

This is a review model, not a certification or a claim that deployment controls are enabled. Code-level safeguards and operator responsibilities are distinguished below. The strengthened filesystem, regex, credential and persistence boundaries depend on the security-hardening changes described in the changelog; verify those implementations and their regression tests in the deployed revision. Residual risk depends on privileges, data sensitivity, tenant trust and the execution environment.

## Assets

| Asset | Sensitivity | Notes |
|-------|-------------|-------|
| Source code under analysis | High | May contain secrets, IP, or regulated data. |
| LLM provider API keys | Critical | Stored in environment or `~/.stride-gpt/config.json`. |
| Generated threat reports | High | Contain security findings and evidence snippets. |
| Agent intermediate state (`plan.json`, findings, etc.) | Medium | May contain paths and partial results. |
| CI job tokens / `.git` metadata | Critical | VCS paths are denied. Remove credentials from the analysis copy and environment; a path filter cannot identify every secret. |
| Web UI session state | High | Streamlit session state lives in server memory. Inputs and rendered/downloaded outputs also reach the browser. No durable web report store is created by default. |

## Trust Boundaries

1. **Operator workstation / CI runner** — trusted. Holds configuration, API keys, and the analysis root.
2. **Analysis root** — untrusted. The codebase under review may contain malicious content, planted prompt injection, symlinks, or oversized files.
3. **LLM provider** — untrusted for confidentiality. Prompts and tool results leave the operator’s control.
4. **Web UI (when exposed)** — untrusted network endpoint. Must be fronted by an identity-aware proxy.
5. **Third-party reference data** (MITRE STIX, control catalogues) — trusted after regeneration and review.

## STRIDE Analysis

### Spoofing

| Threat | Component | Existing Controls | Residual Risk |
|--------|-----------|-------------------|---------------|
| Prompt injection that causes attacker-controlled tool calls | Agent tools | Tool dispatch, path confinement and VCS/credential-path denial constrain access | Prompt text remains untrusted. These controls do not prevent every in-scope disclosure or unsafe model recommendation; planted-comment tests exercise tools, not model resistance. |
| Forged or irrelevant evidence | Evidence verification | Bounded snippet lookup with documented whitespace/comment normalization; unmatched evidence is flagged | A matched snippet proves source presence, not exploitability, completeness or correctness. Unverified threats are retained. |
| Fake LLM provider or man-in-the-middle | LLM client | Operator selects the provider and endpoint; SDK transport verifies TLS for HTTPS | Custom/local endpoints can use HTTP. Use authenticated HTTPS for remote endpoints; restrict egress and endpoint configuration. |

### Tampering

| Threat | Component | Existing Controls | Residual Risk |
|--------|-----------|-------------------|---------------|
| Modification of reference cards or control catalogue | Controls / prompts | Generated control cards and drift checks; reviewed packaged MITRE catalogues | A malicious source-catalogue change can pass regeneration checks. Require independent review of reference data, provenance and mappings. |
| Alteration or disclosure of intermediate run files | Persistence | Hardened builds use private exclusive temporary files and atomic replacement; manifests redact selected paths and omit configured credentials | No cryptographic authenticity. The same OS principal can modify files; snippets and free-text output may still contain sensitive data. |
| Symlink attacks that redirect reads outside the sandbox | Tools | Hardened source/evidence reads use descriptor-relative no-follow opens; unsupported platforms fail closed | `resolve()` alone is not race-safe. Hard links, mounts and concurrent mutation remain limitations; analyze a private sanitized copy. |

### Repudiation

| Threat | Component | Existing Controls | Residual Risk |
|--------|-----------|-------------------|---------------|
| Operator denies having run an analysis that leaked data | Logging | Token accounting, run manifests (redacted), local reports | Medium — no central audit trail unless the operator adds one. |

### Information Disclosure

| Threat | Component | Existing Controls | Residual Risk |
|--------|-----------|-------------------|---------------|
| Agent reads VCS metadata or credentials in a clone | Tools | Case-insensitive VCS denial; hardened builds also filter common sensitive paths and credential-like content | Filters cannot detect every secret. Remove secrets and use a minimally privileged execution identity. |
| Prompts or code snippets sent to the LLM provider | LLM client | Operator choice of provider; documented in SECURITY.md | Medium–High (inherent to cloud LLM use) |
| Report leakage or operator-credential misuse via shared web UI | Web UI | Per-session server-side state; hardened builds resolve operator keys without putting them in widgets and disable shared GitHub credentials by default | No built-in authentication or tenant authorization. All authorized users may spend a configured server LLM key; add a proxy, quotas and a single-trust-domain deployment boundary. |
| Path or secret leakage in shareable manifests | Persistence | Selected path-field redaction; configured API keys/endpoints excluded from manifest metadata | This is not general content redaction. Review code snippets, threat text and outputs before sharing. |

### Denial of Service

| Threat | Component | Existing Controls | Residual Risk |
|--------|-----------|-------------------|---------------|
| ReDoS via malicious grep pattern | `grep_content` | Hardened builds combine pattern caps with regex-engine timeouts and search deadlines | Nested-quantifier heuristics alone are incomplete. Enforce process/resource limits for hostile repositories. |
| Enormous files or directory trees | Tools | File size caps, directory entry caps, budget limits | Low |
| LLM provider rate limits or timeouts | LLM client | Retries with backoff; configurable timeouts | Medium |

### Elevation of Privilege

| Threat | Component | Existing Controls | Residual Risk |
|--------|-----------|-------------------|---------------|
| Agent escapes file boundaries or exposes host secrets | Tools | Confined reads, path/content filters and bounded tool dispatch in hardened builds | The CLI shares its OS principal with the operator. Run in a container/VM with only the sanitized target and required credentials; file confinement is not OS isolation. |
| Web UI container breakout | Docker | Non-root image user; Compose adds capability drop and `no-new-privileges` | Compose settings do not automatically apply to other launch methods. Kernel/dependency vulnerabilities remain; enforce host isolation and patching. |
| Prompt injection that causes the model to recommend dangerous mitigations | Synthesis | Control catalogue constrains IDs; human review expected | Medium |

## Recommended Operational Controls

- **Untrusted codebase operating procedure** (operator guidance, not a CLI mode or flag):
  - Run the CLI as a non-privileged user inside a disposable container/VM; mount only a private sanitized copy of the target. Remove unrelated credentials and disable network access except to approved endpoints.
  - Prefer offline / air-gapped LLM endpoints when possible.
  - Review the generated plan before approving subsystem analysis.
  - Treat all evidence marked unverified as suspect; also review verified evidence for relevance and exploitability.
- **Web UI**:
  - Never expose the Streamlit process directly. Place an identity-aware proxy (OIDC + phishing-resistant MFA) in front of it.
  - Enforce TLS 1.3 and an egress allow-list limited to the chosen LLM provider.
  - Inject API keys at runtime from a secrets manager; never bake them into the image.
- **CI**:
  - Maintainers must enable the dependency graph and configure required checks in repository settings. Workflow files alone do not establish branch protection; verify actual runs and the configured ruleset.
  - Do not grant the agent a checkout token that has write or package-publish scopes.

## Ownership and Verification

| Boundary | Owner | Verification |
|----------|-------|--------------|
| Source/evidence tools | Agent-tool maintainer | Adversarial traversal, symlink-swap, sensitive-content, size-limit and regex-deadline regression tests; inspect actual results on the target OS. |
| Model output and reports | Core/report maintainer | Parser/schema tests, malicious Markdown/HTML fixtures, packaged MITRE lookup tests; analyst reviews evidence relevance. |
| Credentials and sessions | Web maintainer + deployment owner | Credential-widget regressions; inspect browser payloads with test keys; verify proxy identity, quotas and session separation. |
| Checkpoints and artifacts | Persistence maintainer + operator | Exclusive-write/permission tests and resume-scope tests; operator restricts storage ACLs and reviews exported content. |
| Supply chain and CI | Repository maintainer | Lock consistency, clean wheel installation/audit, security workflow results and live required-check settings. |

## Residual Risks That Cannot Be Eliminated

- The model can still produce incorrect, incomplete, or hallucinated threats. Evidence verification reduces but does not eliminate this.
- Any data sent to a third-party LLM provider leaves the operator’s control.
- A sufficiently sophisticated prompt injection combined with a bug in the tool layer could still cause unexpected behaviour. The adversarial test suite is intended to catch regressions in the known classes of attack.

## Related Documents

- [Architecture](architecture.md) — component diagram and trust boundaries
- [Deployment hardening](deployment-hardening.md) — reference architecture for a shared web UI
- [AGENTS.md](../AGENTS.md) — contributor rules and progressive disclosure
- [SECURITY.md](../SECURITY.md) — vulnerability reporting and best practices
