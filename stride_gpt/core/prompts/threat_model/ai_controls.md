---
# Generated from stride_gpt/core/controls/catalog.toml by
# scripts/build_control_catalog.py. Edit the catalogue, not this file.
name: ai_controls
title: AI and Agentic Control Catalogue (LLM security, agentic AI, AI governance)
when_to_load: |
  Load in addition to security_controls when the subsystem uses LLMs, RAG or
  embeddings, trains or serves models, or runs agents with tools, memory or
  delegated credentials. Adds IDs to the same CONTROLS field. Pairs with the
  genai, agentic and insider_threat cards: those name the risk, this card
  names the control.
adds_fields:
  - CONTROLS
stride_letters: [S, T, R, I, D, E]
source: https://github.com/mrwadams/stride-gpt/blob/master/docs/controls-catalog.md
version: 2026.10
---

# AI and Agentic Control Catalogue (LLM security, agentic AI, AI governance) — Reference Card

You loaded this card because the subsystem has language-model or agent behaviour in scope. It adds AI application controls, agentic AI controls, and the AI governance controls that AIUC-1, ISO/IEC 42001 and the EU AI Act expect. Use it alongside security_controls: most AI threats need both a traditional control and an AI-specific one.

## How to use this card

- For each threat, choose **1-4** control IDs that would most directly prevent, detect or contain it, most important first.
- Prefer the most specific control. A threat about a *missing* control cites that control.
- **Anti-hallucination requirement.** Use only IDs listed in the control cards you loaded, exactly as written. Never invent an ID; if nothing fits, leave the field out rather than guess.
- Do not cite framework clauses yourself. STRIDE-GPT looks up the AIUC-1, ISO/IEC 42001, ISO/IEC 27001 and EU AI Act references for the IDs you choose.
- IDs from `security_controls` are equally valid; a threat can combine IDs from both cards.

## Schema additions

Each threat must additionally include:
- `"CONTROLS"`: an array of control IDs, e.g. `["AGT-05", "AI-01"]`. When reporting through `report_threat`, pass them as the `controls` argument.

## Control catalogue

### AI — AI & LLM Application Security

- `AI-01` **Prompt-injection defences for untrusted content.** Treat user, retrieved and tool content as data, not instructions: segregate and label it, screen it for injection, and keep authorisation decisions outside the model. (T, E, S)
- `AI-02` **Validate model output before it is used.** Validate structured model output against strict schemas and never pass it to interpreters, shells, queries or privileged APIs without allow-listing. (T, E)
- `AI-03` **System prompt hygiene: no secrets or security logic in context.** Keep credentials, internal endpoints and authorisation logic out of system prompts, tool descriptions and model context, on the assumption that prompts can be extracted. (I)
- `AI-04` **Retrieval (RAG) access control and source provenance.** Enforce the requesting user's permissions at retrieval time, partition indexes by tenant, control who can write to the corpus, and record provenance for every chunk. (I, T, E)
- `AI-05` **Training and fine-tuning data governance.** Govern training, fine-tuning and evaluation data with documented sourcing, quality and bias checks, lineage, integrity protection and poisoning detection. (T, I)
- `AI-06` **Model provenance, integrity and AI-BOM.** Source models from trusted registries, verify their signatures or hashes, prefer non-executable weight formats, pin versions, and keep an AI bill of materials. (T, E)
- `AI-07` **Adversarial testing and AI red teaming.** Test for prompt injection, jailbreaks, data leakage, tool misuse, harmful or out-of-scope output and hallucination before every release and on model or prompt changes, including independent testing for high-risk systems. (S, T, R, I, D, E)
- `AI-08` **Output guardrails: harmful, out-of-scope and hallucinated content.** Filter harmful and out-of-scope output, ground factual answers in cited sources, flag high-risk output for human review, and measure hallucination rates. (R, T, I)
- `AI-09` **AI transparency and disclosure.** Tell people when they are interacting with AI, mark AI-generated content in a machine-readable way where required, and document capabilities, limitations and intended use. (R, S)

### AGT — Agentic AI

- `AGT-01` **Agent inventory, named owner and assigned autonomy level.** Register every agent with a named accountable owner, purpose, autonomy level (L0-L5), tools, data scopes and credentials, and block agents that are unregistered or unowned. (R, E, S)
- `AGT-02` **Least-agency design.** Give each agent the lowest autonomy, narrowest goal and smallest action space that meet the business need, preferring deterministic workflows for high-risk tasks. (E)
- `AGT-03` **Distinct, verifiable identity for every agent.** Give each agent, and ideally each running instance, its own attested non-human identity — never a shared service account or a human's credentials — so every action is attributable. (S, R)
- `AGT-04` **Task-scoped, short-lived, delegated credentials.** Issue agents just-in-time credentials scoped to the task and audience with minute-level lifetimes, injected at the tool layer and never placed in the model's context. (E, I, S)
- `AGT-05` **Tool allow-listing with policy-enforced, schema-validated calls.** Expose only the tools a task needs and check every tool call against a schema and policy in deterministic code outside the model, denying destructive operations by default. (E, T)
- `AGT-06` **Tool and MCP supply-chain integrity.** Allow-list MCP servers and plugins from trusted publishers, pin tool definitions by hash and verify them before granting access — blocking on mismatch — and keep an AI-BOM per agent. (T, S, E)
- `AGT-07` **Risk-tiered human approval for high-impact actions.** Require explicit human approval for irreversible, financial, privileged, external-communication or bulk-data actions, showing the approver the exact action and its provenance. (E, R, T)
- `AGT-08` **Sandboxed, ephemeral execution of agent actions.** Run agent-generated code and commands in ephemeral, strongly isolated sandboxes with no network by default, no host mounts, strict resource quotas and no agent credentials. (E, T, D)
- `AGT-09` **Memory and context integrity.** Partition agent memory by user, tenant and session, record the provenance of every write, validate before persisting and reuse, and support expiry and rollback. (T, I)
- `AGT-10` **Authenticated, authorised inter-agent communication.** Mutually authenticate agents, sign messages with their delegation chain, authorise each delegated request against the originating principal's scope, and reject replays. (S, T, E, R)
- `AGT-11` **Action-level, tamper-evident audit trail for agents.** Record every model call, tool call, approval, delegation and credential use with agent, user, session and model/prompt version, in append-only storage the agent cannot touch. (R)
- `AGT-12` **Behavioural monitoring, anomaly detection and canaries.** Baseline each agent's tool use, data volumes and destinations, alert on deviation, and plant canary credentials and decoy resources inside its reach. (R, I, E)
- `AGT-13` **Kill switch and rapid containment.** Provide a tested mechanism to halt one agent instance, an agent type or the whole fleet and revoke its credentials and tool access within minutes, leaving a safe, forensically preserved state. (D, E, R)
- `AGT-14` **Execution budgets, loop limits and circuit breakers.** Cap each task's steps, tool calls, tokens, wall-clock time and spend, detect loops, and isolate failures with circuit breakers so one agent cannot cascade into others. (D)

### GOV — AI Governance

- `GOV-01` **AI policy, accountability and acceptable use.** Approve an AI policy, assign roles and accountability for each AI system, publish an acceptable-use policy, and train staff in AI literacy for their role.
- `GOV-02` **AI risk management and impact assessment.** Run a lifecycle AI risk management process — including threat models like this one — classify each system under the EU AI Act, and assess impacts on individuals and society.
- `GOV-03` **AI technical documentation and change control.** Keep current technical documentation for each AI system and version models, prompts, tools and configuration under change control with evaluation evidence before release. (R)
- `GOV-04` **Third-party AI provider due diligence.** Assess model and AI-tool providers for data use, retention, processing locations, sub-processors, security attestations and incident terms, and monitor their access. (I)
- `GOV-05` **AI incident management and serious-incident reporting.** Keep AI-specific failure plans for security breaches, harmful outputs and hallucination-driven harm, integrated with security incident response and regulatory reporting. (R)
- `GOV-06` **Post-deployment monitoring of AI performance and risk.** Monitor deployed AI systems for quality drift, harmful-output and override rates and user complaints, and feed the results back into risk management. (R)
