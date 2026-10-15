# Project goals and execution

Implemented and checked on 12 October 2026.

Tell Manager a goal such as `Create a LinkedIn optimizer and resume maker` or `Build an expense tracker app`. Software requests take precedence over their subject keywords, so a calendar app is sent to Builder rather than treated as a reminder.

Manager saves an architecture with technology choices, alternatives and observable acceptance criteria. Its background worker writes source, looks up package metadata, installs project dependencies, runs checks, starts the app, exercises it in Chrome, feeds failures back into the model and packages the result. You can keep chatting while it works. The Work panel shows progress and starts completed projects; Outputs contains source ZIPs, architecture, verification reports and browser previews.

## Continuing work

- `project progress`
- `continue project` or `retry project`
- `also add CSV export` while a project is active: adds a requirement that needs a passing check.
- `cancel project`: stops owned processes and preserves files.
- `open project`: starts the saved launch command.

Records survive restart in `logs/workflows.db`. Project files live in `workspaces/project-<id>`. Old file versions are retained under `.manager/revisions`. Interrupted work can resume from its saved plan and files. Preview servers are owned by Manager and need restarting after Manager closes.

## Verification and execution boundaries

The typed tools support Python, Node and npm projects, official package-registry metadata, bounded process execution, local HTTP checks, and real Chrome interactions. They do not accept arbitrary shell command strings. Python dependencies use a project virtual environment; provider keys are not forwarded in its environment. Working-directory and environment separation are **not an OS sandbox**: generated programs run with the local user's permissions.

Completion requires checks covering every acceptance identifier at the current source fingerprint, a README with launch instructions, at least two browser assertions for web apps, and a model review without blockers. Source or dependency-manifest changes invalidate checks. Zero-test runs, syntax-only checks and empty Python tests do not count. These gates reduce false completion claims; they do not prove arbitrary generated software correct. Test-to-requirement mapping still includes model judgment.

Project code and planning prefer configured cloud providers, then local inference. `ai_router.local_only: true` still prevents cloud inference. Personal-document workflows retain local inference. Provider readiness on a short probe does not guarantee that a large project request fits the provider's limits. The installed small local model can require substantial repair. Each run has a configurable allowance (`workflows.project_steps_per_run`, default 60); unfinished work is saved rather than falsely reported complete.

This adds a software execution workflow alongside document work and existing commands. It does not implement every possible task, remote account integration, deployment, external messaging or unlimited human-level autonomy.

## Acceptance project: Career Studio

The local LinkedIn Optimizer and Resume Maker imports TXT/PDF/DOCX, preserves source facts, creates editable profile fields, compares a finite list of role keywords, and exports edited resume text as HTML and PDF. Optional local AI offers separate, unverified editing suggestions and falls back honestly when unavailable. No LinkedIn login or publishing is used.

The first local-model implementation had functional and test defects and needed direct repair during this session. The final app passed 11 backend tests and a real Chrome flow verifying actual edited PDF/HTML download contents, invalid input, editable fields, responsive width and no JavaScript errors. A final model review passed. This is a verified local example, not evidence of reliable unattended completion of arbitrary projects.

Manager itself passed 40 regression tests, including a real failing-command/repair/retest sequence with scripted model actions, stale-check rejection, path boundaries, process timeout, live HTTP/Chrome tools and added requirements. Its browser smoke passed existing sign-in/chat/tasks/history/downloads/voice/lock plus Work-panel project launch. The source release excludes personal data, credentials, generated workspaces and environments.

## Outcome requests, task focus and recovery — 12 October 2026

`core/goal_director.py` adds persistent conversational focus. Outcome requests such as “I need a website for my work” start the software workflow without requiring a build command. Ambiguous written-artifact requests receive one bounded local classification call. Supported targets are software, documents and personal resumes; model-proposed shell commands or external-account actions are not accepted by this director.

“Continue,” “make it faster,” “it failed when I uploaded a PDF,” and answers to a pending essential question retain the selected workflow ID. Background checkpoints cannot steal focus. The Work panel lets the user choose **Use as current task** when several items exist. “How is it going?” reports saved work states rather than generating an imagined progress report. Explicit reminders, file commands and send requests retain their own handlers.

`core/task_context.py` retrieves relevant earlier user statements, including preferences, with exact quotations, message IDs and dates. It excludes assistant assertions and messages matching credential patterns, limits query time and source size, and treats older statements as potentially outdated evidence. This is keyword/topic retrieval, not complete semantic memory or a guarantee that every relevant fact is found. Personal file discovery continues through the previously approved document workflows.

Project execution now identifies repeated rewrites or recurring errors and injects a concrete next-check/repair prompt. A transient provider failure or malformed JSON receives one retry without replaying a tool action. Exhausted model failures leave saved work interrupted and resumable. Review outages cannot bypass verification. These mechanisms improve execution discipline, but weak model output can still need intervention.

This does not make Manager equal to the fictional JARVIS. Its reasoning quality still depends on available models, and its actions depend on implemented tools and connected services. No unrestricted self-improvement or universal task completion is claimed.
