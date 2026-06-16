# Project Context

This file records the current workspace's configurable project context, including project-specific wiki structure requirements, classification preferences, naming preferences, and project-specific rules. The agent should complete it during the first project-context initialization conversation and update it when the project subject changes.

Fields are optional unless required for the current task. Leave a field blank when the project has no specific preference; blank fields mean "not specified," not "to be invented."

## Context

- Theme:
- Goal:
- Audience:
- Scope:
- Preferred terms:
- Wiki structure requirements:
- Classification preferences:
- Naming preferences:
- Project-specific rules:
- Constraints:
- Open questions:

## Source Extraction Preferences

- Preferences status: unconfirmed
- Default provider for document: markitdown
- Alternative provider for document: mineru
- MinerU profile:
- MinerU profile status: pending
- MinerU credential status: unconfigured
- Prefer MinerU when available: unconfirmed
- PDF preflight policy: lightweight
- Default provider for webpage: defuddle
- Image extraction policy: ask-before-ocr
- Audio extraction policy: ask-before-transcription
- Video extraction policy: ask-before-transcription-or-frame-ocr
- Unsupported source kinds:
- Provider-specific preferences: non-secret provider choices only; private endpoints and secret values belong in the project-root `.env`
