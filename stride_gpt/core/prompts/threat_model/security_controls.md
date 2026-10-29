---
# Generated from stride_gpt/core/controls/catalog.toml by
# scripts/build_control_catalog.py. Edit the catalogue, not this file.
name: security_controls
title: Security Control Catalogue (identity, data protection, network, logging, application security)
when_to_load: |
  Load for almost any subsystem with a traditional software or
  infrastructure surface (authentication, authorisation, data storage,
  network exposure, logging, input handling, dependencies) to tag each
  threat with the catalogue controls that mitigate it. Adds CONTROLS.
  Framework references (AIUC-1, ISO/IEC 42001, ISO/IEC 27001, EU AI Act) are
  derived from the control IDs automatically.
adds_fields:
  - CONTROLS
stride_letters: [S, T, R, I, D, E]
source: https://github.com/mrwadams/stride-gpt/blob/master/docs/controls-catalog.md
version: 2026.10
---

# Security Control Catalogue (identity, data protection, network, logging, application security) — Reference Card

You loaded this card to tag each threat with the controls that would mitigate it. It covers identity and access management, data protection and cryptography, network security, logging and monitoring, and application security.

## How to use this card

- For each threat, choose **1-4** control IDs that would most directly prevent, detect or contain it, most important first.
- Prefer the most specific control. A threat about a *missing* control cites that control.
- **Anti-hallucination requirement.** Use only IDs listed in the control cards you loaded, exactly as written. Never invent an ID; if nothing fits, leave the field out rather than guess.
- Do not cite framework clauses yourself. STRIDE-GPT looks up the AIUC-1, ISO/IEC 42001, ISO/IEC 27001 and EU AI Act references for the IDs you choose.
- IDs from `ai_controls` are equally valid; a threat can combine IDs from both cards.

## Schema additions

Each threat must additionally include:
- `"CONTROLS"`: an array of control IDs, e.g. `["IAM-05", "LOG-01"]`. When reporting through `report_threat`, pass them as the `controls` argument.

## Control catalogue

### IAM — Identity & Access Management

- `IAM-01` **Centralised authentication with OpenID Connect.** Authenticate users through a central identity provider using OIDC Authorization Code with PKCE instead of application-local credentials. (S, R)
- `IAM-02` **Phishing-resistant multi-factor authentication.** Require phishing-resistant MFA (FIDO2/WebAuthn passkeys or X.509 smart cards) for all users, and always for privileged and administrative access. (S, E)
- `IAM-03` **X.509 PKI and certificate lifecycle management.** Issue, validate, rotate and revoke X.509 certificates from a managed PKI, with full chain and revocation validation on every relying party. (S, T)
- `IAM-04` **Cryptographic workload identity (SPIFFE/SPIRE).** Give every service and workload a short-lived, attested cryptographic identity, such as an X.509 SVID, and authorise on that identity rather than on network location or static secrets. (S, T, E)
- `IAM-05` **Secure JWT issuance and validation.** Validate every JWT strictly — allow-listed algorithms, pinned issuer keys, and iss/aud/exp/nbf/typ checks — and keep tokens short-lived and free of secrets. (S, T, E, I)
- `IAM-06` **OAuth 2.x authorisation with least-privilege, sender-constrained tokens.** Delegate access with OAuth 2.x following RFC 9700: narrowly scoped, audience-restricted, sender-constrained tokens and token exchange instead of token forwarding. (S, E, I)
- `IAM-07` **Deny-by-default, object-level authorisation.** Enforce authorisation server-side on every request at function and object level, deny by default, and never trust client-supplied roles or identifiers. (E, I, T)
- `IAM-08` **Privileged access management and just-in-time elevation.** Remove standing administrative privilege: grant time-bound, approved, recorded elevation and review privileged access regularly. (E, R)
- `IAM-09` **Secure session management.** Protect sessions with server-side revocation, hardened cookies, ID rotation on login, idle and absolute timeouts, and CSRF defences. (S, E)
- `IAM-10` **Non-human identity and API key governance.** Inventory every service account and API key with an owner and purpose, prefer federated short-lived credentials, and rotate or revoke the rest automatically. (S, E)

### DAT — Data Protection & Cryptography

- `DAT-01` **Data classification, minimisation and retention.** Classify data, collect and keep only what the purpose needs, and enforce retention and deletion — including for prompts, outputs and AI training data. (I)
- `DAT-02` **Encryption at rest with customer-managed keys (CMEK).** Encrypt every persistent store — databases, object storage, vector stores, backups, logs and model artefacts — with envelope encryption under keys the organisation controls in a KMS or HSM. (I, T)
- `DAT-03` **Key management and HSM-backed key custody.** Generate and hold keys in FIPS 140-3 validated HSMs or cloud KMS, with separation of duties, defined lifecycles, and monitoring of key use. (I, T, E)
- `DAT-04` **Encryption in transit with TLS 1.3.** Encrypt every network hop, internal and external, with TLS 1.3 (TLS 1.2 minimum with AEAD suites) and validate certificates and hostnames on every client. (I, T, S)
- `DAT-05` **Mutual TLS for service-to-service and partner connections.** Require mutual TLS on internal APIs, LLM gateways, MCP servers and partner integrations, and authorise on the peer certificate's identity. (S, T, I)
- `DAT-06` **Secrets management.** Keep secrets in a secrets manager, out of code, images, CI logs, prompts and agent-readable configuration, with short lifetimes, scoped access and automated rotation. (I, S, E)
- `DAT-07` **Sensitive-data redaction and data loss prevention.** Detect and redact personal data and secrets before they reach prompts, embeddings, logs, traces or third-party model APIs, and filter outputs and egress for leakage. (I)
- `DAT-08` **Tenant data isolation.** Enforce tenant boundaries on every data path — queries, caches, vector-store namespaces, conversation memory and encryption keys — and test them. (I, E)
- `DAT-09` **Backup, integrity and recovery of data and AI artefacts.** Keep immutable, encrypted, tested backups of data and AI artefacts — model weights, prompts, configurations, vector indexes and agent memory — with integrity checks. (D, T)

### NET — Network Security

- `NET-01` **Network segmentation and zero-trust micro-segmentation.** Segment by trust zone (edge, application, data, management, model inference, agent sandbox) with default-deny, identity-aware east-west policy. (E, I, T)
- `NET-02` **Egress control and destination allow-listing.** Deny outbound traffic by default and allow-list destinations, such as model APIs and package mirrors, through an egress proxy; block cloud metadata endpoints from workloads that don't need them. (I, E)
- `NET-03` **MACsec (IEEE 802.1AE) link-layer encryption.** Encrypt and integrity-protect Ethernet links that carry sensitive traffic (data-centre interconnects, colocation cross-connects, GPU cluster fabrics) with MACsec and managed MKA keys. (I, T)
- `NET-04` **IPsec (IKEv2) for site-to-site and hybrid connectivity.** Protect site-to-site, branch and hybrid-cloud links with IKEv2 IPsec using certificate authentication, modern AEAD suites and perfect forward secrecy. (I, T, S)
- `NET-05` **Private connectivity to model providers and data services.** Reach model APIs, vector stores and data services through private endpoints or a controlled AI gateway rather than the public internet, and disable public access where possible. (I, T, S)
- `NET-06` **Edge protection: API gateway, WAF and DDoS mitigation.** Front internet-facing applications and model endpoints with an API gateway, WAF and managed DDoS protection that enforce schemas, rate limits and bot controls. (D, T)

### LOG — Logging, Monitoring & Response

- `LOG-01` **Structured, attributable security event logging.** Log authentication, authorisation, administrative, data-access, configuration and key-usage events as structured, correlated records — without logging secrets or raw personal data. (R)
- `LOG-02` **Tamper-evident log storage and retention.** Ship logs off-host in near real time to append-only, access-controlled storage the logged system cannot alter, and retain them as law and investigations require. (R, T)
- `LOG-03` **Centralised detection and alerting.** Correlate security telemetry in a SIEM with detections mapped to MITRE ATT&CK and ATLAS, and route actionable alerts to an on-call responder. (R, D, E, I)
- `LOG-04` **Security incident response and forensic readiness.** Maintain and exercise an incident response plan, with AI-specific playbooks, evidence preservation and regulatory notification paths. (R, D)
- `LOG-05` **Service health, capacity and cost-anomaly monitoring.** Monitor availability, capacity, provider rate limits and AI token spend against budgets, alerting on anomalies such as denial-of-wallet. (D)

### APP — Application Security

- `APP-01` **Secure SDLC with threat modelling and security requirements.** Threat-model at design time and on significant change, derive security requirements from OWASP ASVS, and gate releases on unresolved high risks. (S, T, R, I, D, E)
- `APP-02` **Input validation and injection prevention.** Validate all untrusted input server-side against allow-lists and schemas and use parameterised interfaces, never building queries or commands from strings. (T, E, I)
- `APP-03` **Context-aware output encoding and content security policy.** Encode output for its sink (HTML, JavaScript, URL, CSV, Markdown), treat model output as untrusted, and enforce a strict Content-Security-Policy. (T, I, E)
- `APP-04` **Software supply-chain security (SBOM, signing, provenance).** Lock and verify dependencies, generate SBOMs and AI-BOMs, sign and verify build artefacts with provenance, and harden the CI/CD pipeline. (T, E)
- `APP-05` **Automated security testing in CI/CD.** Run SAST, dependency, secret, IaC and container scanning on every change and DAST before release, with severity-based gates and fix SLAs. (T, E, I)
- `APP-06` **Secure configuration and hardening.** Deploy from hardened, code-defined baselines — non-root, minimal containers, restricted pod security, no debug endpoints or default credentials — with drift detection. (E, I, T)
- `APP-07` **Robust error handling and fail-safe behaviour.** Fail closed on security errors, return generic error messages, and handle dependency failures (including model-provider outages and tool errors) explicitly. (D, I, E)
- `APP-08` **Rate limits, quotas and resource-exhaustion protection.** Bound resource use per user, tenant and key — request rates, concurrency, payload sizes, timeouts, and for model features input/output token and spend budgets. (D)
- `APP-09` **Secure file upload and document ingestion.** Accept files by content-verified type and size, scan and parse them in isolated workers with hardened parsers, and screen RAG ingestion for hidden instructions. (T, E, D)
- `APP-10` **SSRF-safe outbound requests.** Allow-list the destinations of any server-side fetch — webhooks, URL previews, RAG web loaders, agent browsing tools — and block private, link-local and metadata addresses after resolution. (I, E)
