# Changelog

All notable changes to STRIDE-GPT. Releases are cut from tags (see [RELEASING.md](RELEASING.md)); the newest release is at the top.

## Unreleased

- **Security control catalogue with compliance mapping**: A packaged catalogue of 69 controls in eight domains: identity and access management (OIDC, phishing-resistant MFA, X.509 PKI, SPIFFE workload identity, JWT validation, OAuth 2.x per RFC 9700); data protection (encryption at rest with customer-managed keys, TLS 1.3, mutual TLS, key and secrets management); network security (segmentation, egress control, MACsec, IPsec); logging, monitoring and response; application security (OWASP Top 10:2025 and ASVS 5.0); AI and LLM security; agentic AI; and AI governance. Each control is mapped to AIUC-1, ISO/IEC 42001:2023, the EU AI Act (Regulation (EU) 2024/1689 as amended by Regulation (EU) 2026/1744) and ISO/IEC 27001:2022. The model only chooses control IDs; every framework reference in a report is looked up from the catalogue, so a report cannot cite a clause the model made up. The catalogue lives in `stride_gpt/core/controls/catalog.toml`, and the loader rejects any mapping to a reference that isn't in the framework's registry.
- **`security_controls` and `ai_controls` reference cards**: Two new progressive-disclosure cards, generated from the catalogue by `scripts/build_control_catalog.py`, add a `CONTROLS` field to each threat. `report_threat` takes a `controls` argument constrained to catalogue IDs. IDs the model invents are not recorded, and the tool result names them so the model can correct itself. Synthesis and `/quick` output are filtered the same way. A test fails if the cards or the generated docs drift from the catalogue.
- **Controls and compliance in every report format**: Markdown and HTML reports gain a Controls column and a *Controls & Compliance Mapping* section listing the recommended controls and the requirements of each framework they address. JSON reports carry a `compliance` block, and SARIF results carry `controls` and `frameworks` properties for filtering in code-scanning tools. AI frameworks are shown only when the report concerns an AI system (OWASP LLM/ASI codes, an insider-threat category, an ATLAS technique, or an AI control); a plain web application maps to ISO/IEC 27001 alone.
- **`stride-gpt controls` command**: Browse the catalogue (`stride-gpt controls`, `-d AGT`), read one control in full (`stride-gpt controls IAM-05`), view a framework crosswalk (`--framework eu-ai-act`), or export a saved report's mapping for GRC tools (`--report report.json -o mapping.csv`, also `.json` and `.md`). CSV cells are defused against spreadsheet formula injection, since scenario text is model output.
- **Web UI**: A *Map threats to security controls and compliance frameworks* option (on by default) adds the catalogue to the threat-model prompt. A new **Compliance** tab shows the mapping with Markdown, CSV and JSON downloads. The threat table now uses the shared renderer, so the web UI also shows the Insider Category, MITRE ATT&CK and Controls columns it previously dropped, and the Mitigations tab cites the control IDs each threat lists.
- **Documentation**: The README is restructured around a quick start and a docs index, and release history moves to this file. New guides cover the [architecture](docs/architecture.md), [controls and compliance mapping](docs/controls-and-compliance.md), [agentic AI controls](docs/agentic-ai-controls.md) and [deployment hardening](docs/deployment-hardening.md), alongside the generated [control catalogue](docs/controls-catalog.md) and [framework crosswalks](docs/framework-crosswalks.md). A [contributing guide](CONTRIBUTING.md) is added.
- **Fixes**: The Compose health check called `curl`, which the UI image dropped in 0.17, so the container could never report healthy; it now uses Python like the image's own `HEALTHCHECK`. Compose no longer adds the `NET_BIND_SERVICE` capability, which port 8501 doesn't need. The `/quick` system prompt no longer says a plain web application needs "none of these cards" while advertising MITRE ATT&CK for almost any application, and both system prompts stop calling the card list "the three listed above" when it names more.

## 0.20

- **Resume an interrupted analysis** (closes #197): `analyze` now checkpoints the approved plan and each subsystem finding as it completes, next to the `-o` report. `--resume <checkpoint>` reuses the subsystems that finished and reruns the rest, then runs synthesis and the data flow diagram as usual. Resume refuses when the target's git SHA or the config hash no longer match, naming which changed, so stale findings can't be stitched into a run of different code. A dirty working tree or a missing git SHA refuses unless `--force`; a changed SHA refuses even with it. The run manifest records which subsystems were reused and which were rerun.
- **Threats cite verified evidence** (closes #195): Each threat is now reported through a tool call carrying the code it came from, and every quoted snippet is checked against the file on disk before the threat is recorded. SARIF locations point at the file and line range the evidence was found at, rather than giving every threat in a subsystem the same three files, and `files_analyzed` reflects what the agent actually read rather than what it claimed to.
- **Every subsystem records why it stopped** (closes #196): A `SubsystemFinding` now carries an `outcome` — `completed`, `budget_exhausted`, `parse_failed`, `error`, or `skipped` — so a subsystem that crashed is no longer indistinguishable from one that was analysed and found nothing. Findings always match the plan: subsystems the run budget never reached are recorded as `skipped` rather than dropped. `run_summary.status` is derived from those outcomes, so a run where subsystems crashed is reported as `partial` instead of `completed`, and a clean subsystem with zero threats no longer makes the console print "Analysis partially complete". Failures are classified from the exception type (`context_overflow`, `rate_limited`, `auth`, `provider_error`) rather than by searching the error text, and the markdown and HTML reports show failed and skipped subsystems explicitly. Findings files written before this change still load, treated as `completed`.
- **Token usage recorded per phase and per subsystem** (#198): Prompt and completion tokens are read off each provider response and aggregated per phase (planning, exploration, compression, synthesis, DFD), per subsystem, and as a run total. The console summary gains a token line and `<stem>.run.json` gains `token_usage_total`, `token_usage_by_phase` and `token_usage_by_subsystem`. "Unknown" stays distinct from zero: some providers never report usage, so an all-zero reading records as unavailable rather than free. These are token counts, not costs: cache hit and miss tokens are not yet split out (#225), so a provider that serves most of a conversation from its prefix cache bills well below what the totals imply.
- **The planner represents every directory it found** (#175, closes #180): The key-file sample sent to the planner was a flat alphabetical slice, so one early-sorting directory could consume the whole budget and a later-sorting service reached the planner with no file-level signal at all. On OWASP crAPI that dropped two of six services from the plan entirely while the run still reported complete. The sample now round-robins across the whole directory tree, at any depth, and its header says it is a sample rather than reporting the total over a silently truncated list. `search_files`' truncation marker is no longer mixed into that list as if it were a file.
- **`read_file` pages by line range** (closes #194): `read_file` takes optional 1-based `start_line` and `end_line` arguments and returns numbered lines under a header giving the total line count, the exact range shown, and whether the byte cap cut it short. Previously it returned the first 50 KB and nothing more, so the agent could not read past that point and had no line numbers to cite. When output is truncated, a hint gives the line to request next.
- **OpenRouter as a model provider** (#221): Routes through LiteLLM's `openrouter/` prefix, authenticated with `OPENROUTER_API_KEY`, with a shortlist of six tool-capable models and any other slug available through the wizard's Custom option. CLI only for now. Also fixed: `--worker-model` naming a provider your saved config doesn't know about resolved the model from the flag but the API key from the config file, so the request could carry the wrong provider's secret (#222).
- **Model registry refreshed** (#223): Current lineups for OpenAI, Anthropic, DeepSeek, Mistral, Groq, Google and OpenRouter, with retired models dropped. `supports_thinking` now tracks which models actually accept the legacy extended-thinking parameter, since Claude 4.7 and later reject it, and the Streamlit thinking checkbox follows that flag rather than the provider.
- **Security: the agent's file tools can no longer reach version-control metadata** (#191, #190): `read_file`, `grep_content` and `list_directory` refuse any path resolving inside `.git`, `.hg` or `.svn`, directly or through a committed symlink. `actions/checkout` writes the job token into `.git/config`, and some clones embed a token in the remote URL, so analysing a CI checkout put credentials within reach of a model-driven read. `grep_content` also checked only its starting path before reading everything `os.walk` returned; it now applies the same resolved-path check to each file, matching `read_file`. `list_directory` no longer follows symlinks out of the sandbox when reporting type and size.
- **Malformed model output can no longer destroy a run's intermediates** (closes #208): A null byte in a planner-supplied file path crashed path redaction, which runs while persisting `plan.json`, `findings.json` and `run.json` — after every LLM call had been paid for. Redaction is now total, and an unresolvable path is still redacted rather than written out verbatim, so a home directory can't leak into a manifest that goes to git or a ticket. Genuine disk and serialisation failures still fail the run loudly.
- **Supply chain and scan hygiene** (#176, #177): Cleared 22 Dependabot alerts by updating gitpython, aiohttp and cryptography through the lockfile, cut Trivy base-image noise that was burying actionable findings, and cleared the remaining 18 CodeQL code-quality findings. Scheduled secret scanning no longer fails on model identifiers, and the CI security summary reports icons that follow the job result.

## 0.19

- **`--version` flag** (#161): `stride-gpt --version` now prints the installed version and exits, and the interactive TUI banner shows the running version so you can confirm what you're on at a glance.
- **Dependency management consolidated onto uv** (closes #155): `uv.lock` is now the single source of truth for every dependency. The duplicated `requirements.txt` files are retired; the Docker UI image and the security-scan workflow install from `uv.lock` via `uv export`, so what ships and what gets scanned can no longer drift from what's locked. No change for `pip install stride-gpt` users.
- **Documentation**: Added a sample threat-model markdown output (#151) and an interactive REPL cheat sheet (#163) to the README.

## 0.18

- **Embedded draw.io diagram editor** (#132, #138): The Streamlit Threat Model tab now embeds the [diagrams.net](https://www.diagrams.net/) editor so you can sketch an architecture diagram in-app; on save the diagram XML is parsed (components, connections, trust boundaries) and folded into the threat-model prompt. GitHub analysis, image upload, the diagram editor, and an AI-assisted guided builder are unified into one tabbed *"describe your application"* section over a single description canvas, so the optional inputs no longer crowd out the primary description field. The guided builder now calls the selected model to draft a description and suggest missing security-relevant details, replacing the previous static template and coverage checks. For self-hosted or air-gapped deployments the editor host is configurable via `STRIDE_GPT_DRAWIO_URL` (defaults to `embed.diagrams.net`), the iframe `postMessage` origin is scoped to it, and untrusted diagram XML is parsed with `defusedxml`.
- **DeepSeek provider support** (closes #133): DeepSeek is now a first-class model provider in both the CLI setup wizard and the Streamlit UI, offering `deepseek-v4-pro` and `deepseek-v4-flash`. Calls route through LiteLLM's native `deepseek/` integration (hosted endpoint, no custom base URL needed); set your key via `DEEPSEEK_API_KEY`.
- **Data Flow Diagram support** (closes #56): New "Data Flow Diagram" tab in the Streamlit UI generates DFDs from the application description, parses uploaded DFD images via vision-capable models, and renders an editable Mermaid source pane with a live preview. Ticking *"Use this DFD for the threat model"* stores the confirmed diagram in session state and splices it into subsequent Threat Model and Attack Tree prompts as the authoritative system model — closing the description → DFD → review → refined threat model loop the issue asks for. The CLI's `/analyze` agent also produces a system-level DFD after synthesis, rendered as a Mermaid block in the markdown report, carried in the JSON `data_flow_diagram` field, and shown in the HTML view via a CDN-loaded Mermaid runtime. DFD generation is wrapped so a bad diagram never fails a good report.
- **Graceful GitHub repo analysis errors** (closes #92): The Streamlit UI now catches GitHub API failures during repository analysis instead of surfacing a raw stack trace, with actionable messages for 404 (including fine-grained PAT scoping, which 404s even public repos), 401, 403/rate-limit, and network errors. Repo URLs are normalised (trailing `/` and `.git` suffix stripped) before parsing so `.../repo/` and `.../repo.git` no longer 404 spuriously.
- **Structured intermediates alongside reports** (closes #122): When `-o <path>` is passed to `/analyze` or `/quick`, JSON siblings are written next to the report — `<stem>.plan.json` (the `AnalysisPlan`), `<stem>.findings.json` (subsystem findings, cross-cutting threats, and the data flow diagram), and `<stem>.run.json` (a `RunManifest` recording models, config hash, version, timing, which reference cards actually loaded, and a `run_summary` marking whether the run completed or a call cap truncated it). Manifests exclude API keys and endpoints and redact filesystem paths, so they're safe to commit or attach to a ticket. The `-f` format flag governs only the report artefact; siblings are always JSON.
- **Comma-separated MITRE ATT&CK recovery** (closes #134): When a worker model returns `MITRE_ATTACK` as a comma-separated string (e.g. `"T1190, T1059, AML.T0053"`) instead of the canonical list shape, the technique IDs are now recovered rather than dropped. Previously the markdown/HTML reports showed the "MITRE ATT&CK" column but left every cell blank, and the SARIF export lost the IDs entirely. All renderers (markdown, HTML pills, SARIF) and the column-visibility check now route through a single normaliser, and free-form prose that isn't a technique ID is filtered out so the column never fills with false positives.
- **0.18.1 patch** (closes #159): Fixed LM Studio calls failing with `The api_key client option must be set` when no cloud provider key was present in the environment. LM Studio routes through LiteLLM's `openai/` prefix, and the OpenAI SDK refuses to build a client without a key even when `api_base` points at localhost, so the CLI now passes a placeholder for providers that don't authenticate. Relatedly, the worker tier's last-resort environment scan no longer applies to those providers: a configured `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` was previously sent to whatever host `api_base` named, which both masked this bug and put a real key on the wire. If you use LM Studio and have such a key set, it is no longer transmitted to your endpoint.

## 0.17

- **MITRE ATT&CK and ATLAS integration** (closes #36): Threats emitted by `/analyze` and `/quick` can now carry standardized adversary technique IDs from MITRE ATT&CK Enterprise (v17.1) and MITRE ATLAS (2026.05). Two new progressive-disclosure reference cards (`mitre_enterprise`, `mitre_atlas`) instruct the agent to use only the catalogued IDs and names, eliminating ID hallucination. Cards are regenerated from upstream STIX/YAML via `scripts/refresh_mitre_cards.py` rather than written from model recall. Techniques render as a `MITRE ATT&CK` column in markdown tables, clickable sky-tinted pills in HTML, and `properties.mitre_attack` arrays in SARIF.
- **HTML report companion**: `/analyze` and `/quick` now emit a self-contained browser-viewable HTML report alongside the markdown / JSON / SARIF outputs, suitable for sharing with stakeholders.
- **Anthropic Claude Opus 4.8**: Added support for `claude-opus-4-8`, Anthropic's newest frontier-tier model, alongside the existing Opus 4.7. Either can be selected as the architect or worker model.
- **UI image consolidation**: The dual-namespace Docker setup (`mrwadams/stridegpt-ui`) is gone; the Streamlit web UI now lives at `mrwadams/stridegpt` only. CLI users should `pip install stride-gpt` rather than pulling a container.
- **Dependency hygiene**: Dropped the unused `mistralai` package (Mistral access already flows through LiteLLM). Refreshed the `python:3.12-slim` base for the UI image and dropped `curl`, clearing 21 medium/high CVE alerts across PRs #113–#115.
- **Code quality cleanup**: Cleared CodeQL note alerts (unused imports, bare `except`, dead code) (#116).

## 0.16

- **Standalone CLI**: First release of STRIDE-GPT as a `pip install stride-gpt` CLI, separated from the legacy Streamlit web UI. Two main commands: `/analyze` (autonomous agentic codebase analysis with a planner, per-subsystem tool-using agent loops, and a cross-cutting synthesis pass) and `/quick` (single-shot threat model from a written application description).
- **Progressive-disclosure reference cards**: `genai` (OWASP LLM Top 10), `agentic` (OWASP ASI Top 10), and `insider_threat` cards self-describe via YAML frontmatter; the agent discovers them via `list_references` and pulls bodies via `load_reference`.
- **Two-tier model routing**: Architect + worker model split for cost-efficient analysis, with frontier-class models reserved for planning and synthesis.
- **Interactive REPL**: Full-featured terminal experience with tab completion, history, real-time progress, and a status line.
- **Multi-format output**: Markdown, JSON, and SARIF (imports into GitHub, GitLab, Azure DevOps, IDEs).
- **0.16.1 patch**: Raised the LiteLLM logger to ERROR in `stride_gpt/__init__.py` so the Bedrock/SageMaker pre-load warnings don't appear on fresh installs that lack `botocore`.

  <summary>Click to view release notes for earlier versions (0.15 and older).</summary>

## 0.15

- **Agentic AI Application Support**: Added comprehensive support for threat modeling agentic AI systems with OWASP Top 10 for Agentic Applications (ASI01-ASI10) integration. Simply select "Agentic AI application" and describe your system - the LLM automatically detects architectural patterns and applies relevant threat categories. Each ASI risk is mapped to the appropriate STRIDE category for consistent threat analysis.

- **Generative AI Application Support**: Added support for threat modeling GenAI applications with OWASP LLM Top 10 (LLM01-LLM10) integration. Select "Generative AI application" and describe your system to receive tailored LLM-specific threat analysis. Agentic AI applications include both LLM and ASI risk categories for comprehensive coverage.

- **MAESTRO-Inspired Architectural Pattern Detection**: Enhanced agentic threat analysis with automatic detection of architectural patterns from application descriptions, inspired by the [Cloud Security Alliance MAESTRO framework](https://cloudsecurityalliance.org/blog/2025/02/06/agentic-ai-threat-modeling-framework-maestro). The LLM now identifies and applies pattern-specific threats for:
  - **RAG/Retrieval Systems**: Vector store poisoning, embedding manipulation, cross-tenant leakage
  - **Multi-Agent Systems**: Agent impersonation, inter-agent message tampering, cascading compromises
  - **Code Execution Environments**: Sandbox escape, container breakout, malicious code generation
  - **Tool/MCP Ecosystems**: Rogue tool providers, supply chain attacks, confused deputy vulnerabilities
  - **Persistent Memory**: Memory poisoning, cross-session leakage, state manipulation
  - **Autonomous Operations**: Rogue agent persistence, human oversight bypass, runaway loops

- **Cross-Layer Threat Analysis**: Threat models now include cross-component attack chains that show how compromise in one architectural layer can enable attacks on others (e.g., RAG poisoning → agent goal hijack → tool misuse → data exfiltration).

- **Enhanced Improvement Suggestions**: For agentic applications, improvement suggestions now prompt for specific architectural details such as agent framework, inter-agent communication protocols, sandbox mechanisms, and circuit breaker implementations.

- **OpenAI Model Updates**: Updated to GPT-5.2 series models (gpt-5.2, gpt-5.2-pro, gpt-5-mini, gpt-5-nano, gpt-5, gpt-4.1). Removed deprecated models (gpt-4o, gpt-4o-mini, o3, o3-mini, o4-mini).

- **Anthropic Claude 4.5 Models**: Updated to Claude 4.5 series (claude-sonnet-4-5, claude-haiku-4-5, claude-opus-4-5). Added "Enable Extended Thinking" checkbox for enhanced reasoning capabilities on any Claude model. Increased max tokens to 32k (standard) and 48k (thinking mode).

- **Google Gemini 3 Preview**: Added Gemini 3 preview models (gemini-3-pro-preview, gemini-3-flash-preview) alongside Gemini 2.5 models. Extended thinking mode support to Gemini 3 models.

- **Mistral Model Updates**: Updated to latest versioned Mistral models including Mistral Large 3, Medium 3.1, Small 3.2, Ministral 3 (8B/14B), and Magistral 1.2 (Medium/Small).

- **New Project Logo**: Refreshed branding with a cleaner, minimal shield + neural network design.

- **Bug Fix**: Fixed issue where threat model output would disappear after clicking the download button.

## 0.14.1

- **Security Infrastructure**: Added comprehensive automated security scanning and hardening including:
  - GitHub Actions workflows for Bandit (Python security), CodeQL (vulnerability detection), pip-audit (dependency scanning), Safety (package vulnerabilities), Gitleaks (secret detection), and Trivy (Docker image scanning)
  - SECURITY.md with vulnerability reporting process (48-hour acknowledgment SLA) and security best practices
  - Enhanced Docker configuration with security hardening, resource limits, and production-ready docker-compose.yml
  - Dependabot configuration for automated weekly dependency updates
  - Production-ready secrets management guidance (Docker Swarm secrets, cloud secret managers)
- **Enterprise Operationalization Guide**: Added comprehensive guide for customizing STRIDE-GPT with organizational context including security controls, compliance requirements, approved technology stacks, and deployment patterns for enterprise use.

## 0.14

- **GPT-5 Series Support**: Added comprehensive support for OpenAI's GPT-5 series models (gpt-5, gpt-5-mini, gpt-5-nano) across all threat modeling features. These advanced reasoning models provide enhanced analytical capabilities with proper token allocation for both internal reasoning and output generation.
- **Anthropic Claude 4 Integration**: Added support for Anthropic's latest Claude 4 models (claude-opus-4-1-20250805, claude-opus-4-20250514, and claude-sonnet-4-20250514) with enhanced capabilities.
- **GitHub Enterprise Support**: Added support for GitHub Enterprise repositories. The tool now automatically detects and configures the appropriate API endpoint based on the repository URL, making it easy to analyze repositories hosted on private GitHub Enterprise instances. (Thanks to @danielpops for the contribution!)
- **Enhanced Reasoning Model Integration**: Updated parameter handling to use `max_completion_tokens` instead of deprecated `max_tokens` for GPT-5 and other OpenAI reasoning models, ensuring compatibility with OpenAI's latest API requirements.
- **Improved DREAD Assessment Display**: Removed truncation limits in DREAD assessment scenario descriptions, allowing users to view complete threat scenarios in the risk assessment table instead of abbreviated "..." versions.
- **Security Updates**: Updated dependencies to address security vulnerabilities identified by Snyk, including updates to anyio, zipp, tornado, requests, and urllib3.
- **Mistral Model Updates**: Added support for Mistral's latest models including Magistral Medium/Small (reasoning models), Mistral Medium, and Ministral 8B.
- **Groq Model Updates**: Updated Groq model selection with OpenAI GPT-OSS models (120B, 20B), maintained Llama 3.3 70B and 3.1 8B, kept DeepSeek R1, and added Moonshot Kimi K2 and Qwen3 32B.
- **Google Gemini 2.5 GA Update**: Updated to use the General Availability versions of Gemini 2.5 models (Pro, Flash, Flash Lite) replacing the previous preview versions.
- **Support the Project**: Added a "Buy me a coffee" button in the sidebar to allow users to support the continued development and maintenance of STRIDE GPT.

## 0.13

- **New OpenAI Models**: Added support for OpenAI's latest models: gpt-4.1, o3, and o4-mini while maintaining support for o3-mini. These reasoning models provide detailed analytical capabilities.
- **Migrated to New Google GenAI SDK**: Completely migrated to the new Google GenAI SDK, removing all dependency on the deprecated Google Generative AI library. Refactored Gemini (Google AI) model integration across all modules for improved consistency and performance.
- **Enhanced Reasoning Model Support**: Expanded the reasoning framework to work with all of OpenAI's reasoning models (o1, o3, o3-mini, o4-mini) across all threat modeling features, including threat model generation, attack trees, mitigations, and DREAD assessments.
- **Increased Token Limits**: Updated token limits for new models to take advantage of their expanded contexts, particularly for gpt-4.1 which supports 1 million tokens and o4-mini which supports 200K tokens.
- **Enhanced Multi-Modal Support**: Image upload and analysis now works with more models, including Gemini 2.5, Claude 3, and Claude 4 models. Expanded support for analyzing various image formats across all vision-capable models.
- **Updated to Latest Gemini Preview Models**: Transitioned to use the latest versions of Gemini preview models for improved performance and capabilities.

## 0.12

- **Claude 3.7 Integration**: Added comprehensive support for Anthropic's Claude 3.7 models across all threat modeling features, including the innovative "thinking mode" that provides more detailed reasoning during analysis.
- **Improved GitHub Repository Analysis**: Significantly enhanced the GitHub repository analysis feature with intelligent file selection, better programming language support, and progress tracking during analysis.
- **GPT-4.5 Preview Support**: Added support for OpenAI's GPT-4.5 preview model with improved model selection guidance and descriptions.
- **Performance Optimizations**: Improved overall application performance with better token usage tracking and warning systems for approaching token limits.

## 0.11

- **LM Studio Server Support**: Added support for using LM Studio Server as a model provider, allowing users to run their own local LLMs with OpenAI-compatible API endpoints.
- **Google Gemini Attack Tree Support**: Added support for generating attack trees using Google Gemini models, expanding the available options for users.
- **New Model Support**: Added support for reasoning models (OpenAI's o1 and o3-mini, DeepSeek R1 via Groq API) and Google's newly released Gemini 2.0 Flash for faster inference.
- **Enhanced Attack Tree Generation**: Improved attack tree generation with robust JSON parsing and Mermaid diagram conversion, making the output more reliable and visually appealing.
- **Dynamic Model Discovery**: Added automatic model discovery for LM Studio Server, allowing users to select from available models in their local instances.
- **Improved Threat Model Generation**: Enhanced the guidance and prompts for threat model generation to produce more comprehensive and actionable results.
- **Structured Output Support**: Enhanced JSON output handling across all model providers to ensure reliable threat model and DREAD assessment generation.
- **UI Enhancements**: Updated the user interface to accommodate new model configurations and improved warning messages for local LLM limitations.

## 0.10

- **GitHub Repository Analysis**: STRIDE GPT now supports automatic analysis of GitHub repositories. Users can provide a GitHub repository URL, and the tool will analyse the README and key files to generate a more comprehensive threat model.
- **Environment Variable Support**: Added support for loading API keys and other configuration from environment variables, improving security and ease of deployment.
- **Improved Error Handling**: Enhanced error handling and retry mechanisms for API calls to improve reliability.
- **UI Enhancements**: Updated the user interface to accommodate new features and improve overall user experience.

## 0.9

Release highlights:

- **Mistral Client v1.0**: STRIDE GPT now uses v1.0 of the Mistral Client, which resolves the breaking changes introduced in the latest version of the Mistral API. This ensures that STRIDE GPT users can continue to leverage the Mistral API for threat modelling tasks.

## 0.8.1

This release added support for the following models:

- **GPT4o mini**: I've added support for OpenAI's recently released GPT4o mini model. GPT4o mini is a cost-efficient small model that still provides high-quality responses for threat modelling tasks.

- **Gemini 1.5 Pro (stable)**: Users can now choose from either the stable or preview versions of the Gemini 1.5 Pro model.

## 0.8

Release highlights:

- **DREAD Risk Scoring**: STRIDE GPT now supports DREAD risk scoring, allowing users to assign risk scores to identified threats based on the DREAD model. This feature provides a more comprehensive threat assessment and helps prioritise mitigation efforts.

- **Gherkin Test Cases**: Users can now generate Gherkin test cases based on the identified threats. This feature helps bridge the gap between threat modelling and testing, ensuring that security considerations are integrated into the testing process.

- **UI Enhancements**: I've refreshed the user interface making it easier to navigate and interact with the application and its features.

## 0.7

Release highlights:

- **Multi-Modal Threat Modelling**: STRIDE GPT now supports multi-modal threat modelling using OpenAI's GPT-4o and GPT-4-Turbo models. Users can provide an image of an architecture diagram, flowchart, or other visual representations of their application to enhance the threat modelling process.
- **Google AI Integration**: I've added support for Gemini 1.5 Pro via the Google AI API. Please note that Gemini doesn't consistently generate JSON output so you may need to retry some requests. In addition, Attack Trees can't be generated using Google AI models because of Google's safety restrictions.
- **Refactored Codebase**: I've refactored some parts of the codebase to improve maintainability and readability. This should make it easier to add new features and enhancements in future releases.
- **Bug Fixes**: Minor bug fixes and error handling improvements.

## 0.6

Release highlights:

- **Mistral API Integration**: Users can now choose to use LLMs provided by Mistral AI to generate threat models, attack trees and mitigation suggestions. This provides an alternative to OpenAI's GPT models, offering greater flexibility and choice for users.

- **Refined Prompts**: With more people using STRIDE GPT for work, I've updated the threat model prompt templates to encourage the LLMs to generate more comprehensive outputs. Users should now see multiple threats identified within each STRIDE category.

- **Public Roadmap**: I've created a public roadmap to provide visibility into upcoming features and improvements.

- **UI Enhancements**: I've made some minor updates to the UI to accommodate the new Mistral API integration and improve the overall user experience.

## 0.5

Release highlights:

- **Docker Container Image**: To make it easier to deploy STRIDE GPT on public and private clouds, the tool is now available as a [Docker container image](https://hub.docker.com/repository/docker/mrwadams/stridegpt/general) on Docker Hub.

## 0.4

Release highlights:

- **Integration of New GPT Models**: The application now supports the latest "gpt-4-1106-preview" and "gpt-3.5-turbo-1106" models, offering advanced capabilities and more accurate responses for threat modelling and attack tree generation.
- **Direct OpenAI API Calls**: STRIDE GPT now makes direct calls to the OpenAI API in order to take advantage of the recently introduced JSON Mode. This should greatly reduce the reduce the likelihood of syntax errors when generating threat models.
- **Refined Attack Tree Generation**: The process for generating attack trees has been overhauled to be more reliable, minimising syntax errors when generating Mermaid diagrams and improving the overall quality of the visualisations.
- **New Logo and Color Scheme**: A refreshed colour scheme and new logo (generated by DALL·E 3).
- **Continued Bug Fixes and Performance Improvements**: I've made a small number of additional updates to address existing bugs and optimise the application for better performance, ensuring a smoother and more efficient user experience.

## 0.3

Release highlights:

- **Threat Mitigations**: STRIDE GPT can now suggest potential mitigations for the threats identified in the threat modelling phase. This helps users develop strategies to prevent or minimise the impact of the identified threats.
- **Downloadable Output**: Users can now download the generated threat model, attack tree, and mitigations as Markdown files directly from the application. This makes it easy to share and document the generated outputs.
- **Improved User Interface**: I've further refined the user interface to provide a smoother and more intuitive user experience. The application layout has been optimised for better readability and usability.
- **Updated GPT Models**: STRIDE GPT now supports the latest 0613 versions of the GPT-3.5-turbo and GPT-4 models. These updated models provide improved performance and increased control over the generated output.
- **Bug Fixes and Performance Enhancements**: I've addressed several bugs and made performance improvements to ensure a more stable and responsive application.

## 0.2

Release highlights:

   - **Attack Tree Generation**: In addition to generating threat models, STRIDE GPT can now generate attack trees for your applications based on the provided details. This helps users better understand potential attack paths for their applications.
   - **Attack Tree Visualisation**: This is an experimental feature that allows users to visualise the generated attack tree directly in the app using Mermaid.js. This provides a more interactive experience within the STRIDE GPT interface.
   - **GPT-4 Model Support**: STRIDE GPT now supports the use of OpenAI's GPT-4 model, provided the user has access to the GPT-4 API. This allows users to leverage the latest advancements in GPT technology to generate more accurate and comprehensive threat models and attack trees.
   - **Improved Layout and Organisation**: I've restructured the app layout to make it easier to navigate and use. Key sections, such as Threat Model and Attack Tree, are now organised into collapsible sections for a cleaner and more intuitive user experience.

## 0.1

   Initial release of the application.
