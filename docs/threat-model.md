# Threat Model of STRIDE-GPT

This document is a lightweight STRIDE threat model of the STRIDE-GPT tool itself. It covers the CLI agent, the shared core, the Streamlit web UI, and the operational environment in which either may be deployed. It is intended for operators, reviewers, and contributors who need to understand the residual risks of running an LLM-powered agent with filesystem access.

The controls described here already exist in the codebase (see `AGENTS.md`, `docs/architecture.md`, and `docs/deployment-hardening.md`). This page makes the model explicit.

## Assets

| Asset | Sensitivity | Notes |
|-------|-------------|-------|
| Source code under analysis | High | May contain secrets, IP, or regulated data. |
| LLM provider API keys | Critical | Stored in environment or `~/.stride-gpt/config.json`. |
| Generated threat reports | High | Contain security findings and evidence snippets. |
| Agent intermediate state (`plan.json`, findings, etc.) | Medium | May contain paths and partial results. |
| CI job tokens / `.git` metadata | Critical | Must never be readable by the agent. |
| Web UI session state | Medium | Browser-local; still contains model I/O. |

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
| Prompt injection that causes the agent to call tools with attacker-controlled paths | Agent tools | Path sandbox (`resolve_safe_path`, `is_relative_to`, VCS denial, symlink checks) | Low — tools fail closed. Adversarial tests cover common escapes. |
| Forged evidence snippets that invent code | Evidence verification | Exact-match verification; unverified evidence is flagged | Low–Medium — the threat is still recorded, but the report marks it unverified. |
| Fake LLM provider or man-in-the-middle | LLM client | HTTPS only; operator controls the endpoint | Medium if an operator points at a malicious base URL. |

### Tampering

| Threat | Component | Existing Controls | Residual Risk |
|--------|-----------|-------------------|---------------|
| Modification of reference cards or control catalogue to inject false mappings | Controls / prompts | Generated from `catalog.toml`; tests fail on drift; regeneration scripts | Low |
| Alteration of intermediate run files between tool calls | Persistence | Local filesystem under operator control; redaction of paths/keys | Low |
| Symlink attacks that redirect reads outside the sandbox | Tools | `resolve()` + sandbox check on every path | Low |

### Repudiation

| Threat | Component | Existing Controls | Residual Risk |
|--------|-----------|-------------------|---------------|
| Operator denies having run an analysis that leaked data | Logging | Token accounting, run manifests (redacted), local reports | Medium — no central audit trail unless the operator adds one. |

### Information Disclosure

| Threat | Component | Existing Controls | Residual Risk |
|--------|-----------|-------------------|---------------|
| Agent reads `.git/config` or credentials embedded in a clone | Tools | Explicit VCS metadata denial (case-insensitive) | Low |
| Prompts or code snippets sent to the LLM provider | LLM client | Operator choice of provider; documented in SECURITY.md | Medium–High (inherent to cloud LLM use) |
| Report leakage via shared web UI | Web UI | No server-side persistence by default; reports stay local | Medium if the UI is exposed without auth |
| Path leakage in shareable manifests | Persistence | Path redaction | Low |

### Denial of Service

| Threat | Component | Existing Controls | Residual Risk |
|--------|-----------|-------------------|---------------|
| ReDoS via malicious grep pattern | `grep_content` | Pattern length cap + nested-quantifier heuristic | Low |
| Enormous files or directory trees | Tools | File size caps, directory entry caps, budget limits | Low |
| LLM provider rate limits or timeouts | LLM client | Retries with backoff; configurable timeouts | Medium |

### Elevation of Privilege

| Threat | Component | Existing Controls | Residual Risk |
|--------|-----------|-------------------|---------------|
| Agent escapes sandbox and reads host secrets | Tools | Sandbox + VCS denial | Low |
| Web UI container breakout | Docker | Non-root user, capability drop, `no-new-privileges` | Low (still requires host hardening) |
| Prompt injection that causes the model to recommend dangerous mitigations | Synthesis | Control catalogue constrains IDs; human review expected | Medium |

## Recommended Operational Controls

- **Untrusted codebase mode** (recommended for any analysis of third-party or unreviewed code):
  - Run the CLI as a non-privileged user.
  - Prefer offline / air-gapped LLM endpoints when possible.
  - Review the generated plan before approving subsystem analysis.
  - Treat all evidence marked unverified as suspect.
- **Web UI**:
  - Never expose the Streamlit process directly. Place an identity-aware proxy (OIDC + phishing-resistant MFA) in front of it.
  - Enforce TLS 1.3 and an egress allow-list limited to the chosen LLM provider.
  - Inject API keys at runtime from a secrets manager; never bake them into the image.
- **CI**:
  - The existing security workflow (Bandit, pip-audit, Gitleaks, CodeQL) should remain required.
  - Do not grant the agent a checkout token that has write or package-publish scopes.

## Residual Risks That Cannot Be Eliminated

- The model can still produce incorrect, incomplete, or hallucinated threats. Evidence verification reduces but does not eliminate this.
- Any data sent to a third-party LLM provider leaves the operator’s control.
- A sufficiently sophisticated prompt injection combined with a bug in the tool layer could still cause unexpected behaviour. The adversarial test suite is intended to catch regressions in the known classes of attack.

## Related Documents

- [Architecture](architecture.md) — component diagram and trust boundaries
- [Deployment hardening](deployment-hardening.md) — reference architecture for a shared web UI
- [AGENTS.md](../AGENTS.md) — contributor rules and progressive disclosure
- [SECURITY.md](../SECURITY.md) — vulnerability reporting and best practices
