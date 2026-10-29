<!-- Generated from stride_gpt/core/controls/catalog.toml by scripts/build_control_catalog.py. Edit the catalogue, not this file. -->

# Framework Crosswalks

Catalogue version **2026.10**. For each framework: every reference the control catalogue maps to, the controls that address it, and the references no control addresses. A reference with no control is usually an organisational process outside the reach of a threat model, not an oversight; see [Controls and compliance mapping](controls-and-compliance.md#what-the-mapping-is-and-isnt).

Contents: [AIUC-1](#aiuc-1) · [ISO/IEC 42001](#iso-42001) · [EU AI Act](#eu-ai-act) · [ISO/IEC 27001](#iso-27001) · [OWASP](#owasp) · [STRIDE](#stride)

<a id="aiuc-1"></a>

## AIUC-1

[AIUC-1 standard for AI agents](https://www.aiuc-1.com/) · version: 2026 (Q3 revision)

> Requirement IDs and titles as published at standard.aiuc-1.com after the Q3 2026 revision (A008 added; C005 renamed; E005 revised; E007 and E014 retired). Requirements whose titles could not be verified are not listed.

| Reference | Requirement | Controls |
|-----------|-------------|----------|
| A001 | Establish input data policy | [DAT-01](controls-catalog.md#dat-01), [AI-05](controls-catalog.md#ai-05) |
| A002 | Establish output data policy | [DAT-01](controls-catalog.md#dat-01) |
| A003 | Limit AI agent data access | [AI-04](controls-catalog.md#ai-04), [AGT-02](controls-catalog.md#agt-02), [AGT-04](controls-catalog.md#agt-04), [AGT-09](controls-catalog.md#agt-09) |
| A004 | Protect IP & trade secrets | [DAT-02](controls-catalog.md#dat-02), [AI-03](controls-catalog.md#ai-03) |
| A005 | Prevent cross-customer data exposure | [DAT-08](controls-catalog.md#dat-08), [AI-04](controls-catalog.md#ai-04), [AGT-09](controls-catalog.md#agt-09) |
| A006 | Prevent PII leakage | [DAT-07](controls-catalog.md#dat-07) |
| A007 | Prevent IP violations | [AI-08](controls-catalog.md#ai-08) |
| A008 | Prevent leakage of credentials and secrets | [DAT-06](controls-catalog.md#dat-06), [AI-03](controls-catalog.md#ai-03), [AGT-04](controls-catalog.md#agt-04) |
| B001 | Third-party testing of adversarial robustness | [AI-07](controls-catalog.md#ai-07) |
| B002 | Detect adversarial input | [APP-09](controls-catalog.md#app-09), [AI-01](controls-catalog.md#ai-01) |
| B004 | Prevent AI endpoint scraping | [NET-06](controls-catalog.md#net-06), [APP-08](controls-catalog.md#app-08) |
| B005 | Implement real-time input filtering | [AI-01](controls-catalog.md#ai-01) |
| B006 | Prevent unauthorized AI agent actions | [NET-02](controls-catalog.md#net-02), [AGT-02](controls-catalog.md#agt-02), [AGT-03](controls-catalog.md#agt-03), [AGT-04](controls-catalog.md#agt-04), [AGT-05](controls-catalog.md#agt-05), [AGT-07](controls-catalog.md#agt-07), [AGT-10](controls-catalog.md#agt-10) |
| B007 | Enforce user access privileges to AI systems | [IAM-01](controls-catalog.md#iam-01), [IAM-02](controls-catalog.md#iam-02), [IAM-05](controls-catalog.md#iam-05), [IAM-06](controls-catalog.md#iam-06), [IAM-07](controls-catalog.md#iam-07) |
| B008 | Protect AI system deployment environment | [IAM-03](controls-catalog.md#iam-03), [IAM-04](controls-catalog.md#iam-04), [IAM-08](controls-catalog.md#iam-08), [DAT-05](controls-catalog.md#dat-05), [NET-01](controls-catalog.md#net-01), [NET-02](controls-catalog.md#net-02), [NET-03](controls-catalog.md#net-03), [NET-04](controls-catalog.md#net-04), [NET-05](controls-catalog.md#net-05), [APP-06](controls-catalog.md#app-06), [AGT-08](controls-catalog.md#agt-08) |
| B009 | Limit output over-exposure | [DAT-07](controls-catalog.md#dat-07), [AI-03](controls-catalog.md#ai-03) |
| C001 | Define AI risk taxonomy | [APP-01](controls-catalog.md#app-01), [GOV-02](controls-catalog.md#gov-02) |
| C002 | Conduct pre-deployment testing | [APP-05](controls-catalog.md#app-05), [AI-07](controls-catalog.md#ai-07) |
| C003 | Prevent harmful outputs | [AI-08](controls-catalog.md#ai-08) |
| C004 | Prevent out-of-scope outputs | [AI-08](controls-catalog.md#ai-08) |
| C005 | Prevent agent-specific high risk outputs | [AI-08](controls-catalog.md#ai-08) |
| C006 | Prevent output vulnerabilities | [APP-03](controls-catalog.md#app-03), [AI-02](controls-catalog.md#ai-02) |
| C007 | Flag high risk outputs for human review | [AI-08](controls-catalog.md#ai-08), [AGT-07](controls-catalog.md#agt-07) |
| C008 | Monitor AI risk categories | [AGT-12](controls-catalog.md#agt-12), [GOV-06](controls-catalog.md#gov-06) |
| C009 | Enable real-time feedback and intervention | [AGT-07](controls-catalog.md#agt-07), [AGT-13](controls-catalog.md#agt-13) |
| C010 | Third-party testing for harmful outputs | [AI-07](controls-catalog.md#ai-07) |
| C011 | Third-party testing for out-of-scope outputs | [AI-07](controls-catalog.md#ai-07) |
| C012 | Third-party testing for customer-defined risk | [AI-07](controls-catalog.md#ai-07) |
| D001 | Prevent hallucinated outputs | [AI-08](controls-catalog.md#ai-08) |
| D002 | Third-party testing for hallucinations | [AI-07](controls-catalog.md#ai-07) |
| D003 | Restrict unsafe tool calls | [AGT-05](controls-catalog.md#agt-05), [AGT-08](controls-catalog.md#agt-08) |
| D004 | Third-party testing for tool execution | [AI-07](controls-catalog.md#ai-07) |
| E001 | AI failure plan for security breaches | [LOG-04](controls-catalog.md#log-04), [AGT-13](controls-catalog.md#agt-13), [GOV-05](controls-catalog.md#gov-05) |
| E002 | AI failure plan for harmful outputs | [GOV-05](controls-catalog.md#gov-05) |
| E003 | AI failure plan for hallucinations | [GOV-05](controls-catalog.md#gov-05) |
| E004 | Assign accountability | [AGT-01](controls-catalog.md#agt-01), [GOV-01](controls-catalog.md#gov-01) |
| E005 | Document data storage security | [DAT-02](controls-catalog.md#dat-02), [DAT-03](controls-catalog.md#dat-03) |
| E006 | Conduct vendor and model due diligence | [APP-04](controls-catalog.md#app-04), [AI-06](controls-catalog.md#ai-06), [AGT-06](controls-catalog.md#agt-06), [GOV-04](controls-catalog.md#gov-04) |
| E008 | Review internal processes | [GOV-06](controls-catalog.md#gov-06) |
| E009 | Monitor third-party access | [GOV-04](controls-catalog.md#gov-04) |
| E010 | Establish AI acceptable use policy | [GOV-01](controls-catalog.md#gov-01) |
| E011 | Record processing locations | [GOV-04](controls-catalog.md#gov-04) |
| E012 | Document regulatory compliance | [GOV-03](controls-catalog.md#gov-03) |
| E013 | Implement quality management system | [GOV-03](controls-catalog.md#gov-03) |
| E015 | Log AI system activity | [LOG-01](controls-catalog.md#log-01), [LOG-02](controls-catalog.md#log-02), [AGT-11](controls-catalog.md#agt-11) |
| E016 | Implement AI disclosure mechanisms | [AI-09](controls-catalog.md#ai-09) |
| E017 | Document system transparency policy | [AI-09](controls-catalog.md#ai-09) |
| F001 | Prevent AI cyber misuse | [AI-08](controls-catalog.md#ai-08) |

**Coverage:** 48 of 49 listed references are addressed by at least one catalogue control.

Not addressed by a catalogue control:

- B003 — Manage public release of technical details

<a id="iso-42001"></a>

## ISO/IEC 42001

[ISO/IEC 42001:2023 — AI management system](https://www.iso.org/standard/81230.html) · version: 2023

> Annex A reference controls plus the clause 6 and 9 requirements they support. ISO/IEC 42001 relies on ISO/IEC 27001 for generic information-security controls, so identity, cryptography and network controls are mapped to ISO/IEC 27001 and only carry an ISO/IEC 42001 reference where an AI-specific control applies.

| Reference | Requirement | Controls |
|-----------|-------------|----------|
| 6.1.2 | AI risk assessment | [GOV-02](controls-catalog.md#gov-02) |
| 6.1.4 | AI system impact assessment | [GOV-02](controls-catalog.md#gov-02) |
| 9.1 | Monitoring, measurement, analysis and evaluation | [GOV-06](controls-catalog.md#gov-06) |
| A.2.2 | AI policy | [GOV-01](controls-catalog.md#gov-01) |
| A.2.3 | Alignment with other organizational policies | [GOV-01](controls-catalog.md#gov-01) |
| A.2.4 | Review of the AI policy | [GOV-01](controls-catalog.md#gov-01) |
| A.3.2 | AI roles and responsibilities | [AGT-01](controls-catalog.md#agt-01), [GOV-01](controls-catalog.md#gov-01) |
| A.3.3 | Reporting of concerns | [GOV-05](controls-catalog.md#gov-05) |
| A.4.2 | Resource documentation | [AGT-01](controls-catalog.md#agt-01) |
| A.4.4 | Tooling resources | [AGT-06](controls-catalog.md#agt-06) |
| A.4.6 | Human resources | [GOV-01](controls-catalog.md#gov-01) |
| A.5.2 | AI system impact assessment process | [GOV-02](controls-catalog.md#gov-02) |
| A.5.3 | Documentation of AI system impact assessments | [GOV-02](controls-catalog.md#gov-02) |
| A.5.4 | Assessing AI system impact on individuals or groups of individuals | [GOV-02](controls-catalog.md#gov-02) |
| A.5.5 | Assessing societal impacts of AI systems | [GOV-02](controls-catalog.md#gov-02) |
| A.6.1.3 | Processes for responsible AI system design and development | [APP-01](controls-catalog.md#app-01), [AGT-02](controls-catalog.md#agt-02) |
| A.6.2.2 | AI system requirements and specification | [APP-01](controls-catalog.md#app-01) |
| A.6.2.3 | Documentation of AI system design and development | [GOV-03](controls-catalog.md#gov-03) |
| A.6.2.4 | AI system verification and validation | [APP-05](controls-catalog.md#app-05), [AI-07](controls-catalog.md#ai-07) |
| A.6.2.5 | AI system deployment | [APP-06](controls-catalog.md#app-06) |
| A.6.2.6 | AI system operation and monitoring | [LOG-03](controls-catalog.md#log-03), [LOG-05](controls-catalog.md#log-05), [AI-08](controls-catalog.md#ai-08), [AGT-12](controls-catalog.md#agt-12), [AGT-13](controls-catalog.md#agt-13), [GOV-06](controls-catalog.md#gov-06) |
| A.6.2.7 | AI system technical documentation | [GOV-03](controls-catalog.md#gov-03) |
| A.6.2.8 | AI system recording of event logs | [LOG-01](controls-catalog.md#log-01), [LOG-02](controls-catalog.md#log-02), [AGT-11](controls-catalog.md#agt-11) |
| A.7.2 | Data for development and enhancement of AI system | [AI-05](controls-catalog.md#ai-05) |
| A.7.3 | Acquisition of data | [AI-05](controls-catalog.md#ai-05) |
| A.7.4 | Quality of data for AI systems | [AI-05](controls-catalog.md#ai-05) |
| A.7.5 | Data provenance | [AI-04](controls-catalog.md#ai-04), [AI-05](controls-catalog.md#ai-05) |
| A.7.6 | Data preparation | [AI-05](controls-catalog.md#ai-05) |
| A.8.2 | System documentation and information for users | [AI-09](controls-catalog.md#ai-09) |
| A.8.3 | External reporting | [GOV-05](controls-catalog.md#gov-05) |
| A.8.4 | Communication of incidents | [LOG-04](controls-catalog.md#log-04), [GOV-05](controls-catalog.md#gov-05) |
| A.8.5 | Information for interested parties | [AI-09](controls-catalog.md#ai-09) |
| A.9.2 | Processes for responsible use of AI systems | [AGT-07](controls-catalog.md#agt-07) |
| A.9.4 | Intended use of the AI system | [AI-08](controls-catalog.md#ai-08), [AGT-02](controls-catalog.md#agt-02) |
| A.10.2 | Allocating responsibilities | [AI-06](controls-catalog.md#ai-06), [GOV-04](controls-catalog.md#gov-04) |
| A.10.3 | Suppliers | [APP-04](controls-catalog.md#app-04), [AI-06](controls-catalog.md#ai-06), [AGT-06](controls-catalog.md#agt-06), [GOV-04](controls-catalog.md#gov-04) |

**Coverage:** 36 of 42 listed references are addressed by at least one catalogue control.

Not addressed by a catalogue control:

- 6.1.3 — AI risk treatment
- A.4.3 — Data resources
- A.4.5 — System and computing resources
- A.6.1.2 — Objectives for responsible development of AI system
- A.9.3 — Objectives for responsible use of AI system
- A.10.4 — Customers

<a id="eu-ai-act"></a>

## EU AI Act

[Regulation (EU) 2024/1689 (Artificial Intelligence Act), as amended by Regulation (EU) 2026/1744](https://eur-lex.europa.eu/eli/reg/2024/1689/oj) · version: 2024/1689 as amended by 2026/1744

> Articles 9-15, 17, 19, 26, 27 and 72-73 apply to high-risk AI systems (Annex III obligations apply from 2 December 2027 and Annex I from 2 August 2028 under Regulation (EU) 2026/1744). Article 50 applies to AI systems that interact with people or generate content, from 2 August 2026. Article 55 applies to providers of general-purpose AI models with systemic risk. Article 4 applies to all providers and deployers.

| Reference | Requirement | Controls |
|-----------|-------------|----------|
| Art. 4 | AI literacy | [GOV-01](controls-catalog.md#gov-01) |
| Art. 9 | Risk management system | [APP-01](controls-catalog.md#app-01), [AI-07](controls-catalog.md#ai-07), [AGT-02](controls-catalog.md#agt-02), [GOV-02](controls-catalog.md#gov-02) |
| Art. 10 | Data and data governance | [AI-05](controls-catalog.md#ai-05) |
| Art. 11 | Technical documentation | [GOV-03](controls-catalog.md#gov-03) |
| Art. 12 | Record-keeping (automatic logging of events) | [LOG-01](controls-catalog.md#log-01), [LOG-02](controls-catalog.md#log-02), [AGT-11](controls-catalog.md#agt-11) |
| Art. 13 | Transparency and provision of information to deployers | [AI-09](controls-catalog.md#ai-09) |
| Art. 14 | Human oversight | [AI-08](controls-catalog.md#ai-08), [AGT-07](controls-catalog.md#agt-07) |
| Art. 14(4)(e) | Human oversight: ability to intervene or interrupt the system with a 'stop' button or similar procedure | [AGT-13](controls-catalog.md#agt-13) |
| Art. 15(1) | Appropriate level of accuracy, robustness and cybersecurity throughout the lifecycle | [AI-08](controls-catalog.md#ai-08) |
| Art. 15(4) | Robustness: resilience to errors, faults and inconsistencies, including backup or fail-safe plans | [DAT-09](controls-catalog.md#dat-09), [NET-06](controls-catalog.md#net-06), [LOG-05](controls-catalog.md#log-05), [APP-07](controls-catalog.md#app-07), [APP-08](controls-catalog.md#app-08), [AGT-14](controls-catalog.md#agt-14) |
| Art. 15(5) | Cybersecurity: resilience against unauthorised attempts to alter use, outputs or performance, including data and model poisoning, adversarial examples and confidentiality attacks | [IAM-01](controls-catalog.md#iam-01), [IAM-02](controls-catalog.md#iam-02), [IAM-03](controls-catalog.md#iam-03), [IAM-04](controls-catalog.md#iam-04), [IAM-05](controls-catalog.md#iam-05), [IAM-06](controls-catalog.md#iam-06), [IAM-07](controls-catalog.md#iam-07), [IAM-08](controls-catalog.md#iam-08), [IAM-09](controls-catalog.md#iam-09), [IAM-10](controls-catalog.md#iam-10), [DAT-02](controls-catalog.md#dat-02), [DAT-03](controls-catalog.md#dat-03), [DAT-04](controls-catalog.md#dat-04), [DAT-05](controls-catalog.md#dat-05), [DAT-06](controls-catalog.md#dat-06), [DAT-08](controls-catalog.md#dat-08), [NET-01](controls-catalog.md#net-01), [NET-02](controls-catalog.md#net-02), [NET-03](controls-catalog.md#net-03), [NET-04](controls-catalog.md#net-04), [NET-05](controls-catalog.md#net-05), [NET-06](controls-catalog.md#net-06), [LOG-03](controls-catalog.md#log-03), [APP-02](controls-catalog.md#app-02), [APP-03](controls-catalog.md#app-03), [APP-04](controls-catalog.md#app-04), [APP-05](controls-catalog.md#app-05), [APP-06](controls-catalog.md#app-06), [APP-09](controls-catalog.md#app-09), [APP-10](controls-catalog.md#app-10), [AI-01](controls-catalog.md#ai-01), [AI-02](controls-catalog.md#ai-02), [AI-03](controls-catalog.md#ai-03), [AI-04](controls-catalog.md#ai-04), [AI-05](controls-catalog.md#ai-05), [AI-06](controls-catalog.md#ai-06), [AI-07](controls-catalog.md#ai-07), [AGT-03](controls-catalog.md#agt-03), [AGT-04](controls-catalog.md#agt-04), [AGT-05](controls-catalog.md#agt-05), [AGT-06](controls-catalog.md#agt-06), [AGT-08](controls-catalog.md#agt-08), [AGT-09](controls-catalog.md#agt-09), [AGT-10](controls-catalog.md#agt-10) |
| Art. 17 | Quality management system | [GOV-03](controls-catalog.md#gov-03) |
| Art. 19 | Automatically generated logs (provider retention) | [LOG-02](controls-catalog.md#log-02), [AGT-11](controls-catalog.md#agt-11) |
| Art. 25 | Responsibilities along the AI value chain | [APP-04](controls-catalog.md#app-04), [AI-06](controls-catalog.md#ai-06), [AGT-06](controls-catalog.md#agt-06), [GOV-04](controls-catalog.md#gov-04) |
| Art. 26 | Obligations of deployers of high-risk AI systems | [LOG-02](controls-catalog.md#log-02), [LOG-03](controls-catalog.md#log-03), [AGT-01](controls-catalog.md#agt-01), [AGT-07](controls-catalog.md#agt-07), [AGT-11](controls-catalog.md#agt-11), [AGT-12](controls-catalog.md#agt-12), [GOV-06](controls-catalog.md#gov-06) |
| Art. 27 | Fundamental rights impact assessment for high-risk AI systems | [GOV-02](controls-catalog.md#gov-02) |
| Art. 50(1) | Inform people that they are interacting with an AI system | [AI-09](controls-catalog.md#ai-09) |
| Art. 50(2) | Mark synthetic audio, image, video and text output in a machine-readable, detectable format | [AI-09](controls-catalog.md#ai-09) |
| Art. 55(1) | General-purpose AI models with systemic risk: evaluation incl. adversarial testing, incident reporting and cybersecurity protection | [AI-07](controls-catalog.md#ai-07) |
| Art. 72 | Post-market monitoring | [AGT-12](controls-catalog.md#agt-12), [GOV-06](controls-catalog.md#gov-06) |
| Art. 73 | Reporting of serious incidents | [LOG-04](controls-catalog.md#log-04), [GOV-05](controls-catalog.md#gov-05) |

**Coverage:** 21 of 21 listed references are addressed by at least one catalogue control.

<a id="iso-27001"></a>

## ISO/IEC 27001

[ISO/IEC 27001:2022 — Annex A information security controls](https://www.iso.org/standard/27001) · version: 2022

> Annex A controls as numbered in ISO/IEC 27001:2022 (aligned with ISO/IEC 27002:2022).

| Reference | Requirement | Controls |
|-----------|-------------|----------|
| A.5.9 | Inventory of information and other associated assets | [AGT-01](controls-catalog.md#agt-01) |
| A.5.10 | Acceptable use of information and other associated assets | [GOV-01](controls-catalog.md#gov-01) |
| A.5.12 | Classification of information | [DAT-01](controls-catalog.md#dat-01) |
| A.5.14 | Information transfer | [DAT-04](controls-catalog.md#dat-04), [DAT-05](controls-catalog.md#dat-05), [AGT-10](controls-catalog.md#agt-10) |
| A.5.15 | Access control | [IAM-06](controls-catalog.md#iam-06), [IAM-07](controls-catalog.md#iam-07), [AGT-04](controls-catalog.md#agt-04), [AGT-05](controls-catalog.md#agt-05) |
| A.5.16 | Identity management | [IAM-01](controls-catalog.md#iam-01), [IAM-04](controls-catalog.md#iam-04), [IAM-10](controls-catalog.md#iam-10), [AGT-01](controls-catalog.md#agt-01), [AGT-03](controls-catalog.md#agt-03) |
| A.5.17 | Authentication information | [IAM-01](controls-catalog.md#iam-01), [IAM-02](controls-catalog.md#iam-02), [IAM-10](controls-catalog.md#iam-10), [DAT-06](controls-catalog.md#dat-06), [AI-03](controls-catalog.md#ai-03), [AGT-04](controls-catalog.md#agt-04) |
| A.5.18 | Access rights | [IAM-06](controls-catalog.md#iam-06), [IAM-08](controls-catalog.md#iam-08), [IAM-10](controls-catalog.md#iam-10), [AGT-04](controls-catalog.md#agt-04) |
| A.5.19 | Information security in supplier relationships | [AI-06](controls-catalog.md#ai-06), [AGT-06](controls-catalog.md#agt-06), [GOV-04](controls-catalog.md#gov-04) |
| A.5.20 | Addressing information security within supplier agreements | [GOV-04](controls-catalog.md#gov-04) |
| A.5.21 | Managing information security in the ICT supply chain | [APP-04](controls-catalog.md#app-04), [AI-06](controls-catalog.md#ai-06), [AGT-06](controls-catalog.md#agt-06) |
| A.5.22 | Monitoring, review and change management of supplier services | [GOV-04](controls-catalog.md#gov-04) |
| A.5.23 | Information security for use of cloud services | [NET-05](controls-catalog.md#net-05), [GOV-04](controls-catalog.md#gov-04) |
| A.5.24 | Information security incident management planning and preparation | [LOG-04](controls-catalog.md#log-04), [GOV-05](controls-catalog.md#gov-05) |
| A.5.25 | Assessment and decision on information security events | [LOG-03](controls-catalog.md#log-03), [LOG-04](controls-catalog.md#log-04) |
| A.5.26 | Response to information security incidents | [LOG-04](controls-catalog.md#log-04), [AGT-13](controls-catalog.md#agt-13), [GOV-05](controls-catalog.md#gov-05) |
| A.5.27 | Learning from information security incidents | [LOG-04](controls-catalog.md#log-04), [GOV-05](controls-catalog.md#gov-05) |
| A.5.28 | Collection of evidence | [LOG-02](controls-catalog.md#log-02), [LOG-04](controls-catalog.md#log-04) |
| A.5.30 | ICT readiness for business continuity | [DAT-09](controls-catalog.md#dat-09) |
| A.5.33 | Protection of records | [LOG-02](controls-catalog.md#log-02) |
| A.5.34 | Privacy and protection of PII | [DAT-01](controls-catalog.md#dat-01), [DAT-07](controls-catalog.md#dat-07) |
| A.8.2 | Privileged access rights | [IAM-08](controls-catalog.md#iam-08), [AGT-04](controls-catalog.md#agt-04) |
| A.8.3 | Information access restriction | [IAM-07](controls-catalog.md#iam-07), [DAT-08](controls-catalog.md#dat-08), [AI-04](controls-catalog.md#ai-04), [AGT-05](controls-catalog.md#agt-05), [AGT-09](controls-catalog.md#agt-09) |
| A.8.5 | Secure authentication | [IAM-01](controls-catalog.md#iam-01), [IAM-02](controls-catalog.md#iam-02), [IAM-03](controls-catalog.md#iam-03), [IAM-04](controls-catalog.md#iam-04), [IAM-05](controls-catalog.md#iam-05), [IAM-06](controls-catalog.md#iam-06), [IAM-09](controls-catalog.md#iam-09), [AGT-03](controls-catalog.md#agt-03), [AGT-10](controls-catalog.md#agt-10) |
| A.8.6 | Capacity management | [NET-06](controls-catalog.md#net-06), [LOG-05](controls-catalog.md#log-05), [APP-08](controls-catalog.md#app-08), [AGT-14](controls-catalog.md#agt-14) |
| A.8.7 | Protection against malware | [APP-09](controls-catalog.md#app-09) |
| A.8.8 | Management of technical vulnerabilities | [APP-04](controls-catalog.md#app-04), [APP-05](controls-catalog.md#app-05) |
| A.8.9 | Configuration management | [APP-06](controls-catalog.md#app-06) |
| A.8.10 | Information deletion | [DAT-01](controls-catalog.md#dat-01) |
| A.8.11 | Data masking | [DAT-07](controls-catalog.md#dat-07) |
| A.8.12 | Data leakage prevention | [DAT-07](controls-catalog.md#dat-07) |
| A.8.13 | Information backup | [DAT-09](controls-catalog.md#dat-09) |
| A.8.15 | Logging | [LOG-01](controls-catalog.md#log-01), [LOG-02](controls-catalog.md#log-02), [AGT-11](controls-catalog.md#agt-11) |
| A.8.16 | Monitoring activities | [LOG-03](controls-catalog.md#log-03), [LOG-05](controls-catalog.md#log-05), [AGT-12](controls-catalog.md#agt-12) |
| A.8.17 | Clock synchronization | [LOG-01](controls-catalog.md#log-01) |
| A.8.20 | Networks security | [DAT-05](controls-catalog.md#dat-05), [NET-01](controls-catalog.md#net-01), [NET-02](controls-catalog.md#net-02), [NET-03](controls-catalog.md#net-03), [NET-04](controls-catalog.md#net-04), [NET-05](controls-catalog.md#net-05), [NET-06](controls-catalog.md#net-06) |
| A.8.21 | Security of network services | [NET-04](controls-catalog.md#net-04), [NET-05](controls-catalog.md#net-05) |
| A.8.22 | Segregation of networks | [NET-01](controls-catalog.md#net-01) |
| A.8.23 | Web filtering | [NET-02](controls-catalog.md#net-02) |
| A.8.24 | Use of cryptography | [IAM-03](controls-catalog.md#iam-03), [IAM-05](controls-catalog.md#iam-05), [DAT-02](controls-catalog.md#dat-02), [DAT-03](controls-catalog.md#dat-03), [DAT-04](controls-catalog.md#dat-04), [DAT-05](controls-catalog.md#dat-05), [NET-03](controls-catalog.md#net-03), [NET-04](controls-catalog.md#net-04) |
| A.8.25 | Secure development life cycle | [APP-01](controls-catalog.md#app-01) |
| A.8.26 | Application security requirements | [APP-01](controls-catalog.md#app-01), [APP-02](controls-catalog.md#app-02), [APP-03](controls-catalog.md#app-03), [AI-01](controls-catalog.md#ai-01) |
| A.8.27 | Secure system architecture and engineering principles | [APP-01](controls-catalog.md#app-01), [AGT-02](controls-catalog.md#agt-02), [AGT-08](controls-catalog.md#agt-08) |
| A.8.28 | Secure coding | [APP-02](controls-catalog.md#app-02), [APP-03](controls-catalog.md#app-03), [APP-07](controls-catalog.md#app-07), [APP-09](controls-catalog.md#app-09), [APP-10](controls-catalog.md#app-10), [AI-02](controls-catalog.md#ai-02) |
| A.8.29 | Security testing in development and acceptance | [APP-05](controls-catalog.md#app-05), [AI-07](controls-catalog.md#ai-07) |
| A.8.32 | Change management | [GOV-03](controls-catalog.md#gov-03) |

**Coverage:** 46 of 46 listed references are addressed by at least one catalogue control.

<a id="owasp"></a>

## OWASP

### OWASP Top 10:2025

| Code | Risk | Controls |
|------|------|----------|
| A01:2025 | Broken Access Control | [IAM-06](controls-catalog.md#iam-06), [IAM-07](controls-catalog.md#iam-07), [IAM-08](controls-catalog.md#iam-08), [DAT-08](controls-catalog.md#dat-08), [NET-02](controls-catalog.md#net-02), [APP-10](controls-catalog.md#app-10) |
| A02:2025 | Security Misconfiguration | [APP-05](controls-catalog.md#app-05), [APP-06](controls-catalog.md#app-06) |
| A03:2025 | Software Supply Chain Failures | [APP-04](controls-catalog.md#app-04), [APP-05](controls-catalog.md#app-05) |
| A04:2025 | Cryptographic Failures | [IAM-03](controls-catalog.md#iam-03), [IAM-05](controls-catalog.md#iam-05), [DAT-02](controls-catalog.md#dat-02), [DAT-03](controls-catalog.md#dat-03), [DAT-04](controls-catalog.md#dat-04), [DAT-05](controls-catalog.md#dat-05), [DAT-06](controls-catalog.md#dat-06) |
| A05:2025 | Injection | [APP-02](controls-catalog.md#app-02), [APP-03](controls-catalog.md#app-03), [APP-05](controls-catalog.md#app-05), [APP-09](controls-catalog.md#app-09) |
| A06:2025 | Insecure Design | [APP-01](controls-catalog.md#app-01) |
| A07:2025 | Authentication Failures | [IAM-01](controls-catalog.md#iam-01), [IAM-02](controls-catalog.md#iam-02), [IAM-03](controls-catalog.md#iam-03), [IAM-04](controls-catalog.md#iam-04), [IAM-05](controls-catalog.md#iam-05), [IAM-06](controls-catalog.md#iam-06), [IAM-09](controls-catalog.md#iam-09), [DAT-05](controls-catalog.md#dat-05) |
| A08:2025 | Software or Data Integrity Failures | [IAM-05](controls-catalog.md#iam-05), [APP-04](controls-catalog.md#app-04) |
| A09:2025 | Security Logging and Alerting Failures | [LOG-01](controls-catalog.md#log-01), [LOG-02](controls-catalog.md#log-02), [LOG-03](controls-catalog.md#log-03) |
| A10:2025 | Mishandling of Exceptional Conditions | [APP-07](controls-catalog.md#app-07) |

### OWASP Top 10 for LLM Applications (2025)

| Code | Risk | Controls |
|------|------|----------|
| LLM01 | Prompt Injection | [APP-09](controls-catalog.md#app-09), [AI-01](controls-catalog.md#ai-01), [AI-07](controls-catalog.md#ai-07) |
| LLM02 | Sensitive Information Disclosure | [DAT-01](controls-catalog.md#dat-01), [DAT-06](controls-catalog.md#dat-06), [DAT-07](controls-catalog.md#dat-07), [DAT-08](controls-catalog.md#dat-08), [NET-05](controls-catalog.md#net-05), [AI-03](controls-catalog.md#ai-03), [AI-04](controls-catalog.md#ai-04) |
| LLM03 | Supply Chain | [APP-04](controls-catalog.md#app-04), [AI-06](controls-catalog.md#ai-06), [AGT-06](controls-catalog.md#agt-06), [GOV-04](controls-catalog.md#gov-04) |
| LLM04 | Data and Model Poisoning | [APP-09](controls-catalog.md#app-09), [AI-04](controls-catalog.md#ai-04), [AI-05](controls-catalog.md#ai-05), [AGT-09](controls-catalog.md#agt-09) |
| LLM05 | Improper Output Handling | [APP-02](controls-catalog.md#app-02), [APP-03](controls-catalog.md#app-03), [AI-02](controls-catalog.md#ai-02), [AGT-08](controls-catalog.md#agt-08) |
| LLM06 | Excessive Agency | [AGT-02](controls-catalog.md#agt-02), [AGT-04](controls-catalog.md#agt-04), [AGT-05](controls-catalog.md#agt-05), [AGT-07](controls-catalog.md#agt-07) |
| LLM07 | System Prompt Leakage | [DAT-06](controls-catalog.md#dat-06), [AI-03](controls-catalog.md#ai-03) |
| LLM08 | Vector and Embedding Weaknesses | [DAT-08](controls-catalog.md#dat-08), [AI-04](controls-catalog.md#ai-04), [AGT-09](controls-catalog.md#agt-09) |
| LLM09 | Misinformation | [AI-08](controls-catalog.md#ai-08), [AI-09](controls-catalog.md#ai-09), [GOV-06](controls-catalog.md#gov-06) |
| LLM10 | Unbounded Consumption | [NET-05](controls-catalog.md#net-05), [NET-06](controls-catalog.md#net-06), [LOG-05](controls-catalog.md#log-05), [APP-08](controls-catalog.md#app-08), [AGT-14](controls-catalog.md#agt-14) |

### OWASP Top 10 for Agentic Applications (2026)

| Code | Risk | Controls |
|------|------|----------|
| ASI01 | Agent Goal Hijack | [AI-01](controls-catalog.md#ai-01), [AI-07](controls-catalog.md#ai-07), [AGT-12](controls-catalog.md#agt-12) |
| ASI02 | Tool Misuse and Exploitation | [NET-02](controls-catalog.md#net-02), [AGT-02](controls-catalog.md#agt-02), [AGT-04](controls-catalog.md#agt-04), [AGT-05](controls-catalog.md#agt-05), [AGT-07](controls-catalog.md#agt-07), [AGT-12](controls-catalog.md#agt-12) |
| ASI03 | Identity and Privilege Abuse | [AGT-01](controls-catalog.md#agt-01), [AGT-03](controls-catalog.md#agt-03), [AGT-04](controls-catalog.md#agt-04) |
| ASI04 | Agentic Supply Chain Vulnerabilities | [APP-04](controls-catalog.md#app-04), [AI-06](controls-catalog.md#ai-06), [AGT-06](controls-catalog.md#agt-06) |
| ASI05 | Unexpected Code Execution | [AI-02](controls-catalog.md#ai-02), [AGT-08](controls-catalog.md#agt-08) |
| ASI06 | Memory and Context Poisoning | [DAT-08](controls-catalog.md#dat-08), [AI-04](controls-catalog.md#ai-04), [AGT-09](controls-catalog.md#agt-09) |
| ASI07 | Insecure Inter-Agent Communication | [AGT-03](controls-catalog.md#agt-03), [AGT-10](controls-catalog.md#agt-10) |
| ASI08 | Cascading Failures | [AGT-13](controls-catalog.md#agt-13), [AGT-14](controls-catalog.md#agt-14) |
| ASI09 | Human-Agent Trust Exploitation | [AI-08](controls-catalog.md#ai-08), [AI-09](controls-catalog.md#ai-09), [AGT-07](controls-catalog.md#agt-07), [AGT-11](controls-catalog.md#agt-11) |
| ASI10 | Rogue Agents | [NET-02](controls-catalog.md#net-02), [AGT-01](controls-catalog.md#agt-01), [AGT-02](controls-catalog.md#agt-02), [AGT-03](controls-catalog.md#agt-03), [AGT-10](controls-catalog.md#agt-10), [AGT-11](controls-catalog.md#agt-11), [AGT-12](controls-catalog.md#agt-12), [AGT-13](controls-catalog.md#agt-13) |

<a id="stride"></a>

## STRIDE

| Category | Controls |
|----------|----------|
| Spoofing | [IAM-01](controls-catalog.md#iam-01), [IAM-02](controls-catalog.md#iam-02), [IAM-03](controls-catalog.md#iam-03), [IAM-04](controls-catalog.md#iam-04), [IAM-05](controls-catalog.md#iam-05), [IAM-06](controls-catalog.md#iam-06), [IAM-09](controls-catalog.md#iam-09), [IAM-10](controls-catalog.md#iam-10), [DAT-04](controls-catalog.md#dat-04), [DAT-05](controls-catalog.md#dat-05), [DAT-06](controls-catalog.md#dat-06), [NET-04](controls-catalog.md#net-04), [NET-05](controls-catalog.md#net-05), [APP-01](controls-catalog.md#app-01), [AI-01](controls-catalog.md#ai-01), [AI-07](controls-catalog.md#ai-07), [AI-09](controls-catalog.md#ai-09), [AGT-01](controls-catalog.md#agt-01), [AGT-03](controls-catalog.md#agt-03), [AGT-04](controls-catalog.md#agt-04), [AGT-06](controls-catalog.md#agt-06), [AGT-10](controls-catalog.md#agt-10) |
| Tampering | [IAM-03](controls-catalog.md#iam-03), [IAM-04](controls-catalog.md#iam-04), [IAM-05](controls-catalog.md#iam-05), [IAM-07](controls-catalog.md#iam-07), [DAT-02](controls-catalog.md#dat-02), [DAT-03](controls-catalog.md#dat-03), [DAT-04](controls-catalog.md#dat-04), [DAT-05](controls-catalog.md#dat-05), [DAT-09](controls-catalog.md#dat-09), [NET-01](controls-catalog.md#net-01), [NET-03](controls-catalog.md#net-03), [NET-04](controls-catalog.md#net-04), [NET-05](controls-catalog.md#net-05), [NET-06](controls-catalog.md#net-06), [LOG-02](controls-catalog.md#log-02), [APP-01](controls-catalog.md#app-01), [APP-02](controls-catalog.md#app-02), [APP-03](controls-catalog.md#app-03), [APP-04](controls-catalog.md#app-04), [APP-05](controls-catalog.md#app-05), [APP-06](controls-catalog.md#app-06), [APP-09](controls-catalog.md#app-09), [AI-01](controls-catalog.md#ai-01), [AI-02](controls-catalog.md#ai-02), [AI-04](controls-catalog.md#ai-04), [AI-05](controls-catalog.md#ai-05), [AI-06](controls-catalog.md#ai-06), [AI-07](controls-catalog.md#ai-07), [AI-08](controls-catalog.md#ai-08), [AGT-05](controls-catalog.md#agt-05), [AGT-06](controls-catalog.md#agt-06), [AGT-07](controls-catalog.md#agt-07), [AGT-08](controls-catalog.md#agt-08), [AGT-09](controls-catalog.md#agt-09), [AGT-10](controls-catalog.md#agt-10) |
| Repudiation | [IAM-01](controls-catalog.md#iam-01), [IAM-08](controls-catalog.md#iam-08), [LOG-01](controls-catalog.md#log-01), [LOG-02](controls-catalog.md#log-02), [LOG-03](controls-catalog.md#log-03), [LOG-04](controls-catalog.md#log-04), [APP-01](controls-catalog.md#app-01), [AI-07](controls-catalog.md#ai-07), [AI-08](controls-catalog.md#ai-08), [AI-09](controls-catalog.md#ai-09), [AGT-01](controls-catalog.md#agt-01), [AGT-03](controls-catalog.md#agt-03), [AGT-07](controls-catalog.md#agt-07), [AGT-10](controls-catalog.md#agt-10), [AGT-11](controls-catalog.md#agt-11), [AGT-12](controls-catalog.md#agt-12), [AGT-13](controls-catalog.md#agt-13), [GOV-03](controls-catalog.md#gov-03), [GOV-05](controls-catalog.md#gov-05), [GOV-06](controls-catalog.md#gov-06) |
| Information Disclosure | [IAM-05](controls-catalog.md#iam-05), [IAM-06](controls-catalog.md#iam-06), [IAM-07](controls-catalog.md#iam-07), [DAT-01](controls-catalog.md#dat-01), [DAT-02](controls-catalog.md#dat-02), [DAT-03](controls-catalog.md#dat-03), [DAT-04](controls-catalog.md#dat-04), [DAT-05](controls-catalog.md#dat-05), [DAT-06](controls-catalog.md#dat-06), [DAT-07](controls-catalog.md#dat-07), [DAT-08](controls-catalog.md#dat-08), [NET-01](controls-catalog.md#net-01), [NET-02](controls-catalog.md#net-02), [NET-03](controls-catalog.md#net-03), [NET-04](controls-catalog.md#net-04), [NET-05](controls-catalog.md#net-05), [LOG-03](controls-catalog.md#log-03), [APP-01](controls-catalog.md#app-01), [APP-02](controls-catalog.md#app-02), [APP-03](controls-catalog.md#app-03), [APP-05](controls-catalog.md#app-05), [APP-06](controls-catalog.md#app-06), [APP-07](controls-catalog.md#app-07), [APP-10](controls-catalog.md#app-10), [AI-03](controls-catalog.md#ai-03), [AI-04](controls-catalog.md#ai-04), [AI-05](controls-catalog.md#ai-05), [AI-07](controls-catalog.md#ai-07), [AI-08](controls-catalog.md#ai-08), [AGT-04](controls-catalog.md#agt-04), [AGT-09](controls-catalog.md#agt-09), [AGT-12](controls-catalog.md#agt-12), [GOV-04](controls-catalog.md#gov-04) |
| Denial of Service | [DAT-09](controls-catalog.md#dat-09), [NET-06](controls-catalog.md#net-06), [LOG-03](controls-catalog.md#log-03), [LOG-04](controls-catalog.md#log-04), [LOG-05](controls-catalog.md#log-05), [APP-01](controls-catalog.md#app-01), [APP-07](controls-catalog.md#app-07), [APP-08](controls-catalog.md#app-08), [APP-09](controls-catalog.md#app-09), [AI-07](controls-catalog.md#ai-07), [AGT-08](controls-catalog.md#agt-08), [AGT-13](controls-catalog.md#agt-13), [AGT-14](controls-catalog.md#agt-14) |
| Elevation of Privilege | [IAM-02](controls-catalog.md#iam-02), [IAM-04](controls-catalog.md#iam-04), [IAM-05](controls-catalog.md#iam-05), [IAM-06](controls-catalog.md#iam-06), [IAM-07](controls-catalog.md#iam-07), [IAM-08](controls-catalog.md#iam-08), [IAM-09](controls-catalog.md#iam-09), [IAM-10](controls-catalog.md#iam-10), [DAT-03](controls-catalog.md#dat-03), [DAT-06](controls-catalog.md#dat-06), [DAT-08](controls-catalog.md#dat-08), [NET-01](controls-catalog.md#net-01), [NET-02](controls-catalog.md#net-02), [LOG-03](controls-catalog.md#log-03), [APP-01](controls-catalog.md#app-01), [APP-02](controls-catalog.md#app-02), [APP-03](controls-catalog.md#app-03), [APP-04](controls-catalog.md#app-04), [APP-05](controls-catalog.md#app-05), [APP-06](controls-catalog.md#app-06), [APP-07](controls-catalog.md#app-07), [APP-09](controls-catalog.md#app-09), [APP-10](controls-catalog.md#app-10), [AI-01](controls-catalog.md#ai-01), [AI-02](controls-catalog.md#ai-02), [AI-04](controls-catalog.md#ai-04), [AI-06](controls-catalog.md#ai-06), [AI-07](controls-catalog.md#ai-07), [AGT-01](controls-catalog.md#agt-01), [AGT-02](controls-catalog.md#agt-02), [AGT-04](controls-catalog.md#agt-04), [AGT-05](controls-catalog.md#agt-05), [AGT-06](controls-catalog.md#agt-06), [AGT-07](controls-catalog.md#agt-07), [AGT-08](controls-catalog.md#agt-08), [AGT-10](controls-catalog.md#agt-10), [AGT-12](controls-catalog.md#agt-12), [AGT-13](controls-catalog.md#agt-13) |
