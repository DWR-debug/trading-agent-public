# Free-Only AI Worker Fabric

Stand: 2026-09-28

## Purpose

The Trading Agent now has a provider-neutral AI worker layer for bounded
research-support tasks. Its purpose is to add inexpensive parallel reasoning
capacity without turning an external LLM into a source of scientific evidence.

The fabric is deliberately separate from deterministic computation.

OpenRouter is integrated through a hard-wired HTTP adapter that accepts only the provider's free router and never exposes a paid model fallback.

## Resource classes

1. Self-hosted PC: persistent deterministic QA, reproduction, coverage/PIT
   preparation and approved local research workloads.
2. GitHub-hosted runners: deterministic CI/research plus the bounded
   GitHub-agent queue.
3. External AI workers: Gemini CLI, OpenRouter Free and optionally Claude CLI for bounded
   hypothesis generation, adversarial review, architecture review and research
   design support.
4. Python: canonical numerical computation, statistical validation,
   reproducibility and evidence-generation tooling.

These classes are intended to operate concurrently whenever their jobs are independent.

## Free-only rule

External AI workers are fail-closed. A provider is used only if its executable
and authentication are available, AI_EXTERNAL_PROVIDER_ALLOWLIST=true is set,
a provider-specific free-mode attestation is present, and the task contract
prohibits deterministic computation, selection, gate changes, promotion, live
execution and paid usage.

For Gemini, the official CLI supports headless prompt execution and JSON output
and can be installed with npm. Google's current Gemini Developer API documentation
lists a Free Tier with free input and output tokens for selected models, subject
to limits. This makes Gemini the primary opportunistic external worker.

For Claude, the fabric treats CLI/subscription access as opportunistic. An Anthropic
API key is never accepted as proof of free access. Claude is used only when an existing
CLI session is explicitly attested as free and available.

## Worker output contract

AI output is written to workflow artifacts and operational run state. It is never
inserted directly into research evidence, authorizations, gates or promotion records.
The output envelope records task ID, provider, task fingerprint, preflight result,
return status, output excerpts, worker_output_is_scientific_evidence=false and safety state.

A later deterministic task may consume a worker handoff as an input idea, but must
independently validate every technical or scientific claim.

## Concurrency model

The AI workflow runs on GitHub-hosted runners independently of the self-hosted PC
research loop and the existing bounded GitHub agent queue. Therefore a busy PC runner
does not block AI-worker jobs. Gemini and Claude have separate lanes, and independent
tasks can run in parallel.

## Recommended task classes

Unusual-alpha hypothesis generation; failure-mechanism counterhypotheses; Q089 adversarial
methodology review; architecture/refactoring review; test/specification design; and
research-literature synthesis.

Never delegate formal promotion or scientific gate interpretation.

## Authentifizierung: lokale Google-/Claude-Anmeldung

Auf dem persistenten Windows-PC kann Gemini CLI interaktiv mit einem Google-
Konto angemeldet werden. Die CLI cached die Authentifizierung lokal; Headless-
Aufrufe können diese bestehende Authentifizierung verwenden, sofern sie unter
demselben Windows-Benutzerprofil laufen.

Das ist nicht dasselbe wie eine automatische Verbindung zum Benutzerkonto in
ChatGPT. Für GitHub-hosted Runner müssen Credentials separat bereitgestellt
werden; der lokale Browser-Login wird nicht dorthin übertragen.

Claude Code unterstützt ebenfalls nicht-interaktive `claude -p` Aufrufe und
maschinenlesbare JSON-Ausgabe. Die verfügbare Authentifizierung hängt vom
Claude-Account-/Planstatus ab; kostenlose Nutzung wird deshalb nicht
vorausgesetzt.

Credentials werden niemals in Repository-Dateien oder AI-Task-Prompts geschrieben.