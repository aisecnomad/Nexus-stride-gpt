<!-- Generated from stride_gpt/core/controls/catalog.toml by scripts/build_control_catalog.py. Edit the catalogue, not this file. -->

# Control Catalogue

Catalogue version **2026.10** · 69 controls in 8 domains · mapped to AIUC-1, ISO/IEC 42001, EU AI Act, ISO/IEC 27001.

STRIDE-GPT tags each threat with the IDs of the controls that would mitigate it, and looks up the framework references below from those IDs. See [Controls and compliance mapping](controls-and-compliance.md) for how the mapping works and its limits, and [Framework crosswalks](framework-crosswalks.md) for the same data organised by framework.

## Domains

| Domain | Controls | Reference card | Scope |
|--------|----------|----------------|-------|
| [IAM — Identity & Access Management](#domain-iam) | 10 | `security_controls` | Authentication of people and workloads (OIDC, MFA, X.509, JWT) and authorisation (OAuth 2.x, object-level access control, privileged access). |
| [DAT — Data Protection & Cryptography](#domain-dat) | 9 | `security_controls` | Encryption at rest with customer-managed keys, encryption in transit (TLS, mTLS), key and secrets management, data minimisation, isolation and leakage prevention. |
| [NET — Network Security](#domain-net) | 6 | `security_controls` | Segmentation, egress control, link and site-to-site encryption (MACsec, IPsec), private connectivity and edge protection. |
| [LOG — Logging, Monitoring & Response](#domain-log) | 5 | `security_controls` | Security event logging, tamper-evident retention, detection and alerting, capacity and cost monitoring, and incident response. |
| [APP — Application Security](#domain-app) | 10 | `security_controls` | Secure SDLC and the OWASP Top 10:2025 and ASVS 5.0 control families: injection, output encoding, supply chain, testing, configuration, error handling and resource limits. |
| [AI — AI & LLM Application Security](#domain-ai) | 9 | `ai_controls` | Controls specific to language-model features: prompt injection, output handling, prompt hygiene, RAG access control, data and model provenance, red teaming, output guardrails and transparency. |
| [AGT — Agentic AI](#domain-agt) | 14 | `ai_controls` | Controls for agents that act: inventory and ownership, least agency, agent identity and delegated credentials, tool governance, human approval, sandboxing, memory integrity, inter-agent trust, audit, monitoring, kill switch and execution budgets. |
| [GOV — AI Governance](#domain-gov) | 6 | `ai_controls` | Organisational controls the AI frameworks require: policy and accountability, risk and impact assessment, documentation and change control, supplier due diligence, incident management and post-deployment monitoring. |

<a id="domain-iam"></a>

## IAM — Identity & Access Management

Authentication of people and workloads (OIDC, MFA, X.509, JWT) and authorisation (OAuth 2.x, object-level access control, privileged access).

| ID | Control | STRIDE |
|----|---------|--------|
| [IAM-01](#iam-01) | Centralised authentication with OpenID Connect | S, R |
| [IAM-02](#iam-02) | Phishing-resistant multi-factor authentication | S, E |
| [IAM-03](#iam-03) | X.509 PKI and certificate lifecycle management | S, T |
| [IAM-04](#iam-04) | Cryptographic workload identity (SPIFFE/SPIRE) | S, T, E |
| [IAM-05](#iam-05) | Secure JWT issuance and validation | S, T, E, I |
| [IAM-06](#iam-06) | OAuth 2.x authorisation with least-privilege, sender-constrained tokens | S, E, I |
| [IAM-07](#iam-07) | Deny-by-default, object-level authorisation | E, I, T |
| [IAM-08](#iam-08) | Privileged access management and just-in-time elevation | E, R |
| [IAM-09](#iam-09) | Secure session management | S, E |
| [IAM-10](#iam-10) | Non-human identity and API key governance | S, E |

<a id="iam-01"></a>

### IAM-01 · Centralised authentication with OpenID Connect

**Objective.** Authenticate users through a central identity provider using OIDC Authorization Code with PKCE instead of application-local credentials.

**Guidance**

- Use the OIDC Authorization Code flow with PKCE (RFC 7636) for every client, including confidential ones; do not use the Implicit or Resource Owner Password Credentials grants (RFC 9700).
- Validate ID tokens fully: signature, iss, aud, exp, iat and nonce, per OpenID Connect Core.
- Keep no application-local password store; provision and deprovision accounts from the IdP (e.g. SCIM) so leavers lose access everywhere at once.
- Bound session lifetime and require re-authentication for sensitive operations.

| | |
|---|---|
| STRIDE | Spoofing, Repudiation |
| Mitigates | A07:2025 Authentication Failures |
| AIUC-1 | B007 — Enforce user access privileges to AI systems |
| ISO/IEC 42001 | — |
| EU AI Act | Art. 15(5) — Cybersecurity: resilience against unauthorised attempts to alter use, outputs or performance, including data and model poisoning, adversarial examples and confidentiality attacks |
| ISO/IEC 27001 | A.5.16 — Identity management<br>A.5.17 — Authentication information<br>A.8.5 — Secure authentication |
| Sources | OpenID Connect Core 1.0; RFC 7636 (PKCE); RFC 9700 (OAuth 2.0 Security BCP); OWASP ASVS 5.0 V6, V10 |

<a id="iam-02"></a>

### IAM-02 · Phishing-resistant multi-factor authentication

**Objective.** Require phishing-resistant MFA (FIDO2/WebAuthn passkeys or X.509 smart cards) for all users, and always for privileged and administrative access.

**Guidance**

- Use FIDO2/WebAuthn passkeys or certificate-based authentication (PIV/CAC smart cards); do not accept SMS or voice OTP for privileged access.
- Target NIST SP 800-63B-4 AAL2 for users and AAL3 for administrators.
- Apply step-up authentication before high-risk operations such as changing payment details, exporting data or approving agent actions.
- Rate-limit and alert on repeated authentication failures and MFA fatigue patterns.

| | |
|---|---|
| STRIDE | Spoofing, Elevation of Privilege |
| Mitigates | A07:2025 Authentication Failures |
| AIUC-1 | B007 — Enforce user access privileges to AI systems |
| ISO/IEC 42001 | — |
| EU AI Act | Art. 15(5) — Cybersecurity: resilience against unauthorised attempts to alter use, outputs or performance, including data and model poisoning, adversarial examples and confidentiality attacks |
| ISO/IEC 27001 | A.5.17 — Authentication information<br>A.8.5 — Secure authentication |
| Sources | NIST SP 800-63B-4; W3C Web Authentication (WebAuthn); OWASP ASVS 5.0 V6 |

<a id="iam-03"></a>

### IAM-03 · X.509 PKI and certificate lifecycle management

**Objective.** Issue, validate, rotate and revoke X.509 certificates from a managed PKI, with full chain and revocation validation on every relying party.

**Guidance**

- Run a private CA with an offline, HSM-protected root; issue short-lived certificates automatically (ACME, RFC 8555, or SPIRE for workloads).
- Validate certificates per RFC 5280 on every relying party: chain to a pinned trust anchor, validity period, key usage and extended key usage, name constraints and hostname.
- Check revocation (OCSP stapling or CRLs) or rely on lifetimes short enough that revocation is unnecessary.
- Keep a certificate inventory with expiry alerting; monitor Certificate Transparency logs for public domains.
- Use P-256/Ed25519 or RSA-3072+ keys and plan crypto-agility for post-quantum algorithms (FIPS 203/204).

| | |
|---|---|
| STRIDE | Spoofing, Tampering |
| Mitigates | A04:2025 Cryptographic Failures; A07:2025 Authentication Failures |
| AIUC-1 | B008 — Protect AI system deployment environment |
| ISO/IEC 42001 | — |
| EU AI Act | Art. 15(5) — Cybersecurity: resilience against unauthorised attempts to alter use, outputs or performance, including data and model poisoning, adversarial examples and confidentiality attacks |
| ISO/IEC 27001 | A.8.5 — Secure authentication<br>A.8.24 — Use of cryptography |
| Sources | RFC 5280; RFC 8555 (ACME); RFC 6960 (OCSP); RFC 6962 (Certificate Transparency); NIST SP 800-57 Part 1; FIPS 203, FIPS 204 |

<a id="iam-04"></a>

### IAM-04 · Cryptographic workload identity (SPIFFE/SPIRE)

**Objective.** Give every service and workload a short-lived, attested cryptographic identity, such as an X.509 SVID, and authorise on that identity rather than on network location or static secrets.

**Guidance**

- Issue SPIFFE IDs as X.509-SVIDs through SPIRE with node and workload attestation, rotated automatically (typically hourly).
- Authorise service-to-service calls on the peer's SPIFFE ID, not its IP address or subnet.
- Replace long-lived cloud keys with workload identity federation (OIDC federation for CI/CD and cross-cloud access).
- Pair with DAT-05 so every hop is mutually authenticated.

| | |
|---|---|
| STRIDE | Spoofing, Tampering, Elevation of Privilege |
| Mitigates | A07:2025 Authentication Failures |
| AIUC-1 | B008 — Protect AI system deployment environment |
| ISO/IEC 42001 | — |
| EU AI Act | Art. 15(5) — Cybersecurity: resilience against unauthorised attempts to alter use, outputs or performance, including data and model poisoning, adversarial examples and confidentiality attacks |
| ISO/IEC 27001 | A.5.16 — Identity management<br>A.8.5 — Secure authentication |
| Sources | SPIFFE specification; NIST SP 800-207 (Zero Trust Architecture) |

<a id="iam-05"></a>

### IAM-05 · Secure JWT issuance and validation

**Objective.** Validate every JWT strictly — allow-listed algorithms, pinned issuer keys, and iss/aud/exp/nbf/typ checks — and keep tokens short-lived and free of secrets.

**Guidance**

- Allow-list algorithms (e.g. ES256, EdDSA, RS256); reject alg=none and prevent HMAC/RSA key confusion by binding each key to one algorithm.
- Fetch keys only from the issuer's pinned JWKS endpoint; never trust jku, x5u or embedded jwk headers from the token.
- Validate iss, aud, exp, nbf and iat, and use explicit typing (typ, e.g. at+jwt per RFC 9068) so one token type cannot be replayed as another.
- Keep access tokens short-lived (minutes) and have a revocation strategy for refresh tokens and sessions.
- Never put secrets or unnecessary personal data in JWT claims — signing is not encryption; use JWE where confidentiality is needed.
- Rotate signing keys with kid and use separate keys per environment.

| | |
|---|---|
| STRIDE | Spoofing, Tampering, Elevation of Privilege, Information Disclosure |
| Mitigates | A04:2025 Cryptographic Failures; A07:2025 Authentication Failures; A08:2025 Software or Data Integrity Failures |
| AIUC-1 | B007 — Enforce user access privileges to AI systems |
| ISO/IEC 42001 | — |
| EU AI Act | Art. 15(5) — Cybersecurity: resilience against unauthorised attempts to alter use, outputs or performance, including data and model poisoning, adversarial examples and confidentiality attacks |
| ISO/IEC 27001 | A.8.5 — Secure authentication<br>A.8.24 — Use of cryptography |
| Sources | RFC 7519 (JWT); RFC 8725 (JWT Best Current Practices); RFC 9068 (JWT access tokens); OWASP ASVS 5.0 V9; OWASP JSON Web Token Cheat Sheet |

<a id="iam-06"></a>

### IAM-06 · OAuth 2.x authorisation with least-privilege, sender-constrained tokens

**Objective.** Delegate access with OAuth 2.x following RFC 9700: narrowly scoped, audience-restricted, sender-constrained tokens and token exchange instead of token forwarding.

**Guidance**

- Use Authorization Code with PKCE and exact redirect-URI matching; disable the Implicit and ROPC grants (RFC 9700).
- Scope tokens to the minimum and restrict their audience with resource indicators (RFC 8707).
- Sender-constrain tokens with DPoP (RFC 9449) or mutual-TLS certificate binding (RFC 8705) so stolen tokens cannot be replayed.
- Use Rich Authorization Requests (RFC 9396) for transaction-specific grants such as a single payment.
- Rotate refresh tokens and detect reuse; use token exchange (RFC 8693) for downstream delegation rather than forwarding user tokens.

| | |
|---|---|
| STRIDE | Spoofing, Elevation of Privilege, Information Disclosure |
| Mitigates | A01:2025 Broken Access Control; A07:2025 Authentication Failures |
| AIUC-1 | B007 — Enforce user access privileges to AI systems |
| ISO/IEC 42001 | — |
| EU AI Act | Art. 15(5) — Cybersecurity: resilience against unauthorised attempts to alter use, outputs or performance, including data and model poisoning, adversarial examples and confidentiality attacks |
| ISO/IEC 27001 | A.5.15 — Access control<br>A.5.18 — Access rights<br>A.8.5 — Secure authentication |
| Sources | RFC 6749; RFC 9700 (OAuth 2.0 Security BCP); RFC 8707; RFC 9449 (DPoP); RFC 8705; RFC 9396; RFC 8693; OWASP ASVS 5.0 V10 |

<a id="iam-07"></a>

### IAM-07 · Deny-by-default, object-level authorisation

**Objective.** Enforce authorisation server-side on every request at function and object level, deny by default, and never trust client-supplied roles or identifiers.

**Guidance**

- Check authorisation for every function and every object accessed, server-side, to prevent IDOR/BOLA (OWASP API1:2023) and function-level bypass (API5:2023).
- Centralise policy in a tested policy engine or library (e.g. OPA/Rego, Cedar, or relationship-based access control) rather than ad hoc checks in handlers.
- Deny by default; re-check authorisation on state-changing operations and include the tenant in every data-access predicate.
- Treat roles, tenant IDs and object IDs sent by the client as untrusted input.

| | |
|---|---|
| STRIDE | Elevation of Privilege, Information Disclosure, Tampering |
| Mitigates | A01:2025 Broken Access Control |
| AIUC-1 | B007 — Enforce user access privileges to AI systems |
| ISO/IEC 42001 | — |
| EU AI Act | Art. 15(5) — Cybersecurity: resilience against unauthorised attempts to alter use, outputs or performance, including data and model poisoning, adversarial examples and confidentiality attacks |
| ISO/IEC 27001 | A.5.15 — Access control<br>A.8.3 — Information access restriction |
| Sources | OWASP Top 10:2025 A01; OWASP API Security Top 10 2023 (API1, API5); OWASP ASVS 5.0 V8; OWASP Authorization Cheat Sheet |

<a id="iam-08"></a>

### IAM-08 · Privileged access management and just-in-time elevation

**Objective.** Remove standing administrative privilege: grant time-bound, approved, recorded elevation and review privileged access regularly.

**Guidance**

- Use separate administrative identities and just-in-time, time-boxed elevation with approval.
- Record privileged sessions and alert on break-glass account use.
- Review privileged and service-account access at least quarterly and on role change.

| | |
|---|---|
| STRIDE | Elevation of Privilege, Repudiation |
| Mitigates | A01:2025 Broken Access Control |
| AIUC-1 | B008 — Protect AI system deployment environment |
| ISO/IEC 42001 | — |
| EU AI Act | Art. 15(5) — Cybersecurity: resilience against unauthorised attempts to alter use, outputs or performance, including data and model poisoning, adversarial examples and confidentiality attacks |
| ISO/IEC 27001 | A.5.18 — Access rights<br>A.8.2 — Privileged access rights |
| Sources | NIST SP 800-207; CIS Controls v8.1 (Control 5, 6) |

<a id="iam-09"></a>

### IAM-09 · Secure session management

**Objective.** Protect sessions with server-side revocation, hardened cookies, ID rotation on login, idle and absolute timeouts, and CSRF defences.

**Guidance**

- Set Secure, HttpOnly and SameSite on session cookies; rotate the session ID on login and privilege change.
- Enforce idle and absolute timeouts and support server-side revocation (logout everywhere).
- Use anti-CSRF tokens or SameSite=Strict for cookie-authenticated state-changing requests.

| | |
|---|---|
| STRIDE | Spoofing, Elevation of Privilege |
| Mitigates | A07:2025 Authentication Failures |
| AIUC-1 | — |
| ISO/IEC 42001 | — |
| EU AI Act | Art. 15(5) — Cybersecurity: resilience against unauthorised attempts to alter use, outputs or performance, including data and model poisoning, adversarial examples and confidentiality attacks |
| ISO/IEC 27001 | A.8.5 — Secure authentication |
| Sources | OWASP ASVS 5.0 V7; OWASP Session Management Cheat Sheet |

<a id="iam-10"></a>

### IAM-10 · Non-human identity and API key governance

**Objective.** Inventory every service account and API key with an owner and purpose, prefer federated short-lived credentials, and rotate or revoke the rest automatically.

**Guidance**

- Keep an inventory of non-human identities with owner, purpose, scopes and last use; disable unused ones.
- Prefer federated, short-lived credentials over static API keys; scope any remaining keys to one purpose and least privilege.
- Rotate keys automatically and revoke them when the owner leaves or the integration is retired.

| | |
|---|---|
| STRIDE | Spoofing, Elevation of Privilege |
| AIUC-1 | — |
| ISO/IEC 42001 | — |
| EU AI Act | Art. 15(5) — Cybersecurity: resilience against unauthorised attempts to alter use, outputs or performance, including data and model poisoning, adversarial examples and confidentiality attacks |
| ISO/IEC 27001 | A.5.16 — Identity management<br>A.5.17 — Authentication information<br>A.5.18 — Access rights |
| Sources | NIST SP 800-207; OWASP Non-Human Identities Top 10 (2025) |

<a id="domain-dat"></a>

## DAT — Data Protection & Cryptography

Encryption at rest with customer-managed keys, encryption in transit (TLS, mTLS), key and secrets management, data minimisation, isolation and leakage prevention.

| ID | Control | STRIDE |
|----|---------|--------|
| [DAT-01](#dat-01) | Data classification, minimisation and retention | I |
| [DAT-02](#dat-02) | Encryption at rest with customer-managed keys (CMEK) | I, T |
| [DAT-03](#dat-03) | Key management and HSM-backed key custody | I, T, E |
| [DAT-04](#dat-04) | Encryption in transit with TLS 1.3 | I, T, S |
| [DAT-05](#dat-05) | Mutual TLS for service-to-service and partner connections | S, T, I |
| [DAT-06](#dat-06) | Secrets management | I, S, E |
| [DAT-07](#dat-07) | Sensitive-data redaction and data loss prevention | I |
| [DAT-08](#dat-08) | Tenant data isolation | I, E |
| [DAT-09](#dat-09) | Backup, integrity and recovery of data and AI artefacts | D, T |

<a id="dat-01"></a>

### DAT-01 · Data classification, minimisation and retention

**Objective.** Classify data, collect and keep only what the purpose needs, and enforce retention and deletion — including for prompts, outputs and AI training data.

**Guidance**

- Classify data (e.g. public, internal, confidential, restricted) and tag stores holding PII, payment or health data.
- Collect the minimum, define retention per class, and delete on schedule, covering backups, logs, embeddings and conversation history.
- Write down what data may enter prompts, logs and model training, and how customer data is used (input and output data policies).

| | |
|---|---|
| STRIDE | Information Disclosure |
| Mitigates | LLM02 Sensitive Information Disclosure |
| AIUC-1 | A001 — Establish input data policy<br>A002 — Establish output data policy |
| ISO/IEC 42001 | — |
| EU AI Act | — |
| ISO/IEC 27001 | A.5.12 — Classification of information<br>A.5.34 — Privacy and protection of PII<br>A.8.10 — Information deletion |
| Sources | ISO/IEC 27002:2022 5.12; GDPR Art. 5(1)(c) and (e) |

<a id="dat-02"></a>

### DAT-02 · Encryption at rest with customer-managed keys (CMEK)

**Objective.** Encrypt every persistent store — databases, object storage, vector stores, backups, logs and model artefacts — with envelope encryption under keys the organisation controls in a KMS or HSM.

**Guidance**

- Use envelope encryption: data keys wrapped by a customer-managed key in a KMS (AWS KMS customer managed keys, Google Cloud CMEK with Cloud KMS/HSM/EKM, Azure Key Vault or Managed HSM).
- Separate keys per environment, tenant and data class; restrict Decrypt to the workload identity that needs it, independent of storage administrators.
- Enable automatic rotation and audit every key-usage event in cloud audit logs.
- Cover AI-specific stores too: vector indexes, embedding caches, fine-tuning datasets, model weights and prompt/response logs.
- Support crypto-shredding: destroying a tenant's key makes its data unrecoverable.
- Use AES-256-GCM in FIPS 140-3 validated modules.

| | |
|---|---|
| STRIDE | Information Disclosure, Tampering |
| Mitigates | A04:2025 Cryptographic Failures |
| AIUC-1 | A004 — Protect IP & trade secrets<br>E005 — Document data storage security |
| ISO/IEC 42001 | — |
| EU AI Act | Art. 15(5) — Cybersecurity: resilience against unauthorised attempts to alter use, outputs or performance, including data and model poisoning, adversarial examples and confidentiality attacks |
| ISO/IEC 27001 | A.8.24 — Use of cryptography |
| Sources | NIST SP 800-57 Part 1 Rev. 5; FIPS 140-3; OWASP Cryptographic Storage Cheat Sheet; OWASP ASVS 5.0 V11 |

<a id="dat-03"></a>

### DAT-03 · Key management and HSM-backed key custody

**Objective.** Generate and hold keys in FIPS 140-3 validated HSMs or cloud KMS, with separation of duties, defined lifecycles, and monitoring of key use.

**Guidance**

- Generate and store keys in FIPS 140-3 Level 3 HSMs or cloud KMS/HSM; never export plaintext key material.
- Separate key custodians from data administrators and require dual control for root and master keys.
- Define the key lifecycle (generation, rotation, revocation, destruction) per NIST SP 800-57; use BYOK, HYOK or external key managers where sovereignty requires.
- Alert on anomalous key use (unexpected principals, volumes or regions).
- Keep a cryptographic bill of materials (CBOM) to plan post-quantum migration.

| | |
|---|---|
| STRIDE | Information Disclosure, Tampering, Elevation of Privilege |
| Mitigates | A04:2025 Cryptographic Failures |
| AIUC-1 | E005 — Document data storage security |
| ISO/IEC 42001 | — |
| EU AI Act | Art. 15(5) — Cybersecurity: resilience against unauthorised attempts to alter use, outputs or performance, including data and model poisoning, adversarial examples and confidentiality attacks |
| ISO/IEC 27001 | A.8.24 — Use of cryptography |
| Sources | NIST SP 800-57 Part 1 Rev. 5; FIPS 140-3; CycloneDX 1.6 (CBOM) |

<a id="dat-04"></a>

### DAT-04 · Encryption in transit with TLS 1.3

**Objective.** Encrypt every network hop, internal and external, with TLS 1.3 (TLS 1.2 minimum with AEAD suites) and validate certificates and hostnames on every client.

**Guidance**

- Prefer TLS 1.3; allow TLS 1.2 only with ECDHE and AEAD suites (AES-GCM, ChaCha20-Poly1305); disable TLS 1.0/1.1 (RFC 8996), static RSA key exchange and CBC suites.
- Validate certificates and hostnames in every client and SDK — no verify=False or custom trust-all managers.
- Encrypt internal hops as well: databases, caches, message buses, vector stores and LLM gateways.
- Send HSTS for web origins and automate certificate renewal.
- Enable hybrid post-quantum key exchange (e.g. X25519MLKEM768) where supported, for long-lived confidentiality.

| | |
|---|---|
| STRIDE | Information Disclosure, Tampering, Spoofing |
| Mitigates | A04:2025 Cryptographic Failures |
| AIUC-1 | — |
| ISO/IEC 42001 | — |
| EU AI Act | Art. 15(5) — Cybersecurity: resilience against unauthorised attempts to alter use, outputs or performance, including data and model poisoning, adversarial examples and confidentiality attacks |
| ISO/IEC 27001 | A.5.14 — Information transfer<br>A.8.24 — Use of cryptography |
| Sources | RFC 8446 (TLS 1.3); RFC 9325 (BCP 195); RFC 8996; RFC 6797 (HSTS); NIST SP 800-52 Rev. 2; OWASP ASVS 5.0 V12 |

<a id="dat-05"></a>

### DAT-05 · Mutual TLS for service-to-service and partner connections

**Objective.** Require mutual TLS on internal APIs, LLM gateways, MCP servers and partner integrations, and authorise on the peer certificate's identity.

**Guidance**

- Require client certificates on internal APIs, model gateways, MCP servers and B2B integrations; terminate mTLS at the service or sidecar (service mesh in STRICT mode).
- Authorise on the certificate identity (SAN or SPIFFE ID) rather than accepting any certificate from the CA.
- Pin the issuing CA per trust domain and keep client certificates short-lived.
- When OAuth is also in use, bind access tokens to the client certificate (RFC 8705).

| | |
|---|---|
| STRIDE | Spoofing, Tampering, Information Disclosure |
| Mitigates | A04:2025 Cryptographic Failures; A07:2025 Authentication Failures |
| AIUC-1 | B008 — Protect AI system deployment environment |
| ISO/IEC 42001 | — |
| EU AI Act | Art. 15(5) — Cybersecurity: resilience against unauthorised attempts to alter use, outputs or performance, including data and model poisoning, adversarial examples and confidentiality attacks |
| ISO/IEC 27001 | A.5.14 — Information transfer<br>A.8.20 — Networks security<br>A.8.24 — Use of cryptography |
| Sources | RFC 8446; RFC 8705; NIST SP 800-207; NIST SP 800-204 |

<a id="dat-06"></a>

### DAT-06 · Secrets management

**Objective.** Keep secrets in a secrets manager, out of code, images, CI logs, prompts and agent-readable configuration, with short lifetimes, scoped access and automated rotation.

**Guidance**

- Store secrets in a secrets manager (e.g. HashiCorp Vault, AWS Secrets Manager, Google Secret Manager, Azure Key Vault) and inject them at runtime.
- Never place secrets in source code, container images, CI logs, prompts, tool descriptions or files an agent can read.
- Prefer dynamic, short-lived credentials; rotate immediately on suspected exposure.
- Scan commits and CI for secrets with push protection (e.g. Gitleaks, GitHub secret scanning).

| | |
|---|---|
| STRIDE | Information Disclosure, Spoofing, Elevation of Privilege |
| Mitigates | A04:2025 Cryptographic Failures; LLM02 Sensitive Information Disclosure; LLM07 System Prompt Leakage |
| AIUC-1 | A008 — Prevent leakage of credentials and secrets |
| ISO/IEC 42001 | — |
| EU AI Act | Art. 15(5) — Cybersecurity: resilience against unauthorised attempts to alter use, outputs or performance, including data and model poisoning, adversarial examples and confidentiality attacks |
| ISO/IEC 27001 | A.5.17 — Authentication information |
| Sources | OWASP Secrets Management Cheat Sheet; NIST SP 800-57 Part 1 |

<a id="dat-07"></a>

### DAT-07 · Sensitive-data redaction and data loss prevention

**Objective.** Detect and redact personal data and secrets before they reach prompts, embeddings, logs, traces or third-party model APIs, and filter outputs and egress for leakage.

**Guidance**

- Redact or tokenise PII and secrets before data enters prompts, embeddings, logs, traces or external model APIs.
- Filter model outputs and agent egress for sensitive data, and limit response content to what the user is entitled to see.
- Use pseudonymisation where analytics need joins; test detection with seeded canary records.

| | |
|---|---|
| STRIDE | Information Disclosure |
| Mitigates | LLM02 Sensitive Information Disclosure |
| AIUC-1 | A006 — Prevent PII leakage<br>B009 — Limit output over-exposure |
| ISO/IEC 42001 | — |
| EU AI Act | — |
| ISO/IEC 27001 | A.5.34 — Privacy and protection of PII<br>A.8.11 — Data masking<br>A.8.12 — Data leakage prevention |
| Sources | ISO/IEC 27002:2022 8.11, 8.12; NIST AI 600-1 |

<a id="dat-08"></a>

### DAT-08 · Tenant data isolation

**Objective.** Enforce tenant boundaries on every data path — queries, caches, vector-store namespaces, conversation memory and encryption keys — and test them.

**Guidance**

- Scope every query by tenant (row-level security, per-tenant schemas, or per-tenant namespaces and indexes in vector databases).
- Never share caches, conversation memory or retrieval indexes across tenants without partitioning; use per-tenant keys where possible (DAT-02).
- Run cross-tenant access tests in CI.

| | |
|---|---|
| STRIDE | Information Disclosure, Elevation of Privilege |
| Mitigates | A01:2025 Broken Access Control; LLM02 Sensitive Information Disclosure; LLM08 Vector and Embedding Weaknesses; ASI06 Memory and Context Poisoning |
| AIUC-1 | A005 — Prevent cross-customer data exposure |
| ISO/IEC 42001 | — |
| EU AI Act | Art. 15(5) — Cybersecurity: resilience against unauthorised attempts to alter use, outputs or performance, including data and model poisoning, adversarial examples and confidentiality attacks |
| ISO/IEC 27001 | A.8.3 — Information access restriction |
| Sources | OWASP ASVS 5.0 V8; OWASP API Security Top 10 2023 (API1) |

<a id="dat-09"></a>

### DAT-09 · Backup, integrity and recovery of data and AI artefacts

**Objective.** Keep immutable, encrypted, tested backups of data and AI artefacts — model weights, prompts, configurations, vector indexes and agent memory — with integrity checks.

**Guidance**

- Take immutable, versioned, encrypted backups held under separate credentials or accounts.
- Include AI artefacts: model weights and adapters, prompt and tool configurations, vector indexes and agent memory.
- Verify integrity with checksums or signatures and test restores against defined RPO/RTO.

| | |
|---|---|
| STRIDE | Denial of Service, Tampering |
| AIUC-1 | — |
| ISO/IEC 42001 | — |
| EU AI Act | Art. 15(4) — Robustness: resilience to errors, faults and inconsistencies, including backup or fail-safe plans |
| ISO/IEC 27001 | A.5.30 — ICT readiness for business continuity<br>A.8.13 — Information backup |
| Sources | NIST SP 800-34 Rev. 1; ISO/IEC 27002:2022 8.13 |

<a id="domain-net"></a>

## NET — Network Security

Segmentation, egress control, link and site-to-site encryption (MACsec, IPsec), private connectivity and edge protection.

| ID | Control | STRIDE |
|----|---------|--------|
| [NET-01](#net-01) | Network segmentation and zero-trust micro-segmentation | E, I, T |
| [NET-02](#net-02) | Egress control and destination allow-listing | I, E |
| [NET-03](#net-03) | MACsec (IEEE 802.1AE) link-layer encryption | I, T |
| [NET-04](#net-04) | IPsec (IKEv2) for site-to-site and hybrid connectivity | I, T, S |
| [NET-05](#net-05) | Private connectivity to model providers and data services | I, T, S |
| [NET-06](#net-06) | Edge protection: API gateway, WAF and DDoS mitigation | D, T |

<a id="net-01"></a>

### NET-01 · Network segmentation and zero-trust micro-segmentation

**Objective.** Segment by trust zone (edge, application, data, management, model inference, agent sandbox) with default-deny, identity-aware east-west policy.

**Guidance**

- Separate internet edge, application, data, management, model-inference and agent-sandbox zones; isolate the management plane behind privileged access.
- Default-deny east-west traffic with identity-aware policy (e.g. Kubernetes NetworkPolicy/Cilium, cloud security groups).
- Treat network location as non-authoritative: authenticate and authorise every request (NIST SP 800-207).

| | |
|---|---|
| STRIDE | Elevation of Privilege, Information Disclosure, Tampering |
| AIUC-1 | B008 — Protect AI system deployment environment |
| ISO/IEC 42001 | — |
| EU AI Act | Art. 15(5) — Cybersecurity: resilience against unauthorised attempts to alter use, outputs or performance, including data and model poisoning, adversarial examples and confidentiality attacks |
| ISO/IEC 27001 | A.8.20 — Networks security<br>A.8.22 — Segregation of networks |
| Sources | NIST SP 800-207; CISA Zero Trust Maturity Model v2.0 |

<a id="net-02"></a>

### NET-02 · Egress control and destination allow-listing

**Objective.** Deny outbound traffic by default and allow-list destinations, such as model APIs and package mirrors, through an egress proxy; block cloud metadata endpoints from workloads that don't need them.

**Guidance**

- Default-deny outbound; allow-list FQDNs through an egress proxy or firewall and log all egress.
- Block or tightly control access to cloud instance metadata (169.254.169.254); require IMDSv2 on AWS.
- Apply DNS filtering; give agent and code-execution sandboxes the narrowest egress of all.
- Alert on egress to new destinations and on large outbound transfers.

| | |
|---|---|
| STRIDE | Information Disclosure, Elevation of Privilege |
| Mitigates | A01:2025 Broken Access Control; ASI02 Tool Misuse and Exploitation; ASI10 Rogue Agents |
| AIUC-1 | B006 — Prevent unauthorized AI agent actions<br>B008 — Protect AI system deployment environment |
| ISO/IEC 42001 | — |
| EU AI Act | Art. 15(5) — Cybersecurity: resilience against unauthorised attempts to alter use, outputs or performance, including data and model poisoning, adversarial examples and confidentiality attacks |
| ISO/IEC 27001 | A.8.20 — Networks security<br>A.8.23 — Web filtering |
| Sources | NIST SP 800-41 Rev. 1; OWASP SSRF Prevention Cheat Sheet |

<a id="net-03"></a>

### NET-03 · MACsec (IEEE 802.1AE) link-layer encryption

**Objective.** Encrypt and integrity-protect Ethernet links that carry sensitive traffic (data-centre interconnects, colocation cross-connects, GPU cluster fabrics) with MACsec and managed MKA keys.

**Guidance**

- Enable MACsec with GCM-AES-256 (GCM-AES-XPN-256 on high-speed links) on DCI, colocation and dark-fibre links carrying sensitive data such as training data or model weights.
- Manage keys with MKA (IEEE 802.1X), using a protected pre-shared CAK or keys derived from 802.1X/EAP-TLS, and rotate SAKs automatically.
- Use a fail-closed (must-secure) policy so a link cannot silently fall back to cleartext; alert on MKA session loss.
- MACsec protects each hop only; keep TLS/mTLS (DAT-04, DAT-05) for end-to-end protection.

| | |
|---|---|
| STRIDE | Information Disclosure, Tampering |
| AIUC-1 | B008 — Protect AI system deployment environment |
| ISO/IEC 42001 | — |
| EU AI Act | Art. 15(5) — Cybersecurity: resilience against unauthorised attempts to alter use, outputs or performance, including data and model poisoning, adversarial examples and confidentiality attacks |
| ISO/IEC 27001 | A.8.20 — Networks security<br>A.8.24 — Use of cryptography |
| Sources | IEEE 802.1AE-2018 (MACsec); IEEE 802.1X-2020 (MKA) |

<a id="net-04"></a>

### NET-04 · IPsec (IKEv2) for site-to-site and hybrid connectivity

**Objective.** Protect site-to-site, branch and hybrid-cloud links with IKEv2 IPsec using certificate authentication, modern AEAD suites and perfect forward secrecy.

**Guidance**

- Use IKEv2 (RFC 7296) with X.509 certificate authentication instead of pre-shared keys; disable IKEv1.
- Use AES-256-GCM with ECDH groups 19/20/31 and perfect forward secrecy, per RFC 8221 and RFC 8247; add a post-quantum hybrid key exchange (RFC 9370) where supported.
- Prefer private interconnects to cloud providers, with IPsec or MACsec over them for sensitive traffic; monitor tunnel state and rekeying.

| | |
|---|---|
| STRIDE | Information Disclosure, Tampering, Spoofing |
| AIUC-1 | B008 — Protect AI system deployment environment |
| ISO/IEC 42001 | — |
| EU AI Act | Art. 15(5) — Cybersecurity: resilience against unauthorised attempts to alter use, outputs or performance, including data and model poisoning, adversarial examples and confidentiality attacks |
| ISO/IEC 27001 | A.8.20 — Networks security<br>A.8.21 — Security of network services<br>A.8.24 — Use of cryptography |
| Sources | RFC 4301; RFC 7296 (IKEv2); RFC 8221; RFC 8247; RFC 9370; NIST SP 800-77 Rev. 1 |

<a id="net-05"></a>

### NET-05 · Private connectivity to model providers and data services

**Objective.** Reach model APIs, vector stores and data services through private endpoints or a controlled AI gateway rather than the public internet, and disable public access where possible.

**Guidance**

- Use private endpoints (AWS PrivateLink, Azure Private Link, Google Private Service Connect) for managed model and data services; disable their public network access.
- Enforce service perimeters (e.g. VPC Service Controls) around data used by AI workloads.
- Route all model traffic through an AI gateway that enforces authentication, quotas, logging and DLP.

| | |
|---|---|
| STRIDE | Information Disclosure, Tampering, Spoofing |
| Mitigates | LLM02 Sensitive Information Disclosure; LLM10 Unbounded Consumption |
| AIUC-1 | B008 — Protect AI system deployment environment |
| ISO/IEC 42001 | — |
| EU AI Act | Art. 15(5) — Cybersecurity: resilience against unauthorised attempts to alter use, outputs or performance, including data and model poisoning, adversarial examples and confidentiality attacks |
| ISO/IEC 27001 | A.5.23 — Information security for use of cloud services<br>A.8.20 — Networks security<br>A.8.21 — Security of network services |
| Sources | NIST SP 800-207; CSA Cloud Controls Matrix v4 |

<a id="net-06"></a>

### NET-06 · Edge protection: API gateway, WAF and DDoS mitigation

**Objective.** Front internet-facing applications and model endpoints with an API gateway, WAF and managed DDoS protection that enforce schemas, rate limits and bot controls.

**Guidance**

- Put internet-facing apps and APIs behind an API gateway and WAF (e.g. OWASP CRS) with managed DDoS protection.
- Validate requests against OpenAPI schemas at the gateway; enforce request-size limits and per-identity, per-tenant and per-IP rate limits.
- For model endpoints, add token-based quotas and anti-scraping or bot controls.

| | |
|---|---|
| STRIDE | Denial of Service, Tampering |
| Mitigates | LLM10 Unbounded Consumption |
| AIUC-1 | B004 — Prevent AI endpoint scraping |
| ISO/IEC 42001 | — |
| EU AI Act | Art. 15(4) — Robustness: resilience to errors, faults and inconsistencies, including backup or fail-safe plans<br>Art. 15(5) — Cybersecurity: resilience against unauthorised attempts to alter use, outputs or performance, including data and model poisoning, adversarial examples and confidentiality attacks |
| ISO/IEC 27001 | A.8.6 — Capacity management<br>A.8.20 — Networks security |
| Sources | OWASP Core Rule Set; OWASP API Security Top 10 2023 (API4) |

<a id="domain-log"></a>

## LOG — Logging, Monitoring & Response

Security event logging, tamper-evident retention, detection and alerting, capacity and cost monitoring, and incident response.

| ID | Control | STRIDE |
|----|---------|--------|
| [LOG-01](#log-01) | Structured, attributable security event logging | R |
| [LOG-02](#log-02) | Tamper-evident log storage and retention | R, T |
| [LOG-03](#log-03) | Centralised detection and alerting | R, D, E, I |
| [LOG-04](#log-04) | Security incident response and forensic readiness | R, D |
| [LOG-05](#log-05) | Service health, capacity and cost-anomaly monitoring | D |

<a id="log-01"></a>

### LOG-01 · Structured, attributable security event logging

**Objective.** Log authentication, authorisation, administrative, data-access, configuration and key-usage events as structured, correlated records — without logging secrets or raw personal data.

**Guidance**

- Log who, what, when, where and outcome for authentication, authorisation decisions, admin actions, sensitive data access, configuration changes and key use, as structured JSON with correlation and trace IDs (e.g. OpenTelemetry).
- Never log secrets, tokens or full personal data; redact at source (DAT-07).
- Neutralise log injection (encode CR/LF and delimiters) and synchronise clocks (NTP).

| | |
|---|---|
| STRIDE | Repudiation |
| Mitigates | A09:2025 Security Logging and Alerting Failures |
| AIUC-1 | E015 — Log AI system activity |
| ISO/IEC 42001 | A.6.2.8 — AI system recording of event logs |
| EU AI Act | Art. 12 — Record-keeping (automatic logging of events) |
| ISO/IEC 27001 | A.8.15 — Logging<br>A.8.17 — Clock synchronization |
| Sources | OWASP Logging Cheat Sheet; OWASP ASVS 5.0 V16; NIST SP 800-92 |

<a id="log-02"></a>

### LOG-02 · Tamper-evident log storage and retention

**Objective.** Ship logs off-host in near real time to append-only, access-controlled storage the logged system cannot alter, and retain them as law and investigations require.

**Guidance**

- Forward logs in near real time to central storage the source system cannot modify; use WORM storage (e.g. S3 Object Lock in compliance mode) or hash-chained, signed batches.
- Separate log administration from system administration, and encrypt log stores (DAT-02).
- Set retention to meet legal requirements: under the EU AI Act, high-risk system logs are kept for at least six months (Art. 19, Art. 26).
- Alert on gaps in the logging pipeline — a silent pipeline is an attacker's best friend.

| | |
|---|---|
| STRIDE | Repudiation, Tampering |
| Mitigates | A09:2025 Security Logging and Alerting Failures |
| AIUC-1 | E015 — Log AI system activity |
| ISO/IEC 42001 | A.6.2.8 — AI system recording of event logs |
| EU AI Act | Art. 12 — Record-keeping (automatic logging of events)<br>Art. 19 — Automatically generated logs (provider retention)<br>Art. 26 — Obligations of deployers of high-risk AI systems |
| ISO/IEC 27001 | A.5.28 — Collection of evidence<br>A.5.33 — Protection of records<br>A.8.15 — Logging |
| Sources | OWASP Logging Cheat Sheet; NIST SP 800-92 |

<a id="log-03"></a>

### LOG-03 · Centralised detection and alerting

**Objective.** Correlate security telemetry in a SIEM with detections mapped to MITRE ATT&CK and ATLAS, and route actionable alerts to an on-call responder.

**Guidance**

- Correlate logs in a SIEM with detections mapped to MITRE ATT&CK and ATLAS: credential stuffing, privilege escalation, anomalous data access, key misuse, prompt-injection indicators and abnormal tool-call patterns.
- Route alerts to an on-call owner with runbooks; automate containment with SOAR where safe.
- Tune for signal and track mean time to detect and respond.

| | |
|---|---|
| STRIDE | Repudiation, Denial of Service, Elevation of Privilege, Information Disclosure |
| Mitigates | A09:2025 Security Logging and Alerting Failures |
| AIUC-1 | — |
| ISO/IEC 42001 | A.6.2.6 — AI system operation and monitoring |
| EU AI Act | Art. 15(5) — Cybersecurity: resilience against unauthorised attempts to alter use, outputs or performance, including data and model poisoning, adversarial examples and confidentiality attacks<br>Art. 26 — Obligations of deployers of high-risk AI systems |
| ISO/IEC 27001 | A.5.25 — Assessment and decision on information security events<br>A.8.16 — Monitoring activities |
| Sources | MITRE ATT&CK; MITRE ATLAS; NIST SP 800-61 Rev. 3 |

<a id="log-04"></a>

### LOG-04 · Security incident response and forensic readiness

**Objective.** Maintain and exercise an incident response plan, with AI-specific playbooks, evidence preservation and regulatory notification paths.

**Guidance**

- Document roles, severity levels and communications; include AI scenarios such as prompt injection leading to data exfiltration, model or agent compromise, and leaked system prompts.
- Preserve evidence with chain of custody; run tabletop exercises at least annually.
- Pre-agree notification paths: GDPR (72 hours), NIS2 where applicable, and EU AI Act Art. 73 serious-incident reporting for high-risk AI systems.

| | |
|---|---|
| STRIDE | Repudiation, Denial of Service |
| AIUC-1 | E001 — AI failure plan for security breaches |
| ISO/IEC 42001 | A.8.4 — Communication of incidents |
| EU AI Act | Art. 73 — Reporting of serious incidents |
| ISO/IEC 27001 | A.5.24 — Information security incident management planning and preparation<br>A.5.25 — Assessment and decision on information security events<br>A.5.26 — Response to information security incidents<br>A.5.27 — Learning from information security incidents<br>A.5.28 — Collection of evidence |
| Sources | NIST SP 800-61 Rev. 3; ISO/IEC 27035 |

<a id="log-05"></a>

### LOG-05 · Service health, capacity and cost-anomaly monitoring

**Objective.** Monitor availability, capacity, provider rate limits and AI token spend against budgets, alerting on anomalies such as denial-of-wallet.

**Guidance**

- Define SLOs and health checks; alert on capacity saturation and dependency degradation, including model-provider latency and rate limits, with failover.
- Set token and spend budgets per application, tenant and user, and alert on cost anomalies (denial-of-wallet).

| | |
|---|---|
| STRIDE | Denial of Service |
| Mitigates | LLM10 Unbounded Consumption |
| AIUC-1 | — |
| ISO/IEC 42001 | A.6.2.6 — AI system operation and monitoring |
| EU AI Act | Art. 15(4) — Robustness: resilience to errors, faults and inconsistencies, including backup or fail-safe plans |
| ISO/IEC 27001 | A.8.6 — Capacity management<br>A.8.16 — Monitoring activities |
| Sources | Google SRE workbook (SLOs); OWASP LLM10:2025 |

<a id="domain-app"></a>

## APP — Application Security

Secure SDLC and the OWASP Top 10:2025 and ASVS 5.0 control families: injection, output encoding, supply chain, testing, configuration, error handling and resource limits.

| ID | Control | STRIDE |
|----|---------|--------|
| [APP-01](#app-01) | Secure SDLC with threat modelling and security requirements | S, T, R, I, D, E |
| [APP-02](#app-02) | Input validation and injection prevention | T, E, I |
| [APP-03](#app-03) | Context-aware output encoding and content security policy | T, I, E |
| [APP-04](#app-04) | Software supply-chain security (SBOM, signing, provenance) | T, E |
| [APP-05](#app-05) | Automated security testing in CI/CD | T, E, I |
| [APP-06](#app-06) | Secure configuration and hardening | E, I, T |
| [APP-07](#app-07) | Robust error handling and fail-safe behaviour | D, I, E |
| [APP-08](#app-08) | Rate limits, quotas and resource-exhaustion protection | D |
| [APP-09](#app-09) | Secure file upload and document ingestion | T, E, D |
| [APP-10](#app-10) | SSRF-safe outbound requests | I, E |

<a id="app-01"></a>

### APP-01 · Secure SDLC with threat modelling and security requirements

**Objective.** Threat-model at design time and on significant change, derive security requirements from OWASP ASVS, and gate releases on unresolved high risks.

**Guidance**

- Threat-model new systems and significant changes (STRIDE over data flow diagrams) and track identified risks to closure.
- Derive security requirements from OWASP ASVS 5.0 at the level appropriate to the system's risk.
- Follow NIST SSDF (SP 800-218) and, for generative AI, its SP 800-218A profile; gate releases on unresolved high risks.

| | |
|---|---|
| STRIDE | Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege |
| Mitigates | A06:2025 Insecure Design |
| AIUC-1 | C001 — Define AI risk taxonomy |
| ISO/IEC 42001 | A.6.1.3 — Processes for responsible AI system design and development<br>A.6.2.2 — AI system requirements and specification |
| EU AI Act | Art. 9 — Risk management system |
| ISO/IEC 27001 | A.8.25 — Secure development life cycle<br>A.8.26 — Application security requirements<br>A.8.27 — Secure system architecture and engineering principles |
| Sources | NIST SP 800-218 (SSDF); NIST SP 800-218A; OWASP ASVS 5.0; OWASP SAMM; Threat Modeling Manifesto |

<a id="app-02"></a>

### APP-02 · Input validation and injection prevention

**Objective.** Validate all untrusted input server-side against allow-lists and schemas and use parameterised interfaces, never building queries or commands from strings.

**Guidance**

- Validate type, length, range and format server-side against allow-lists or schemas; canonicalise paths before validating them.
- Use parameterised queries and safe APIs; never build SQL, NoSQL, LDAP, shell or template strings from untrusted input — including model output.
- Avoid unsafe deserialisation of untrusted data.

| | |
|---|---|
| STRIDE | Tampering, Elevation of Privilege, Information Disclosure |
| Mitigates | A05:2025 Injection; LLM05 Improper Output Handling |
| AIUC-1 | — |
| ISO/IEC 42001 | — |
| EU AI Act | Art. 15(5) — Cybersecurity: resilience against unauthorised attempts to alter use, outputs or performance, including data and model poisoning, adversarial examples and confidentiality attacks |
| ISO/IEC 27001 | A.8.26 — Application security requirements<br>A.8.28 — Secure coding |
| Sources | OWASP Injection Prevention Cheat Sheet; OWASP ASVS 5.0; CWE-89, CWE-78, CWE-94, CWE-502 |

<a id="app-03"></a>

### APP-03 · Context-aware output encoding and content security policy

**Objective.** Encode output for its sink (HTML, JavaScript, URL, CSV, Markdown), treat model output as untrusted, and enforce a strict Content-Security-Policy.

**Guidance**

- Encode for the destination context; sanitise rich text with a vetted sanitiser (e.g. DOMPurify).
- Treat LLM output as untrusted when rendering it: generated Markdown or HTML can carry XSS, data-exfiltrating image links or CSV formulas.
- Deploy a nonce- or hash-based Content-Security-Policy without unsafe-inline, plus frame-ancestors and X-Content-Type-Options.

| | |
|---|---|
| STRIDE | Tampering, Information Disclosure, Elevation of Privilege |
| Mitigates | A05:2025 Injection; LLM05 Improper Output Handling |
| AIUC-1 | C006 — Prevent output vulnerabilities |
| ISO/IEC 42001 | — |
| EU AI Act | Art. 15(5) — Cybersecurity: resilience against unauthorised attempts to alter use, outputs or performance, including data and model poisoning, adversarial examples and confidentiality attacks |
| ISO/IEC 27001 | A.8.26 — Application security requirements<br>A.8.28 — Secure coding |
| Sources | OWASP Cross Site Scripting Prevention Cheat Sheet; OWASP ASVS 5.0; W3C Content Security Policy Level 3 |

<a id="app-04"></a>

### APP-04 · Software supply-chain security (SBOM, signing, provenance)

**Objective.** Lock and verify dependencies, generate SBOMs and AI-BOMs, sign and verify build artefacts with provenance, and harden the CI/CD pipeline.

**Guidance**

- Pin and lock dependencies with hashes; gate CI on software composition analysis; vet new packages for typosquatting and for hallucinated names an AI assistant suggested (slopsquatting).
- Generate SBOMs (CycloneDX or SPDX), including ML-BOM/AI-BOM entries for models and datasets.
- Sign artefacts and images (Sigstore/cosign), verify signatures at deploy, and produce SLSA build provenance.
- Harden CI/CD: pin actions by commit SHA, use OIDC federation instead of stored cloud keys, and give jobs least-privilege tokens.

| | |
|---|---|
| STRIDE | Tampering, Elevation of Privilege |
| Mitigates | A03:2025 Software Supply Chain Failures; A08:2025 Software or Data Integrity Failures; LLM03 Supply Chain; ASI04 Agentic Supply Chain Vulnerabilities |
| AIUC-1 | E006 — Conduct vendor and model due diligence |
| ISO/IEC 42001 | A.10.3 — Suppliers |
| EU AI Act | Art. 15(5) — Cybersecurity: resilience against unauthorised attempts to alter use, outputs or performance, including data and model poisoning, adversarial examples and confidentiality attacks<br>Art. 25 — Responsibilities along the AI value chain |
| ISO/IEC 27001 | A.5.21 — Managing information security in the ICT supply chain<br>A.8.8 — Management of technical vulnerabilities |
| Sources | SLSA v1; CycloneDX 1.6 (ML-BOM); SPDX 3.0 (AI and Dataset profiles); NIST SP 800-218 (SSDF); OpenSSF Scorecard; Sigstore |

<a id="app-05"></a>

### APP-05 · Automated security testing in CI/CD

**Objective.** Run SAST, dependency, secret, IaC and container scanning on every change and DAST before release, with severity-based gates and fix SLAs.

**Guidance**

- Run SAST (e.g. CodeQL, Semgrep, Bandit), SCA (e.g. pip-audit, OSV-Scanner), secret scanning, IaC scanning and container scanning on every change; run DAST (e.g. ZAP) against staging.
- Fail builds on high-severity findings and track the rest against fix SLAs; add periodic penetration tests.
- For AI features, add automated prompt-injection and agent-behaviour test suites (AI-07).

| | |
|---|---|
| STRIDE | Tampering, Elevation of Privilege, Information Disclosure |
| Mitigates | A02:2025 Security Misconfiguration; A03:2025 Software Supply Chain Failures; A05:2025 Injection |
| AIUC-1 | C002 — Conduct pre-deployment testing |
| ISO/IEC 42001 | A.6.2.4 — AI system verification and validation |
| EU AI Act | Art. 15(5) — Cybersecurity: resilience against unauthorised attempts to alter use, outputs or performance, including data and model poisoning, adversarial examples and confidentiality attacks |
| ISO/IEC 27001 | A.8.8 — Management of technical vulnerabilities<br>A.8.29 — Security testing in development and acceptance |
| Sources | NIST SP 800-218 (SSDF); OWASP Web Security Testing Guide; OWASP DevSecOps Guideline |

<a id="app-06"></a>

### APP-06 · Secure configuration and hardening

**Objective.** Deploy from hardened, code-defined baselines — non-root, minimal containers, restricted pod security, no debug endpoints or default credentials — with drift detection.

**Guidance**

- Apply hardened baselines (CIS Benchmarks) to hosts, containers, Kubernetes (Pod Security Standards: restricted) and cloud accounts (CSPM).
- Run containers as non-root with a read-only root filesystem, dropped capabilities and seccomp; never mount the Docker socket.
- Disable debug modes, verbose errors and default credentials in production; manage configuration as code with drift detection.

| | |
|---|---|
| STRIDE | Elevation of Privilege, Information Disclosure, Tampering |
| Mitigates | A02:2025 Security Misconfiguration |
| AIUC-1 | B008 — Protect AI system deployment environment |
| ISO/IEC 42001 | A.6.2.5 — AI system deployment |
| EU AI Act | Art. 15(5) — Cybersecurity: resilience against unauthorised attempts to alter use, outputs or performance, including data and model poisoning, adversarial examples and confidentiality attacks |
| ISO/IEC 27001 | A.8.9 — Configuration management |
| Sources | CIS Benchmarks; Kubernetes Pod Security Standards; NIST SP 800-190 |

<a id="app-07"></a>

### APP-07 · Robust error handling and fail-safe behaviour

**Objective.** Fail closed on security errors, return generic error messages, and handle dependency failures (including model-provider outages and tool errors) explicitly.

**Guidance**

- Fail closed when authentication, authorisation or validation errors occur.
- Return generic errors to clients; keep stack traces, SQL and file paths in logs only.
- Handle timeouts and partial failures of dependencies — model providers, tools, vector stores — with bounded retries, backoff and circuit breakers.

| | |
|---|---|
| STRIDE | Denial of Service, Information Disclosure, Elevation of Privilege |
| Mitigates | A10:2025 Mishandling of Exceptional Conditions |
| AIUC-1 | — |
| ISO/IEC 42001 | — |
| EU AI Act | Art. 15(4) — Robustness: resilience to errors, faults and inconsistencies, including backup or fail-safe plans |
| ISO/IEC 27001 | A.8.28 — Secure coding |
| Sources | OWASP Top 10:2025 A10; OWASP ASVS 5.0 V16; OWASP Error Handling Cheat Sheet |

<a id="app-08"></a>

### APP-08 · Rate limits, quotas and resource-exhaustion protection

**Objective.** Bound resource use per user, tenant and key — request rates, concurrency, payload sizes, timeouts, and for model features input/output token and spend budgets.

**Guidance**

- Apply per-user, per-tenant and per-key rate limits and concurrency caps; bound payload, file and page sizes and set timeouts everywhere.
- For model features, cap max_tokens per request, limit context length, and enforce daily token or spend budgets per user and tenant.
- Throttle expensive operations and apply back-pressure on queues.

| | |
|---|---|
| STRIDE | Denial of Service |
| Mitigates | LLM10 Unbounded Consumption |
| AIUC-1 | B004 — Prevent AI endpoint scraping |
| ISO/IEC 42001 | — |
| EU AI Act | Art. 15(4) — Robustness: resilience to errors, faults and inconsistencies, including backup or fail-safe plans |
| ISO/IEC 27001 | A.8.6 — Capacity management |
| Sources | OWASP API Security Top 10 2023 (API4); OWASP LLM10:2025 |

<a id="app-09"></a>

### APP-09 · Secure file upload and document ingestion

**Objective.** Accept files by content-verified type and size, scan and parse them in isolated workers with hardened parsers, and screen RAG ingestion for hidden instructions.

**Guidance**

- Allow-list file types by content (magic bytes), enforce size limits, and store uploads outside the web root under random names.
- Scan for malware or disarm content; parse untrusted PDF, Office, XML and image formats in sandboxed workers with hardened parsers (e.g. defusedxml against XXE; guards against zip bombs).
- For RAG ingestion, record provenance and screen for hidden prompt-injection payloads (white or zero-width text, metadata, alt text).

| | |
|---|---|
| STRIDE | Tampering, Elevation of Privilege, Denial of Service |
| Mitigates | A05:2025 Injection; LLM01 Prompt Injection; LLM04 Data and Model Poisoning |
| AIUC-1 | B002 — Detect adversarial input |
| ISO/IEC 42001 | — |
| EU AI Act | Art. 15(5) — Cybersecurity: resilience against unauthorised attempts to alter use, outputs or performance, including data and model poisoning, adversarial examples and confidentiality attacks |
| ISO/IEC 27001 | A.8.7 — Protection against malware<br>A.8.28 — Secure coding |
| Sources | OWASP File Upload Cheat Sheet; OWASP XML External Entity Prevention Cheat Sheet |

<a id="app-10"></a>

### APP-10 · SSRF-safe outbound requests

**Objective.** Allow-list the destinations of any server-side fetch — webhooks, URL previews, RAG web loaders, agent browsing tools — and block private, link-local and metadata addresses after resolution.

**Guidance**

- Allow-list scheme, host and port for every server-side fetch; resolve then validate the IP address to block private, loopback, link-local and metadata ranges, defeating DNS rebinding.
- Disable redirects or re-validate each hop; route fetches through the egress proxy (NET-02).

| | |
|---|---|
| STRIDE | Information Disclosure, Elevation of Privilege |
| Mitigates | A01:2025 Broken Access Control |
| AIUC-1 | — |
| ISO/IEC 42001 | — |
| EU AI Act | Art. 15(5) — Cybersecurity: resilience against unauthorised attempts to alter use, outputs or performance, including data and model poisoning, adversarial examples and confidentiality attacks |
| ISO/IEC 27001 | A.8.28 — Secure coding |
| Sources | OWASP SSRF Prevention Cheat Sheet; OWASP API Security Top 10 2023 (API7) |

<a id="domain-ai"></a>

## AI — AI & LLM Application Security

Controls specific to language-model features: prompt injection, output handling, prompt hygiene, RAG access control, data and model provenance, red teaming, output guardrails and transparency.

| ID | Control | STRIDE |
|----|---------|--------|
| [AI-01](#ai-01) | Prompt-injection defences for untrusted content | T, E, S |
| [AI-02](#ai-02) | Validate model output before it is used | T, E |
| [AI-03](#ai-03) | System prompt hygiene: no secrets or security logic in context | I |
| [AI-04](#ai-04) | Retrieval (RAG) access control and source provenance | I, T, E |
| [AI-05](#ai-05) | Training and fine-tuning data governance | T, I |
| [AI-06](#ai-06) | Model provenance, integrity and AI-BOM | T, E |
| [AI-07](#ai-07) | Adversarial testing and AI red teaming | S, T, R, I, D, E |
| [AI-08](#ai-08) | Output guardrails: harmful, out-of-scope and hallucinated content | R, T, I |
| [AI-09](#ai-09) | AI transparency and disclosure | R, S |

<a id="ai-01"></a>

### AI-01 · Prompt-injection defences for untrusted content

**Objective.** Treat user, retrieved and tool content as data, not instructions: segregate and label it, screen it for injection, and keep authorisation decisions outside the model.

**Guidance**

- Never rely on the system prompt as a security boundary; enforce authorisation and policy in code outside the model.
- Segregate and label untrusted content (delimiting or spotlighting, structured message roles) and screen direct and indirect inputs with injection and jailbreak classifiers.
- Use privilege separation: a quarantined model processes untrusted content without tool access, or a plan-then-execute design whose control flow untrusted data cannot change.
- Re-test defences continuously (AI-07); they degrade as models and attacks change.

| | |
|---|---|
| STRIDE | Tampering, Elevation of Privilege, Spoofing |
| Mitigates | LLM01 Prompt Injection; ASI01 Agent Goal Hijack |
| AIUC-1 | B002 — Detect adversarial input<br>B005 — Implement real-time input filtering |
| ISO/IEC 42001 | — |
| EU AI Act | Art. 15(5) — Cybersecurity: resilience against unauthorised attempts to alter use, outputs or performance, including data and model poisoning, adversarial examples and confidentiality attacks |
| ISO/IEC 27001 | A.8.26 — Application security requirements |
| Sources | OWASP LLM01:2025; OWASP LLM Prompt Injection Prevention Cheat Sheet; MITRE ATLAS AML.T0051; NIST AI 100-2 E2025 |

<a id="ai-02"></a>

### AI-02 · Validate model output before it is used

**Objective.** Validate structured model output against strict schemas and never pass it to interpreters, shells, queries or privileged APIs without allow-listing.

**Guidance**

- Validate structured output against a strict schema (JSON Schema, Pydantic) and reject anything that does not conform.
- Never pass model output to eval/exec, a shell, SQL or a privileged API without allow-listing; encode it for its sink (APP-03).
- Run generated code only in a sandbox (AGT-08) and route high-impact outputs to human review.

| | |
|---|---|
| STRIDE | Tampering, Elevation of Privilege |
| Mitigates | LLM05 Improper Output Handling; ASI05 Unexpected Code Execution |
| AIUC-1 | C006 — Prevent output vulnerabilities |
| ISO/IEC 42001 | — |
| EU AI Act | Art. 15(5) — Cybersecurity: resilience against unauthorised attempts to alter use, outputs or performance, including data and model poisoning, adversarial examples and confidentiality attacks |
| ISO/IEC 27001 | A.8.28 — Secure coding |
| Sources | OWASP LLM05:2025; OWASP Top 10 for Agentic Applications ASI05 |

<a id="ai-03"></a>

### AI-03 · System prompt hygiene: no secrets or security logic in context

**Objective.** Keep credentials, internal endpoints and authorisation logic out of system prompts, tool descriptions and model context, on the assumption that prompts can be extracted.

**Guidance**

- Assume system prompts and tool descriptions can be extracted; keep credentials, connection strings, internal URLs and access rules out of them.
- Enforce policy in code, not in prompt wording; minimise sensitive data placed in the context window.
- Detect and alert on prompt-extraction attempts.

| | |
|---|---|
| STRIDE | Information Disclosure |
| Mitigates | LLM07 System Prompt Leakage; LLM02 Sensitive Information Disclosure |
| AIUC-1 | A004 — Protect IP & trade secrets<br>A008 — Prevent leakage of credentials and secrets<br>B009 — Limit output over-exposure |
| ISO/IEC 42001 | — |
| EU AI Act | Art. 15(5) — Cybersecurity: resilience against unauthorised attempts to alter use, outputs or performance, including data and model poisoning, adversarial examples and confidentiality attacks |
| ISO/IEC 27001 | A.5.17 — Authentication information |
| Sources | OWASP LLM07:2025 |

<a id="ai-04"></a>

### AI-04 · Retrieval (RAG) access control and source provenance

**Objective.** Enforce the requesting user's permissions at retrieval time, partition indexes by tenant, control who can write to the corpus, and record provenance for every chunk.

**Guidance**

- Propagate document ACLs into vector-store metadata and filter at query time by the requesting user's entitlements.
- Partition indexes or namespaces per tenant (DAT-08) and restrict who and what can write to the corpus.
- Record source, owner, content hash and ingestion time per chunk; re-validate retrieved content before use and support deletion across embeddings.
- Monitor for anomalous retrieval patterns and corpus changes.

| | |
|---|---|
| STRIDE | Information Disclosure, Tampering, Elevation of Privilege |
| Mitigates | LLM08 Vector and Embedding Weaknesses; LLM04 Data and Model Poisoning; LLM02 Sensitive Information Disclosure; ASI06 Memory and Context Poisoning |
| AIUC-1 | A003 — Limit AI agent data access<br>A005 — Prevent cross-customer data exposure |
| ISO/IEC 42001 | A.7.5 — Data provenance |
| EU AI Act | Art. 15(5) — Cybersecurity: resilience against unauthorised attempts to alter use, outputs or performance, including data and model poisoning, adversarial examples and confidentiality attacks |
| ISO/IEC 27001 | A.8.3 — Information access restriction |
| Sources | OWASP LLM08:2025; NIST AI 600-1 |

<a id="ai-05"></a>

### AI-05 · Training and fine-tuning data governance

**Objective.** Govern training, fine-tuning and evaluation data with documented sourcing, quality and bias checks, lineage, integrity protection and poisoning detection.

**Guidance**

- Document data sources, collection, consent and licensing; keep lineage from source to model version.
- Check data quality and representativeness, de-duplicate, and keep evaluation sets separate from training data.
- Protect dataset integrity (hashes or signatures) and scan for poisoning and backdoor triggers before training.
- Publish datasheets or data cards for significant datasets.

| | |
|---|---|
| STRIDE | Tampering, Information Disclosure |
| Mitigates | LLM04 Data and Model Poisoning |
| AIUC-1 | A001 — Establish input data policy |
| ISO/IEC 42001 | A.7.2 — Data for development and enhancement of AI system<br>A.7.3 — Acquisition of data<br>A.7.4 — Quality of data for AI systems<br>A.7.5 — Data provenance<br>A.7.6 — Data preparation |
| EU AI Act | Art. 10 — Data and data governance<br>Art. 15(5) — Cybersecurity: resilience against unauthorised attempts to alter use, outputs or performance, including data and model poisoning, adversarial examples and confidentiality attacks |
| ISO/IEC 27001 | — |
| Sources | OWASP LLM04:2025; NIST AI 600-1; ISO/IEC 5259 series |

<a id="ai-06"></a>

### AI-06 · Model provenance, integrity and AI-BOM

**Objective.** Source models from trusted registries, verify their signatures or hashes, prefer non-executable weight formats, pin versions, and keep an AI bill of materials.

**Guidance**

- Pull models from trusted registries; verify hashes or signatures (e.g. OpenSSF Model Signing / Sigstore) before loading.
- Prefer safetensors over pickle-based formats and scan model files for embedded code.
- Pin model versions and re-evaluate before upgrading; keep an AI-BOM covering models, adapters, datasets, prompts and tools.

| | |
|---|---|
| STRIDE | Tampering, Elevation of Privilege |
| Mitigates | LLM03 Supply Chain; ASI04 Agentic Supply Chain Vulnerabilities |
| AIUC-1 | E006 — Conduct vendor and model due diligence |
| ISO/IEC 42001 | A.10.2 — Allocating responsibilities<br>A.10.3 — Suppliers |
| EU AI Act | Art. 15(5) — Cybersecurity: resilience against unauthorised attempts to alter use, outputs or performance, including data and model poisoning, adversarial examples and confidentiality attacks<br>Art. 25 — Responsibilities along the AI value chain |
| ISO/IEC 27001 | A.5.19 — Information security in supplier relationships<br>A.5.21 — Managing information security in the ICT supply chain |
| Sources | OWASP LLM03:2025; OpenSSF Model Signing; CycloneDX 1.6 (ML-BOM) |

<a id="ai-07"></a>

### AI-07 · Adversarial testing and AI red teaming

**Objective.** Test for prompt injection, jailbreaks, data leakage, tool misuse, harmful or out-of-scope output and hallucination before every release and on model or prompt changes, including independent testing for high-risk systems.

**Guidance**

- Maintain regression suites for prompt injection (direct and indirect), jailbreaks, data exfiltration, tool misuse, harmful and out-of-scope output and hallucination (e.g. garak, PyRIT, promptfoo).
- Re-run them on every model, prompt, tool or retrieval-corpus change; commission independent third-party testing for high-risk systems.
- Map tests to MITRE ATLAS and the OWASP LLM and Agentic Top 10s, and track findings to closure.

| | |
|---|---|
| STRIDE | Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege |
| Mitigates | LLM01 Prompt Injection; ASI01 Agent Goal Hijack |
| AIUC-1 | B001 — Third-party testing of adversarial robustness<br>C002 — Conduct pre-deployment testing<br>C010 — Third-party testing for harmful outputs<br>C011 — Third-party testing for out-of-scope outputs<br>C012 — Third-party testing for customer-defined risk<br>D002 — Third-party testing for hallucinations<br>D004 — Third-party testing for tool execution |
| ISO/IEC 42001 | A.6.2.4 — AI system verification and validation |
| EU AI Act | Art. 9 — Risk management system<br>Art. 15(5) — Cybersecurity: resilience against unauthorised attempts to alter use, outputs or performance, including data and model poisoning, adversarial examples and confidentiality attacks<br>Art. 55(1) — General-purpose AI models with systemic risk: evaluation incl. adversarial testing, incident reporting and cybersecurity protection |
| ISO/IEC 27001 | A.8.29 — Security testing in development and acceptance |
| Sources | OWASP GenAI Red Teaming Guide; MITRE ATLAS; NIST AI 600-1 |

<a id="ai-08"></a>

### AI-08 · Output guardrails: harmful, out-of-scope and hallucinated content

**Objective.** Filter harmful and out-of-scope output, ground factual answers in cited sources, flag high-risk output for human review, and measure hallucination rates.

**Guidance**

- Apply moderation classifiers to output and enforce the assistant's intended scope (topic or task allow-list).
- Require grounding with source citations for factual answers, and let the system abstain when confidence is low.
- Flag high-risk outputs for human review and give users a way to report bad output.
- Measure harmful-output and hallucination rates on evaluation sets and in production.

| | |
|---|---|
| STRIDE | Repudiation, Tampering, Information Disclosure |
| Mitigates | LLM09 Misinformation; ASI09 Human-Agent Trust Exploitation |
| AIUC-1 | A007 — Prevent IP violations<br>C003 — Prevent harmful outputs<br>C004 — Prevent out-of-scope outputs<br>C005 — Prevent agent-specific high risk outputs<br>C007 — Flag high risk outputs for human review<br>D001 — Prevent hallucinated outputs<br>F001 — Prevent AI cyber misuse |
| ISO/IEC 42001 | A.6.2.6 — AI system operation and monitoring<br>A.9.4 — Intended use of the AI system |
| EU AI Act | Art. 14 — Human oversight<br>Art. 15(1) — Appropriate level of accuracy, robustness and cybersecurity throughout the lifecycle |
| ISO/IEC 27001 | — |
| Sources | OWASP LLM09:2025; NIST AI 600-1 |

<a id="ai-09"></a>

### AI-09 · AI transparency and disclosure

**Objective.** Tell people when they are interacting with AI, mark AI-generated content in a machine-readable way where required, and document capabilities, limitations and intended use.

**Guidance**

- Disclose AI interaction to users and label AI-generated content; apply machine-readable marking (e.g. C2PA content credentials or watermarking) where required.
- Publish system or model cards covering intended purpose, capabilities, limitations and known risks, and instructions for deployers.

| | |
|---|---|
| STRIDE | Repudiation, Spoofing |
| Mitigates | LLM09 Misinformation; ASI09 Human-Agent Trust Exploitation |
| AIUC-1 | E016 — Implement AI disclosure mechanisms<br>E017 — Document system transparency policy |
| ISO/IEC 42001 | A.8.2 — System documentation and information for users<br>A.8.5 — Information for interested parties |
| EU AI Act | Art. 13 — Transparency and provision of information to deployers<br>Art. 50(1) — Inform people that they are interacting with an AI system<br>Art. 50(2) — Mark synthetic audio, image, video and text output in a machine-readable, detectable format |
| ISO/IEC 27001 | — |
| Sources | C2PA specification; NIST AI 600-1 |

<a id="domain-agt"></a>

## AGT — Agentic AI

Controls for agents that act: inventory and ownership, least agency, agent identity and delegated credentials, tool governance, human approval, sandboxing, memory integrity, inter-agent trust, audit, monitoring, kill switch and execution budgets.

| ID | Control | STRIDE |
|----|---------|--------|
| [AGT-01](#agt-01) | Agent inventory, named owner and assigned autonomy level | R, E, S |
| [AGT-02](#agt-02) | Least-agency design | E |
| [AGT-03](#agt-03) | Distinct, verifiable identity for every agent | S, R |
| [AGT-04](#agt-04) | Task-scoped, short-lived, delegated credentials | E, I, S |
| [AGT-05](#agt-05) | Tool allow-listing with policy-enforced, schema-validated calls | E, T |
| [AGT-06](#agt-06) | Tool and MCP supply-chain integrity | T, S, E |
| [AGT-07](#agt-07) | Risk-tiered human approval for high-impact actions | E, R, T |
| [AGT-08](#agt-08) | Sandboxed, ephemeral execution of agent actions | E, T, D |
| [AGT-09](#agt-09) | Memory and context integrity | T, I |
| [AGT-10](#agt-10) | Authenticated, authorised inter-agent communication | S, T, E, R |
| [AGT-11](#agt-11) | Action-level, tamper-evident audit trail for agents | R |
| [AGT-12](#agt-12) | Behavioural monitoring, anomaly detection and canaries | R, I, E |
| [AGT-13](#agt-13) | Kill switch and rapid containment | D, E, R |
| [AGT-14](#agt-14) | Execution budgets, loop limits and circuit breakers | D |

<a id="agt-01"></a>

### AGT-01 · Agent inventory, named owner and assigned autonomy level

**Objective.** Register every agent with a named accountable owner, purpose, autonomy level (L1-L4), tools, data scopes and credentials, and block agents that are unregistered or unowned.

**Guidance**

- Govern agents as you would privileged accounts: keep a registry recording owner, business purpose, autonomy level (L1 human-as-operator to L4 human-as-auditor), model and version, tools and MCP servers, data scopes, credentials and environments.
- Deny runtime access to agents that are not registered or have no owner; retire agents together with their credentials so none are orphaned.
- Derive the required controls from the autonomy level — higher autonomy needs stronger approval gates, isolation, monitoring and a tested kill switch.
- Review the registry quarterly and whenever an agent gains tools, data or autonomy.

| | |
|---|---|
| STRIDE | Repudiation, Elevation of Privilege, Spoofing |
| Mitigates | ASI03 Identity and Privilege Abuse; ASI10 Rogue Agents |
| AIUC-1 | E004 — Assign accountability |
| ISO/IEC 42001 | A.3.2 — AI roles and responsibilities<br>A.4.2 — Resource documentation |
| EU AI Act | Art. 26 — Obligations of deployers of high-risk AI systems |
| ISO/IEC 27001 | A.5.9 — Inventory of information and other associated assets<br>A.5.16 — Identity management |
| Sources | Emmanuel Dahunsi, The Agentic AI Controls That Actually Matter (Part 1); CSA Agentic AI Autonomy Levels and Control Framework (2026); OWASP Agentic AI - Threats and Mitigations |

<a id="agt-02"></a>

### AGT-02 · Least-agency design

**Objective.** Give each agent the lowest autonomy, narrowest goal and smallest action space that meet the business need, preferring deterministic workflows for high-risk tasks.

**Guidance**

- Choose the lowest autonomy level that meets the need; prefer deterministic workflows with model steps over open-ended agents for high-risk tasks.
- Scope goals narrowly, bound the action space, and separate planning from execution.
- Re-assess autonomy whenever tools, data scopes or integrations change.

| | |
|---|---|
| STRIDE | Elevation of Privilege |
| Mitigates | LLM06 Excessive Agency; ASI02 Tool Misuse and Exploitation; ASI10 Rogue Agents |
| AIUC-1 | A003 — Limit AI agent data access<br>B006 — Prevent unauthorized AI agent actions |
| ISO/IEC 42001 | A.6.1.3 — Processes for responsible AI system design and development<br>A.9.4 — Intended use of the AI system |
| EU AI Act | Art. 9 — Risk management system |
| ISO/IEC 27001 | A.8.27 — Secure system architecture and engineering principles |
| Sources | OWASP Top 10 for Agentic Applications (2026); OWASP LLM06:2025 |

<a id="agt-03"></a>

### AGT-03 · Distinct, verifiable identity for every agent

**Objective.** Give each agent, and ideally each running instance, its own attested non-human identity — never a shared service account or a human's credentials — so every action is attributable.

**Guidance**

- Issue each agent its own workload identity (SPIFFE or OIDC federation), attested to the runtime it runs in.
- Never let agents use shared service accounts or a person's credentials.
- Carry the agent identity and the delegating user in every downstream call (e.g. act/sub claims via token exchange) so actions are attributable end to end.

| | |
|---|---|
| STRIDE | Spoofing, Repudiation |
| Mitigates | ASI03 Identity and Privilege Abuse; ASI07 Insecure Inter-Agent Communication; ASI10 Rogue Agents |
| AIUC-1 | B006 — Prevent unauthorized AI agent actions |
| ISO/IEC 42001 | — |
| EU AI Act | Art. 15(5) — Cybersecurity: resilience against unauthorised attempts to alter use, outputs or performance, including data and model poisoning, adversarial examples and confidentiality attacks |
| ISO/IEC 27001 | A.5.16 — Identity management<br>A.8.5 — Secure authentication |
| Sources | RFC 8693 (Token Exchange); SPIFFE specification; OWASP Non-Human Identities Top 10 (2025) |

<a id="agt-04"></a>

### AGT-04 · Task-scoped, short-lived, delegated credentials

**Objective.** Issue agents just-in-time credentials scoped to the task and audience with minute-level lifetimes, injected at the tool layer and never placed in the model's context.

**Guidance**

- Mint credentials per task with minimal scopes, a restricted audience (RFC 8707) and a short TTL; revoke them when the task ends.
- Delegate with OAuth token exchange or on-behalf-of flows (RFC 8693) instead of handing agents user tokens or long-lived API keys.
- Inject credentials in the tool-execution layer; never put them in prompts or anywhere the model can read or echo them.
- Separate secret scopes by agent function — an issue-triage agent must not share secrets with release or deployment workflows.

| | |
|---|---|
| STRIDE | Elevation of Privilege, Information Disclosure, Spoofing |
| Mitigates | ASI03 Identity and Privilege Abuse; ASI02 Tool Misuse and Exploitation; LLM06 Excessive Agency |
| AIUC-1 | A003 — Limit AI agent data access<br>A008 — Prevent leakage of credentials and secrets<br>B006 — Prevent unauthorized AI agent actions |
| ISO/IEC 42001 | — |
| EU AI Act | Art. 15(5) — Cybersecurity: resilience against unauthorised attempts to alter use, outputs or performance, including data and model poisoning, adversarial examples and confidentiality attacks |
| ISO/IEC 27001 | A.5.15 — Access control<br>A.5.17 — Authentication information<br>A.5.18 — Access rights<br>A.8.2 — Privileged access rights |
| Sources | RFC 8693; RFC 8707; MCP Authorization specification; Emmanuel Dahunsi, The Supply Chain of Agency |

<a id="agt-05"></a>

### AGT-05 · Tool allow-listing with policy-enforced, schema-validated calls

**Objective.** Expose only the tools a task needs and check every tool call against a schema and policy in deterministic code outside the model, denying destructive operations by default.

**Guidance**

- Allow-list tools per agent and per task; separate read tools from write tools.
- Validate every call in deterministic code (a policy enforcement point) against a strict schema and policy: parameter bounds, target allow-lists, row and amount limits.
- Deny delete, transfer, execute and external-send operations by default unless approved (AGT-07); rate-limit each tool.

| | |
|---|---|
| STRIDE | Elevation of Privilege, Tampering |
| Mitigates | ASI02 Tool Misuse and Exploitation; LLM06 Excessive Agency |
| AIUC-1 | B006 — Prevent unauthorized AI agent actions<br>D003 — Restrict unsafe tool calls |
| ISO/IEC 42001 | — |
| EU AI Act | Art. 15(5) — Cybersecurity: resilience against unauthorised attempts to alter use, outputs or performance, including data and model poisoning, adversarial examples and confidentiality attacks |
| ISO/IEC 27001 | A.5.15 — Access control<br>A.8.3 — Information access restriction |
| Sources | OWASP Top 10 for Agentic Applications ASI02; OWASP LLM06:2025 |

<a id="agt-06"></a>

### AGT-06 · Tool and MCP supply-chain integrity

**Objective.** Allow-list MCP servers and plugins from trusted publishers, pin tool definitions by hash and verify them before granting access — blocking on mismatch — and keep an AI-BOM per agent.

**Guidance**

- Allow-list MCP servers, plugins and tool packages from vetted publishers; verify server identity (TLS/mTLS) and package signatures.
- Pin each tool definition (name, description, schema) by hash; compare the live definition before granting the agent access, and block and alert on any mismatch (rug-pull and tool-poisoning defence).
- Review tool descriptions for hidden instructions before approval.
- Maintain an AI-BOM for every production agent: models, prompts, tools, MCP servers and versions.

| | |
|---|---|
| STRIDE | Tampering, Spoofing, Elevation of Privilege |
| Mitigates | ASI04 Agentic Supply Chain Vulnerabilities; LLM03 Supply Chain |
| AIUC-1 | E006 — Conduct vendor and model due diligence |
| ISO/IEC 42001 | A.4.4 — Tooling resources<br>A.10.3 — Suppliers |
| EU AI Act | Art. 15(5) — Cybersecurity: resilience against unauthorised attempts to alter use, outputs or performance, including data and model poisoning, adversarial examples and confidentiality attacks<br>Art. 25 — Responsibilities along the AI value chain |
| ISO/IEC 27001 | A.5.19 — Information security in supplier relationships<br>A.5.21 — Managing information security in the ICT supply chain |
| Sources | Emmanuel Dahunsi, The Supply Chain of Agency; OWASP Top 10 for Agentic Applications ASI04; MCP specification |

<a id="agt-07"></a>

### AGT-07 · Risk-tiered human approval for high-impact actions

**Objective.** Require explicit human approval for irreversible, financial, privileged, external-communication or bulk-data actions, showing the approver the exact action and its provenance.

**Guidance**

- Classify actions by impact and reversibility; require approval for irreversible, financial, privileged, external-communication and bulk-data actions.
- Show approvers the exact action, parameters and data provenance — not the agent's own summary — to resist human-agent trust exploitation.
- Tie approval thresholds to the agent's autonomy level (AGT-01), time-box approvals, and record approver identity (AGT-11).
- Counter approval fatigue: batch routine low-risk actions and escalate unusual ones.

| | |
|---|---|
| STRIDE | Elevation of Privilege, Repudiation, Tampering |
| Mitigates | ASI09 Human-Agent Trust Exploitation; ASI02 Tool Misuse and Exploitation; LLM06 Excessive Agency |
| AIUC-1 | B006 — Prevent unauthorized AI agent actions<br>C007 — Flag high risk outputs for human review<br>C009 — Enable real-time feedback and intervention |
| ISO/IEC 42001 | A.9.2 — Processes for responsible use of AI systems |
| EU AI Act | Art. 14 — Human oversight<br>Art. 26 — Obligations of deployers of high-risk AI systems |
| ISO/IEC 27001 | — |
| Sources | OWASP Top 10 for Agentic Applications ASI09; EU AI Act Art. 14 |

<a id="agt-08"></a>

### AGT-08 · Sandboxed, ephemeral execution of agent actions

**Objective.** Run agent-generated code and commands in ephemeral, strongly isolated sandboxes with no network by default, no host mounts, strict resource quotas and no agent credentials.

**Guidance**

- Use strong isolation (gVisor, Firecracker microVMs, Kata Containers or WebAssembly), not plain containers on shared hosts.
- No network by default (allow-list via NET-02), no host mounts or Docker socket, read-only base image, dropped capabilities and seccomp.
- Enforce CPU, memory, time and disk quotas and destroy the sandbox after each task; never execute inside the agent's credentialed process.

| | |
|---|---|
| STRIDE | Elevation of Privilege, Tampering, Denial of Service |
| Mitigates | ASI05 Unexpected Code Execution; LLM05 Improper Output Handling |
| AIUC-1 | B008 — Protect AI system deployment environment<br>D003 — Restrict unsafe tool calls |
| ISO/IEC 42001 | — |
| EU AI Act | Art. 15(5) — Cybersecurity: resilience against unauthorised attempts to alter use, outputs or performance, including data and model poisoning, adversarial examples and confidentiality attacks |
| ISO/IEC 27001 | A.8.27 — Secure system architecture and engineering principles |
| Sources | OWASP Top 10 for Agentic Applications ASI05; NIST SP 800-190 |

<a id="agt-09"></a>

### AGT-09 · Memory and context integrity

**Objective.** Partition agent memory by user, tenant and session, record the provenance of every write, validate before persisting and reuse, and support expiry and rollback.

**Guidance**

- Partition memory per user, tenant and session; never let one principal's context reach another's.
- Record provenance (source, writer, time) for every memory write; stop untrusted content from writing long-term memory without validation or review.
- Apply TTLs and size limits, version memory with rollback, and scan stored memory for injected instructions and secrets.

| | |
|---|---|
| STRIDE | Tampering, Information Disclosure |
| Mitigates | ASI06 Memory and Context Poisoning; LLM04 Data and Model Poisoning; LLM08 Vector and Embedding Weaknesses |
| AIUC-1 | A003 — Limit AI agent data access<br>A005 — Prevent cross-customer data exposure |
| ISO/IEC 42001 | — |
| EU AI Act | Art. 15(5) — Cybersecurity: resilience against unauthorised attempts to alter use, outputs or performance, including data and model poisoning, adversarial examples and confidentiality attacks |
| ISO/IEC 27001 | A.8.3 — Information access restriction |
| Sources | OWASP Top 10 for Agentic Applications ASI06 |

<a id="agt-10"></a>

### AGT-10 · Authenticated, authorised inter-agent communication

**Objective.** Mutually authenticate agents, sign messages with their delegation chain, authorise each delegated request against the originating principal's scope, and reject replays.

**Guidance**

- Mutually authenticate agents (mTLS/SPIFFE) and accept only agents in the registry (AGT-01); verify signed agent metadata (e.g. A2A Agent Cards).
- Sign or MAC messages, including task context and delegation chain; reject replays with nonces and expiry.
- Authorise each delegated request against the originating principal's scopes so privileges cannot be laundered through another agent; validate message schemas.

| | |
|---|---|
| STRIDE | Spoofing, Tampering, Elevation of Privilege, Repudiation |
| Mitigates | ASI07 Insecure Inter-Agent Communication; ASI10 Rogue Agents |
| AIUC-1 | B006 — Prevent unauthorized AI agent actions |
| ISO/IEC 42001 | — |
| EU AI Act | Art. 15(5) — Cybersecurity: resilience against unauthorised attempts to alter use, outputs or performance, including data and model poisoning, adversarial examples and confidentiality attacks |
| ISO/IEC 27001 | A.5.14 — Information transfer<br>A.8.5 — Secure authentication |
| Sources | OWASP Top 10 for Agentic Applications ASI07; Agent2Agent (A2A) protocol |

<a id="agt-11"></a>

### AGT-11 · Action-level, tamper-evident audit trail for agents

**Objective.** Record every model call, tool call, approval, delegation and credential use with agent, user, session and model/prompt version, in append-only storage the agent cannot touch.

**Guidance**

- Log what the agent did, not only what it said: each tool call with arguments and a result digest, approvals, delegations and credential use, tagged with agent ID, delegating user, session and trace IDs, and model and prompt versions.
- Write to append-only storage the agent cannot modify (LOG-02); follow the OpenTelemetry GenAI semantic conventions for traces.
- Treat chain-of-thought as testimony, not evidence — the action log is the record.

| | |
|---|---|
| STRIDE | Repudiation |
| Mitigates | ASI09 Human-Agent Trust Exploitation; ASI10 Rogue Agents |
| AIUC-1 | E015 — Log AI system activity |
| ISO/IEC 42001 | A.6.2.8 — AI system recording of event logs |
| EU AI Act | Art. 12 — Record-keeping (automatic logging of events)<br>Art. 19 — Automatically generated logs (provider retention)<br>Art. 26 — Obligations of deployers of high-risk AI systems |
| ISO/IEC 27001 | A.8.15 — Logging |
| Sources | OpenTelemetry GenAI semantic conventions; OWASP Logging Cheat Sheet |

<a id="agt-12"></a>

### AGT-12 · Behavioural monitoring, anomaly detection and canaries

**Objective.** Baseline each agent's tool use, data volumes and destinations, alert on deviation, and plant canary credentials and decoy resources inside its reach.

**Guidance**

- Baseline each agent's normal tools, data volumes, destinations and timing; alert on new tools, bulk reads, unusual egress and off-hours privilege use.
- Plant canary credentials, honeytokens and decoy records or MCP endpoints within the agent's reach — any touch is a high-fidelity signal.
- Watch for goal drift and repeated policy-violation attempts; feed detections into the SIEM (LOG-03).

| | |
|---|---|
| STRIDE | Repudiation, Information Disclosure, Elevation of Privilege |
| Mitigates | ASI10 Rogue Agents; ASI01 Agent Goal Hijack; ASI02 Tool Misuse and Exploitation |
| AIUC-1 | C008 — Monitor AI risk categories |
| ISO/IEC 42001 | A.6.2.6 — AI system operation and monitoring |
| EU AI Act | Art. 26 — Obligations of deployers of high-risk AI systems<br>Art. 72 — Post-market monitoring |
| ISO/IEC 27001 | A.8.16 — Monitoring activities |
| Sources | OWASP Top 10 for Agentic Applications ASI10; MITRE ATLAS |

<a id="agt-13"></a>

### AGT-13 · Kill switch and rapid containment

**Objective.** Provide a tested mechanism to halt one agent instance, an agent type or the whole fleet and revoke its credentials and tool access within minutes, leaving a safe, forensically preserved state.

**Guidance**

- Halt at the granularity needed (instance, agent type, fleet) and atomically revoke tokens, keys and tool access.
- Fail safe: stop accepting tasks, abort in-flight actions, and preserve state for forensics; plan rollback of changes the agent made.
- Let both the owner and the SOC trigger it, and drill it regularly — an untested kill switch is not a control.

| | |
|---|---|
| STRIDE | Denial of Service, Elevation of Privilege, Repudiation |
| Mitigates | ASI10 Rogue Agents; ASI08 Cascading Failures |
| AIUC-1 | C009 — Enable real-time feedback and intervention<br>E001 — AI failure plan for security breaches |
| ISO/IEC 42001 | A.6.2.6 — AI system operation and monitoring |
| EU AI Act | Art. 14(4)(e) — Human oversight: ability to intervene or interrupt the system with a 'stop' button or similar procedure |
| ISO/IEC 27001 | A.5.26 — Response to information security incidents |
| Sources | EU AI Act Art. 14(4)(e); CSA Agentic AI Autonomy Levels and Control Framework (2026) |

<a id="agt-14"></a>

### AGT-14 · Execution budgets, loop limits and circuit breakers

**Objective.** Cap each task's steps, tool calls, tokens, wall-clock time and spend, detect loops, and isolate failures with circuit breakers so one agent cannot cascade into others.

**Guidance**

- Cap steps, tool calls, tokens, wall-clock time and spend per task and per session.
- Detect loops and repeated failing calls; add circuit breakers between agents and on downstream dependencies, with bulkheads per tenant.
- Degrade gracefully by handing off to a human rather than retrying indefinitely.

| | |
|---|---|
| STRIDE | Denial of Service |
| Mitigates | ASI08 Cascading Failures; LLM10 Unbounded Consumption |
| AIUC-1 | — |
| ISO/IEC 42001 | — |
| EU AI Act | Art. 15(4) — Robustness: resilience to errors, faults and inconsistencies, including backup or fail-safe plans |
| ISO/IEC 27001 | A.8.6 — Capacity management |
| Sources | OWASP Top 10 for Agentic Applications ASI08; OWASP LLM10:2025 |

<a id="domain-gov"></a>

## GOV — AI Governance

Organisational controls the AI frameworks require: policy and accountability, risk and impact assessment, documentation and change control, supplier due diligence, incident management and post-deployment monitoring.

| ID | Control | STRIDE |
|----|---------|--------|
| [GOV-01](#gov-01) | AI policy, accountability and acceptable use | — |
| [GOV-02](#gov-02) | AI risk management and impact assessment | — |
| [GOV-03](#gov-03) | AI technical documentation and change control | R |
| [GOV-04](#gov-04) | Third-party AI provider due diligence | I |
| [GOV-05](#gov-05) | AI incident management and serious-incident reporting | R |
| [GOV-06](#gov-06) | Post-deployment monitoring of AI performance and risk | R |

<a id="gov-01"></a>

### GOV-01 · AI policy, accountability and acceptable use

**Objective.** Approve an AI policy, assign roles and accountability for each AI system, publish an acceptable-use policy, and train staff in AI literacy for their role.

**Guidance**

- Have leadership approve an AI policy aligned with security, privacy and data policies, and review it periodically.
- Assign accountable owners and RACI for every AI system; publish acceptable-use rules for staff and customers.
- Provide AI literacy training proportionate to each role (EU AI Act Art. 4).

| | |
|---|---|
| STRIDE | — |
| AIUC-1 | E004 — Assign accountability<br>E010 — Establish AI acceptable use policy |
| ISO/IEC 42001 | A.2.2 — AI policy<br>A.2.3 — Alignment with other organizational policies<br>A.2.4 — Review of the AI policy<br>A.3.2 — AI roles and responsibilities<br>A.4.6 — Human resources |
| EU AI Act | Art. 4 — AI literacy |
| ISO/IEC 27001 | A.5.10 — Acceptable use of information and other associated assets |
| Sources | ISO/IEC 42001:2023 A.2, A.3; NIST AI RMF 1.0 (GOVERN) |

<a id="gov-02"></a>

### GOV-02 · AI risk management and impact assessment

**Objective.** Run a lifecycle AI risk management process — including threat models like this one — classify each system under the EU AI Act, and assess impacts on individuals and society.

**Guidance**

- Identify, analyse, evaluate, treat and monitor AI risks across the lifecycle; feed threat-model findings into the risk register.
- Classify each AI system under the EU AI Act (prohibited, high-risk, transparency-only, minimal; GPAI) and record the rationale.
- Assess impacts on individuals, groups and society, including fundamental rights where required, and re-assess on material change.

| | |
|---|---|
| STRIDE | — |
| AIUC-1 | C001 — Define AI risk taxonomy |
| ISO/IEC 42001 | 6.1.2 — AI risk assessment<br>6.1.4 — AI system impact assessment<br>A.5.2 — AI system impact assessment process<br>A.5.3 — Documentation of AI system impact assessments<br>A.5.4 — Assessing AI system impact on individuals or groups of individuals<br>A.5.5 — Assessing societal impacts of AI systems |
| EU AI Act | Art. 9 — Risk management system<br>Art. 27 — Fundamental rights impact assessment for high-risk AI systems |
| ISO/IEC 27001 | — |
| Sources | ISO/IEC 23894:2023; NIST AI RMF 1.0; ISO/IEC 42005:2025 |

<a id="gov-03"></a>

### GOV-03 · AI technical documentation and change control

**Objective.** Keep current technical documentation for each AI system and version models, prompts, tools and configuration under change control with evaluation evidence before release.

**Guidance**

- Document architecture, data, models, evaluations, limitations and human-oversight measures, and keep them current.
- Version models, prompts, tool definitions and configuration; approve changes with regression-evaluation evidence before release.
- Operate these processes within a quality management system and record regulatory compliance decisions.

| | |
|---|---|
| STRIDE | Repudiation |
| AIUC-1 | E012 — Document regulatory compliance<br>E013 — Implement quality management system |
| ISO/IEC 42001 | A.6.2.3 — Documentation of AI system design and development<br>A.6.2.7 — AI system technical documentation |
| EU AI Act | Art. 11 — Technical documentation<br>Art. 17 — Quality management system |
| ISO/IEC 27001 | A.8.32 — Change management |
| Sources | EU AI Act Annex IV; ISO/IEC 42001:2023 A.6.2 |

<a id="gov-04"></a>

### GOV-04 · Third-party AI provider due diligence

**Objective.** Assess model and AI-tool providers for data use, retention, processing locations, sub-processors, security attestations and incident terms, and monitor their access.

**Guidance**

- Assess providers' training-data use and opt-outs, retention, processing locations, sub-processors and certifications (ISO/IEC 27001, ISO/IEC 42001, SOC 2).
- Allocate responsibilities contractually, including incident notification, and record where data is processed.
- Monitor third-party access and re-assess providers periodically.

| | |
|---|---|
| STRIDE | Information Disclosure |
| Mitigates | LLM03 Supply Chain |
| AIUC-1 | E006 — Conduct vendor and model due diligence<br>E009 — Monitor third-party access<br>E011 — Record processing locations |
| ISO/IEC 42001 | A.10.2 — Allocating responsibilities<br>A.10.3 — Suppliers |
| EU AI Act | Art. 25 — Responsibilities along the AI value chain |
| ISO/IEC 27001 | A.5.19 — Information security in supplier relationships<br>A.5.20 — Addressing information security within supplier agreements<br>A.5.22 — Monitoring, review and change management of supplier services<br>A.5.23 — Information security for use of cloud services |
| Sources | ISO/IEC 42001:2023 A.10; NIST AI RMF 1.0 (GOVERN 6) |

<a id="gov-05"></a>

### GOV-05 · AI incident management and serious-incident reporting

**Objective.** Keep AI-specific failure plans for security breaches, harmful outputs and hallucination-driven harm, integrated with security incident response and regulatory reporting.

**Guidance**

- Write failure plans for AI security breaches, harmful outputs and hallucination-driven harm, covering owner, triage, user communication, remediation and rollback.
- Integrate them with security incident response (LOG-04), and give users and other affected parties a channel to report adverse impacts.
- Report serious incidents under EU AI Act Art. 73 (high-risk systems) and Art. 55 (GPAI with systemic risk), and feed lessons back into risk management.

| | |
|---|---|
| STRIDE | Repudiation |
| AIUC-1 | E001 — AI failure plan for security breaches<br>E002 — AI failure plan for harmful outputs<br>E003 — AI failure plan for hallucinations |
| ISO/IEC 42001 | A.3.3 — Reporting of concerns<br>A.8.3 — External reporting<br>A.8.4 — Communication of incidents |
| EU AI Act | Art. 73 — Reporting of serious incidents |
| ISO/IEC 27001 | A.5.24 — Information security incident management planning and preparation<br>A.5.26 — Response to information security incidents<br>A.5.27 — Learning from information security incidents |
| Sources | NIST SP 800-61 Rev. 3; OECD AI Incidents Monitor (AIM) |

<a id="gov-06"></a>

### GOV-06 · Post-deployment monitoring of AI performance and risk

**Objective.** Monitor deployed AI systems for quality drift, harmful-output and override rates and user complaints, and feed the results back into risk management.

**Guidance**

- Track accuracy and quality drift, harmful-output rates, human override rates and complaints against thresholds.
- Review results with the system owner, re-evaluate periodically and on drift, and update the risk register.
- For high-risk systems, operate a documented post-market monitoring plan.

| | |
|---|---|
| STRIDE | Repudiation |
| Mitigates | LLM09 Misinformation |
| AIUC-1 | C008 — Monitor AI risk categories<br>E008 — Review internal processes |
| ISO/IEC 42001 | 9.1 — Monitoring, measurement, analysis and evaluation<br>A.6.2.6 — AI system operation and monitoring |
| EU AI Act | Art. 26 — Obligations of deployers of high-risk AI systems<br>Art. 72 — Post-market monitoring |
| ISO/IEC 27001 | — |
| Sources | ISO/IEC 42001:2023 9.1; NIST AI RMF 1.0 (MEASURE, MANAGE) |
