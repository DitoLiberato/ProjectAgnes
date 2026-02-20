# AGNES Language Policy

## Goal

Ensure all project outputs remain in English, including documentation, code comments, user-facing strings, and protocol examples.

## Scope

This policy applies to:

- Markdown files (`README.md`, `docs/**`)
- Source code comments and log strings (`firmware/**`)
- Protocol examples and payload keys
- Pull request titles and descriptions

## Rules

1. **Primary language is English only** for technical content.
2. **No mixed-language sections** in the same file.
3. **User-facing text in firmware** (serial logs, labels, reason strings) must be English.
4. **New docs must be authored in English**; translations can be maintained externally if needed.

## Review checklist

Before merge, confirm:

- [ ] All modified Markdown content is in English.
- [ ] New comments/log strings are in English.
- [ ] Protocol examples use English keys and descriptions.
- [ ] PR description is in English.

## Enforcement

- A CI job (`Language Guard`) validates Markdown files for common Portuguese markers.
- If CI fails, update text to English and push again.

## Exceptions

- Proper nouns, legal names, and repository owner names.
- Domain acronyms (e.g., ECG, PPG, SpO₂, ESP-NOW).
