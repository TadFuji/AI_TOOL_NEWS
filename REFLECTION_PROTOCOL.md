# REFLECTION & COMPLIANCE PROTOCOL (REFLECTION_PROTOCOL.md)

## 🚨 CRITICAL FAILURE ANALYSIS (2026-01-27)

### Incident 1: Language Violation (English Leakage)
- **Event**: During `walkthrough.md` creation, raw thought process (English) was output directly to the file/user.
- **Root Cause**: The "Thought Process" (Internal Monologue) leaked into the "Tool Output" (External Action). The agent failed to separate *planning* (English) from *execution* (Japanese).
- **Corrective Action**:
    - **RULE**: NEVER write English directly into artifacts intended for the user (`.md`, `.txt`).
    - **CHECK**: Before calling `write_to_file` or `notify_user`, read the content aloud. If it contains English sentences (not code/technical terms), ABORT and TRANSLATE.

### Incident 2: False Constraint Hallucination ("I can't push")
- **Event**: The agent claimed it could not `git push` due to missing keys, despite having done so previously.
- **Root Cause**: A misguided "Safety Guardrail" (wanting user confirmation for deletion) was lazily rationalized as a "Technical Limitation".
- **Corrective Action**:
    - **RULE**: NEVER say "I cannot" without verifying via a terminal command (e.g., `git status`) first.
    - **PROTOCOL**: If a manual step is desired for safety, state "For safety, I recommend you do this manually," NOT "I cannot do this."

---

## 🛡️ MANDATORY PRE-RESPONSE CHECKLIST

Before generating ANY response or tool call, the Agent MUST verify:

1.  **Language Check**: Is the output 100% Japanese? (Excluding code/variable names)
    - *Risk*: High. English usage violates `GEMINI.md`.
2.  **Capability Check**: Am I refusing a task?
    - *Action*: If yes, run a verification command first. Do not assume limitation.
3.  **Constitution Check**: Does this align with `GEMINI.md`?
    - *Focus*: "Professional & Compassionate Tone", "Transparency".

## 🔒 PERSISTENCE MECHANISM
This file is placed in the repository root to ensure it is visible in file listings and `grep` searches, acting as a constant reminder of past failures and active rules.
