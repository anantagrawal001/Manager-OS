# Implementation Plan — Concurrent Background Agents, Multi-Profile Chrome, and Recruiter Call Answering

This plan implements concurrent background task loops for agents, multiple Chrome profile launching / remote debugging, LinkedIn automatic job search & resume tailoring, simulated recruiter call answering, and a welcome-back status update screen triggered by "lets buckle up".

## User Review Required

> [!IMPORTANT]
> **Main Chrome Profile & Locks**: To allow the manager to operate on the user's *actual* main Chrome browser with logged-in sessions (Gmail, LinkedIn), we will implement a dual-mode loader:
> 1. Try to connect to an active Chrome instance running with remote debugging on port `9222`.
> 2. If no debug instance is detected, try to launch a headful Chrome using the user's Windows profile directory (`%LocalAppData%\Google\Chrome\User Data`). If the profile is locked (since Chrome is already open), the manager will log a warning and fall back to an isolated profile folder (`logs/chrome_user_data`), notifying the user.

> [!WARNING]
> **LinkedIn Easy Apply Automation**: Automated job application is highly subject to LinkedIn's anti-bot detection. To safeguard the user's accounts, the Career Agent will use human-like delays (30–60 seconds between inputs) and will fallback to opening the job page headful for manual completion if security verification is triggered.

## Proposed Changes

### Configuration

#### [MODIFY] [config.yaml](file:///c:/Users/Anant/Downloads/project/Manager/manager-os-v1.4/manager-os/config.yaml)
- Add a `chrome` section to customize profile paths and remote debugging:
  ```yaml
  chrome:
    remote_debugging_port: 9222
    user_data_path: null # Automatically resolves to LocalAppData if null
    profiles:
      main: "Default"
      work: "Profile 1"
      personal: "Profile 2"
  ```

---

### Core Activity Tracking System

#### [NEW] [activity_tracker.py](file:///c:/Users/Anant/Downloads/project/Manager/manager-os-v1.4/manager-os/core/activity_tracker.py)
- Implement `log_activity(agent_name, message)`: Writes timestamped activity logs to `logs/agent_activities.json`.
- Implement `get_recent_activities(limit)`: Retrieves recent activity lists for compiling updates.

---

### Chrome Profile & Debugging Integration

#### [MODIFY] [browser_automation.py](file:///c:/Users/Anant/Downloads/project/Manager/manager-os-v1.4/manager-os/core/browser_automation.py)
- Update `get_browser_context(playwright, profile_name="main")`:
  - Check if `localhost:9222` remote debugging is open and connect via CDP if available.
  - Otherwise, resolve `%LocalAppData%\Google\Chrome\User Data` and launch headful Chrome targeting the selected profile folder.
  - Fall back to `./logs/chrome_user_data` if a file lock is detected.

---

### Career Agent & Background Job Application

#### [MODIFY] [career_agent.py](file:///c:/Users/Anant/Downloads/project/Manager/manager-os-v1.4/manager-os/agents/career_agent.py)
- Implement `start_job_loop(keywords)`: Spawns a background task `_run_job_application_loop(keywords)` running in parallel.
- Implement `_run_job_application_loop(keywords)`:
  - Periodically search LinkedIn for job matches.
  - Extract job requirements.
  - Call AI to tailor the user's resume with the Google XYZ formula matching the listing.
  - Automate clicking "Easy Apply" and inputs, uploading the tailored resume.
  - Sleep between applications.
  - Log all actions using `activity_tracker.log_activity("career", ...)`.
- Add stop handler command (`"stop job loop"`).

---

### Recruiter Call Answering Simulation

#### [MODIFY] [communication_agent.py](file:///c:/Users/Anant/Downloads/project/Manager/manager-os-v1.4/manager-os/agents/communication_agent.py)
- Add `"simulate recruiter call"` and `"incoming call"` command handlers:
  - Trigger simulated voice call.
  - Say: *"Hello, this is Anant's personal assistant speaking. Anant is currently away. How can I help you?"*
  - Listen, transcribe caller responses, run a quick prompt to generate helper answers (like scheduling or screening questions), and speak them back.
  - Log the completed conversation to the activity database.

---

### Welcome Back "Lets Buckle Up" Handler

#### [MODIFY] [manager.py](file:///c:/Users/Anant/Downloads/project/Manager/manager-os-v1.4/manager-os/core/manager.py)
- Catch `"lets buckle up"`, `"buckle up"`, and `"let's buckle up"` intents.
- When caught:
  - Load recent activities from `logs/agent_activities.json`.
  - Query current background queue metrics and active threads.
  - Synthesize a J.A.R.V.I.S. style morning brief summarizing what each agent has accomplished since the user was away.

---

## Verification Plan

### Automated Tests
- Run test scripts to verify multiple profile loaders and remote CDP debugger connections.

### Manual Verification
1. **Buckle Up Status**: Say `"lets buckle up"` and verify it returns a clean status update showing what agents have accomplished.
2. **Career Background Loop**: Say `"start linkedin job loop for python developer"`, verify it runs in the background. Say `"status"` to verify it continues.
3. **Chrome Profile Selection**: Trigger the browser loop with different profile settings and verify correct folders are targeted.
4. **VoIP Recruiter Call**: Say `"simulate recruiter call"`, speak to the microphone, and verify the assistant responds to the recruiter questions and takes a message.
