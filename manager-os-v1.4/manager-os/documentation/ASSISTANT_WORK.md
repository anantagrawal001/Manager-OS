# Background document work

Implemented and verified on 12 October 2026. This extends the local assistant with tasks that gather information and produce files.

Say **create my resume**. Manager searches the approved folders and saved user messages, selects a matching source, drafts using local AI, validates source quotations and numbers, and saves PDF, printable HTML and text. Dated employment blocks are preserved even when the model omits them. Other people's unmatched resumes are excluded using the configured owner's name near the document header. This is a name check, not proof of identity.

For other documents, try **summarize my weekly-notes document into an update and next steps**. The assistant selects actual tools to find documents, read them, and save drafts. This loop has a ten-step limit. It checks that output files exist before reporting a draft ready.

The **Work** panel shows progress and questions; **Outputs** downloads files. Chat remains usable during background work. Keep Manager running. Completion messages and essential questions are saved to chat.

## Continue and recover

- Resume: `continue resume`, `retry resume`, `resume progress`, `cancel resume`.
- Other documents: `continue work [answer]`, `work progress`, `cancel work`.
- Work records survive a restart. Interrupted work requires a continue command.
- Configure approved folders in `personal_context.roots` in `config.yaml`. This installation uses Documents, Desktop and Downloads, as approved by the owner.

## Implementation and validation

`core/personal_context.py` provides bounded PDF/DOCX/text discovery and user-only chat evidence. `core/workflows.py` implements persistent resume work and document rendering. `core/assistant_work.py` implements the general local document tool loop. State is in `logs/workflows.db`; files are in `outputs`. The authenticated `/api/workflows` endpoint omits extracted source text.

Resume processing and the general tool loop use local AI with structured JSON output. The local model context window accommodates both evidence and generated output. Ordinary chat retains its existing provider configuration.

Thirty regression tests passed. A real Chrome/local-model test found and read a notes file, saved a summary, displayed progress, accepted another task during execution, and downloaded the result. Existing browser smoke passed sign-in, chat, local AI, tasks, downloads, history, connections, lock and local microphone transcription. An actual resume from the owner's source files was generated and its one-page PDF was rendered and visually reviewed. Compilation and dependency checks passed.

## Scope and limitations

This is a bounded document assistant, not general human-level autonomy. Its document loop has three executable tools: find, read and save. It cannot browse the internet, send messages, operate external accounts, execute arbitrary code or install software. Existing deterministic commands remain available separately.

Folder scans have time, depth, count and size limits. Encrypted or scanned PDFs may need text extraction. Resume quotations and numeric claims are checked, but every paraphrase is not independently verified. Existing employment dates and claims are not verified against external sources. Review drafts before submission; no application is submitted by these workflows.

Workflow records, extracted source text, and output documents are ordinary local files. They are excluded from the source release along with credentials and conversation history.
