# Workable local release — 2026-10-12

This report supersedes earlier claims that every agent or integration is complete.
The release provides a usable local assistant with tested startup, authentication,
AI chat, history, local voice, tasks, reminders and file outputs. It does not
complete every feature in the original Manager OS vision.

## Verified capabilities

| Area | Current implementation and evidence |
|---|---|
| Startup | Python 3.11 environment imports successfully; core package checks pass. Launcher anchors paths to the project and reuses an existing server. |
| Authentication | Existing passphrase retained; first-run enrollment creates a salted hash. Private HTTP endpoints and both WebSockets require a session. Logout revokes it. |
| Local AI | Actual `qwen3.5:4b` completion succeeded. Installed embedding models are excluded from chat selection. No model download occurs in a chat request. |
| Providers | Catalog-based model discovery, bounded timeouts, cooldowns and visible connection states. Gemini uses the supported compatible endpoint rather than the deprecated SDK. |
| Tasks | SQLite persistence, create/list/complete APIs, natural-language commands and dashboard controls. |
| Reminders | Persisted due time and delivery state; notifications recorded in history, broadcast to the dashboard and spoken when enabled. The process must be running. |
| History | SQLite retained across sessions and reloaded in the UI. Memory queries route to the conversation agent. Vector memory is optional via `MANAGER_ENABLE_VECTOR_MEMORY=1`. |
| Files | Filename search, numbered search-result reads, text creation without overwrite, and deterministic supported-app launch commands. Search excludes large generated directories and has an eight-second budget. |
| Generated projects | Builder produces real files and a ZIP under `outputs`; a live local-model generation produced a valid two-file archive. Generated code is not automatically executed or proven correct. |
| Speech | Local pyttsx3/Zira speech completed. Local Whisper base correctly transcribed synthesized test speech. The Local mic flow records locally and places the transcript into the input for review. |
| Dashboard | Browser smoke checks sign-in, wrong-passphrase rejection, real AI chat, saved tasks, task completion, reload/history, Connections, lock, authorized output downloads and the Local mic flow using a synthetic audio device. Screenshots are in `logs/qa-*.png`. |

## Explicit limits

- WhatsApp: explicit recipient/message syntax only; requires a signed-in dedicated browser profile. No real message was sent to validate delivery. Missing or ambiguous contacts do not fall through to another contact. Photo/group sending is not a verified supported workflow.
- LinkedIn: the background loop collects visible job links to `outputs/job-listings.jsonl`. It records `applied: false` and `resume_tailored: false`. It does not submit applications. Real account search remains unverified.
- Recruiter calls: simulation only; no telephony integration. Silence no longer becomes an invented recruiter transcript.
- Trading: informational analysis only, with no live broker, order execution or verified current market feed. Older speculative consensus handlers are no longer used by the public execution path.
- Research: knowledge-based drafts only; no connected live search or automatic citation verification.
- Email, social publishing, external calendar synchronization and second-laptop remote deployment are unfinished integrations. API synchronization now requires authentication; any old unauthenticated second-laptop client needs updating before use.
- Full local-data encryption and voice biometrics are not implemented. The vault encrypts keys; SQLite conversations/tasks and outputs are not encrypted databases.
- Cloud fallbacks may send request content to configured providers. Use `ai_router.local_only: true` for local-only inference. The existing browser speech feature may use an online service; Local mic does not.
- The minimal installer was import-checked in the existing environment; a clean Windows machine installation was not performed.

## Regression evidence

`python -m unittest discover -s tests -v` passes 15 tests covering route selection,
authentication, session revocation, file creation/read/no overwrite, task persistence,
reminder retry/deduplication, selected-agent execution, provider failure behavior,
history prompt duplication, explicit communication actions, safe artifact paths and
replacement-key persistence. Test data uses temporary stores.

`python -m tests.browser_smoke` runs the actual FastAPI lifespan and a headless Chrome
session on port 8011 using isolated credentials, history and tasks. Local AI is real;
external messaging is replaced with an assertion failure to prevent any accidental
send during a non-send test. The optional voice fixture is synthesized speech,
not microphone audio from the user.

Manual/runtime checks also verified the Windows Zira voice, Whisper transcription,
provider availability errors without printing secrets, and actual local-model file
bundle generation. Some cloud keys reported quota or endpoint errors; those are
shown as connection failures rather than being described as working.

## Implementation notes

Source before changes is retained in `backups/before_workable_2026-10-12.zip`.
Superseded definitions are commented in place in accordance with this repository's
retention policy. One-time migration scripts are maintenance records, not setup steps.

References used for provider compatibility: [Gemini compatible endpoint](https://ai.google.dev/gemini-api/docs/openai)
and [Ollama API documentation](https://github.com/ollama/ollama/blob/main/docs/api.md).

Final launch check: the actual production launcher started port 8000; /api/health returned ready=true. STOP.bat is available to stop the recorded process belonging to this checkout.

### Update: 12 October 2026 — background document work

Resume commands now gather approved local evidence, run in the background and save real PDF/HTML/text drafts. General document requests use a find/read/save tool loop. Work status and follow-ups persist. Thirty regression tests and both browser workflows passed. See [ASSISTANT_WORK.md](ASSISTANT_WORK.md) for exact behavior, commands and limitations; this does not complete unrestricted computer or account automation.
