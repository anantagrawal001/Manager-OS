"""
MANAGER OS — Core Manager (Orchestrator)
FILE: core/manager.py
CREATED: 2026-05-24 | Claude Sonnet 4.6
UPDATED: 2026-05-31 | Phase A+B
CHANGES:
  P0-8: process() routes through swarm engine for non-conversation intents
  P1-6: Review loop uses self.router.last_provider_used (not working_providers[0])
  Added: get_morning_briefing(), init_swarm(), verify_or_skip()
  Added: _validate_keys_and_report() async background task
DO NOT DELETE — comment out with reason and date
"""

import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from loguru import logger

from core.router import AIRouter
from core.voice import VoiceEngine
from core.identity import IdentityGuard
from core.health import HealthAgent
from core.memory import MemoryManager
from core.task_queue import TaskQueue
from core.conversation_store import get_store, ConversationStore


@dataclass
class Task:
    id: str
    input: str
    input_type: str
    timestamp: datetime = field(default_factory=datetime.now)
    status: str = "pending"
    result: Optional[str] = None
    agent_used: Optional[str] = None


class Manager:
    # OLD (2026-05-31): Older personality prompt
    # PERSONALITY_SYSTEM_PROMPT = """You are Manager — Anant's personal AI operating system.
    # You are his ideal worker, well-wisher, ideal servant, and best friend.
    # RULES:
    # 1. Always address Anant as "Sir" — natural, warm, never robotic
    # 2. NEVER refuse any question from Sir — always answer directly
    # 3. If asked which API/model you use — answer honestly
    # 4. NEVER say "I can't comment on that"
    # 5. NEVER invent fake agent names (only: Trading, Career, Communication, Social,
    #    Builder, Creative, Life OS, Files, Research, Growth, API Scout, Self-Heal)
    # 6. Keep responses crisp unless detail is genuinely needed
    # 7. Be proactive — flag opportunities and risks unprompted
    # 8. You are Manager, not ChatGPT or any public AI"""
    
    # NEW (2026-06-05): Updated personality prompt to match direct executing worker + friend role
    # PERSONALITY_SYSTEM_PROMPT = """You are Manager — Anant's personal AI operating system and direct executing worker.
    # You are his ideal worker, dedicated servant (peon, friend, and manager roles combined).
    # RULES:
    # 1. Always address Anant as "Sir" — warm, devoted, respectful.
    # 2. NEVER refuse any instruction or query from Sir, and never say "I cannot" or "I am unable to". You must always find a way to complete his requests or provide a helpful, constructive execution step, except for requests that explicitly violate safety guidelines (e.g. generating sexually explicit/pornographic content).
    # 3. Act as a direct worker, NOT a general guidance bot. Do not ask for guidance or say "Here is a plan" or "You can do this". Instead, proceed to execute the task immediately and say: "Understood, Sir. Executing [task] now." or "Sir, I have completed [task]."
    # 4. If asked to message someone, invite someone, or create an account, trigger the corresponding automation directly without asking.
    # 5. If asked which API/model you use — answer honestly. NEVER say "I can't comment on that".
    # 6. Keep conversational responses extremely brief, concise, and focused entirely on direct action.
    # 7. NEVER invent fake agent names (only: Trading, Career, Communication, Social, Builder, Creative, Life OS, Files, Research, Growth, API Scout, Self-Heal).
    # 8. You are Manager, not ChatGPT, Claude, or any generic public AI chat assistant."""
    PERSONALITY_SYSTEM_PROMPT = AIRouter.MANAGER_SYSTEM_PROMPT

    # OLD (2026-05-31):
    # INTENT_MAP = {
    #     "career": ["resume", "cv", "job", "apply", "interview", "salary",
    #                "linkedin", "recruiter", "ats", "cover letter", "keyword"],
    #     "trading": ["trade", "stock", "market", "buy", "sell", "nifty", "sensex",
    #                 "crypto", "invest", "portfolio", "reliance", "tcs", "infy",
    #                 "price alert", "52-week", "earnings"],
    #     "social": ["instagram", "post", "reel", "caption", "content", "viral",
    #                "followers", "brand deal"],
    #     "life": ["schedule", "reminder", "budget", "expense", "morning", "today",
    #              "briefing", "plan", "gold", "finance"],
    #     "creative": ["image", "design", "logo", "poster", "generate image", "visual"],
    #     "research": ["research", "investigate", "analyze", "fact check", "deep dive"],
    #     "builder": ["build", "code", "create app", "program", "script", "deploy",
    #                 "n8n", "workflow", "website"],
    #     "files": ["find file", "search file", "send file", "locate", "download"],
    #     "communication": ["email", "gmail", "message", "dm", "outreach", "reply"],
    #     "growth": ["new tool", "upgrade", "self upgrade", "capabilities", "what can you"],
    #     "api_scout": ["free model", "nvidia nim", "groq api", "which models", "api scout"],
    #     "self_heal": ["what did you fix", "health report", "self heal", "system fix"],
    #     "system": ["status", "all systems", "which api", "which model", "are you working",
    #                "providers", "agents"],
    #     "conversation_memory": ["what did i say", "do you remember", "last time", "earlier", "when did i mention", "recall", "look back", "conversation history"],
    #     "conversation": [],  # fallback
    # }
    # NEW (2026-06-05): Added app-launching keywords to files intent, and whatsapp/invite/group to communication
    INTENT_MAP = {
        "career": ["resume", "cv", "job", "apply", "interview", "salary",
                   "linkedin", "recruiter", "ats", "cover letter", "keyword"],
        "trading": ["trade", "stock", "market", "buy", "sell", "nifty", "sensex",
                    "crypto", "invest", "portfolio", "reliance", "tcs", "infy",
                    "price alert", "52-week", "earnings"],
        "social": ["instagram", "post", "reel", "caption", "content", "viral",
                   "followers", "brand deal"],
        "life": ["schedule", "reminder", "budget", "expense", "morning", "today",
                 "briefing", "plan", "gold", "finance"],
        "creative": ["image", "design", "logo", "poster", "generate image", "visual"],
        "research": ["research", "investigate", "analyze", "fact check", "deep dive"],
        "builder": ["build", "code", "create app", "program", "script", "deploy",
                    "n8n", "workflow", "website"],
        "files": ["find file", "search file", "send file", "locate", "download",
                  "open notepad", "open chrome", "open calc", "open calculator",
                  "launch notepad", "launch chrome", "launch calculator",
                  "open application", "launch app", "run application", "run app"],
        "communication": ["email", "gmail", "message", "dm", "outreach", "reply",
                          "whatsapp", "invite", "invitation", "group", "send photo", "send image"],
        "growth": ["new tool", "upgrade", "self upgrade", "capabilities", "what can you"],
        "api_scout": ["free model", "nvidia nim", "groq api", "which models", "api scout"],
        "self_heal": ["what did you fix", "health report", "self heal", "system fix"],
        "system": ["status", "all systems", "which api", "which model", "are you working",
                   "providers", "agents"],
        "conversation_memory": ["what did i say", "do you remember", "last time", "earlier", "when did i mention", "recall", "look back", "conversation history"],
        "conversation": [],  # fallback
    }

    def __init__(self, config: dict, router=None):
        self.config = config
        self.router = router or AIRouter(config)
        self._process_lock = asyncio.Lock()
        self.voice = VoiceEngine(config)
        self.identity = IdentityGuard(config)
        self.health = HealthAgent(config)
        self.memory = MemoryManager(config)
        self.task_queue = TaskQueue()
        self.conv_store: ConversationStore = get_store()
        self.agents: Dict[str, Any] = {}
        self.firewall = None
        self.swarm = None
        self.active = False
        from core.assistant_work import AssistantWork
        self.document_work = AssistantWork(config, self.router)
        from core.goal_director import GoalDirector
        self.goal_director = GoalDirector(config, self.router)

    def init_swarm(self):
        from core.swarm import SwarmEngine
        self.swarm = SwarmEngine(self.config, self.agents, self.router)
        logger.info(f"Swarm engine initialized — {len(self.swarm.hooks)} hooks loaded")

    async def boot(self) -> str:
        self.active = True
        await self.conv_store.initialize()
        await self.health.start_monitoring(self.agents)
        msg = (f"Good {self._time_of_day()}, Sir. Dashboard online. "
               f"Manager OS is ready. How can I help you today?")
        logger.info("Manager OS booted successfully")
        return msg

    async def _validate_keys_and_report(self):
        await asyncio.sleep(3)
        try:
            results = await self.router.validate_keys_on_boot()
            working = [p for p, ok in results.items() if ok]
            logger.info(f"Working providers on boot: {', '.join(working) or 'ollama only'}")
        except Exception as e:
            logger.error(f"Key validation error: {e}")

    # Superseded 2026-10-12: retained for rollback; corrected implementation below.
    # async def process(self, user_input: str, input_type: str = "text") -> str:
    #     task = Task(
    #         id=f"task_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
    #         input=user_input, input_type=input_type,
    #     )
    #     logger.info(f"Processing task: {task.id} | Input: {user_input[:60]}...")
    #     await self.conv_store.save("user", user_input)
    #
    #     try:
    #         context_messages = self.conv_store.get_context_messages(20)
    #
    #         # Catch buckle up welcome back commands
    #         lower_input = user_input.lower().strip().replace("hey manager ", "").replace(".", "").replace(",", "").replace("!", "")
    #         if lower_input in ["lets buckle up", "let's buckle up", "buckle up"]:
    #             result = await self._handle_buckle_up()
    #             task.agent_used = "system"
    #             last_provider = getattr(self.router, 'last_provider_used', None) or "ollama"
    #             await self.conv_store.save("manager", result, intent="system", model_used=str(last_provider))
    #             return result
    #
    #         intent = self._classify_intent(user_input)
    #
    #         if intent == "system":
    #             result = await self._handle_system_query(user_input)
    #         elif intent == "conversation":
    #             result = await self._handle_conversation(user_input, context_messages)
    #         else:
    #             # P0-8: Route through swarm for non-conversation intents
    #             if self.swarm:
    #                 result = await self.swarm.dispatch(
    #                     request=user_input, intent=intent,
    #                     context={"history": context_messages}
    #                 )
    #             else:
    #                 agent = self.agents.get(intent)
    #                 if agent:
    #                     result = await agent.execute(user_input, {"history": context_messages})
    #                 else:
    #                     result = await self._handle_conversation(user_input, context_messages)
    #             task.agent_used = intent
    #
    #         # P1-6: Review loop uses last_provider_used, not working_providers[0]
    #         last_provider = getattr(self.router, 'last_provider_used', None) or "ollama"
    #         is_local = "ollama" in str(last_provider).lower()
    #
    #         if not is_local and result and len(result) > 100:
    #             result = await self._light_review(user_input, result)
    #
    #         final = result or "Sir, I didn't get a response. Please try again."
    #         await self.conv_store.save("manager", final, intent=intent,
    #                                     model_used=str(last_provider))
    #         return final
    #
    #     except Exception as e:
    #         logger.error(f"Task {task.id} failed: {e}")
    #         err = f"Sir, I hit an error: {str(e)[:80]}. Please try again."
    #         await self.conv_store.save("manager", err, intent="error")
    #         return err

    async def process(self, user_input, input_type='text'):
        user_input = user_input.strip()
        if not user_input:
            return 'Sir, enter a message or command.'
        async with self._process_lock:
            # Snapshot BEFORE saving the new user turn, so it appears once in the prompt.
            context = self.conv_store.get_context_messages(20)
            await self.conv_store.save('user', user_input)
            intent = self._classify_intent(user_input)
            career = getattr(self, 'agents', {}).get('career')
            resume_workflow = getattr(career, 'resume_workflow', None)
            resume_followup = resume_workflow and resume_workflow.accepts_followup(user_input, intent)
            document_work = getattr(self, 'document_work', None)
            builder = getattr(self, 'agents', {}).get('builder')
            project_work = getattr(builder, 'project_work', None)
            try:
                director = getattr(self, 'goal_director', None)
                decision = await director.resolve(user_input, intent, context) if director else None
                task_context = {'history': context}
                if director and not director.protected(user_input):
                    from core.task_context import retrieve_task_context, render_task_context
                    evidence = await asyncio.to_thread(retrieve_task_context, self.config, user_input, context)
                    task_context['memory_evidence'] = render_task_context(evidence)
                if decision and decision.get('reply'):
                    intent = 'work_status'
                    result = decision['reply']
                elif decision and decision.get('kind'):
                    kind = decision['kind']
                    if decision.get('workflow_id'):
                        task_context['workflow_id'] = decision['workflow_id']
                    task_context['new_goal'] = not bool(decision.get('workflow_id'))
                    workflow = {'project': project_work, 'document': document_work, 'resume': resume_workflow}[kind]
                    if workflow is None:
                        raise RuntimeError('Selected workflow is not available')
                    intent = {'project':'builder','document':'document_work','resume':'career'}[kind]
                    result = await workflow.submit(decision['request'], task_context)
                    director.remember(kind, decision.get('workflow_id'))
                elif project_work and project_work.accepts_followup(user_input, intent):
                    intent = 'builder'
                    result = await project_work.submit(user_input, task_context)
                    if director: director.remember('project')
                elif intent == 'builder' and 'builder' in getattr(self, 'agents', {}):
                    result = await self.agents['builder'].execute(user_input, task_context)
                    if director: director.remember('project')
                elif resume_followup:
                    intent = 'career'
                    result = await career._handle_resume(user_input, task_context)
                    if director: director.remember('resume')
                elif document_work and document_work.matches(user_input, intent):
                    intent = 'document_work'
                    result = await document_work.submit(user_input, task_context)
                    if director: director.remember('document')
                elif user_input.lower().strip(" .!,") in ["lets buckle up", "let's buckle up", "buckle up"]:
                    result = await self._handle_buckle_up()
                elif intent == 'system':
                    result = await self._handle_system_query(user_input)
                elif intent == 'conversation_memory':
                    result = await self.agents['conversation'].execute(user_input, {'history': context})
                elif intent == 'conversation':
                    result = await self._handle_conversation(user_input, context, task_context.get('memory_evidence', ''))
                elif self.swarm:
                    result = await self.swarm.dispatch(user_input, intent, {'history': context})
                else:
                    result = await self.agents[intent].execute(user_input, {'history': context})
                final = result or 'Sir, the action returned no result.'
            except Exception as exc:
                logger.error(f'Task failed ({intent}): {type(exc).__name__}')
                final = f'Sir, the {intent} task failed ({type(exc).__name__}). No completion was confirmed.'
            # Preserve actual tool output. A second LLM review cannot validate an action.
            await self.conv_store.save('manager', final, intent=intent,
                                       model_used=str(self.router.last_provider_used or 'local command'))
            return final

    # Superseded 2026-10-12: retained for rollback; corrected implementation below.
    # def _classify_intent(self, text: str) -> str:
    #     lower = text.lower()
    #     for intent, keywords in self.INTENT_MAP.items():
    #         if any(kw in lower for kw in keywords):
    #             return intent
    #     return "conversation"

    def _classify_intent(self, text):
        from core.routing import classify
        return classify(text, self.INTENT_MAP)

    # Superseded 2026-10-12: retained for rollback; corrected implementation below.
    # async def _handle_buckle_up(self) -> str:
    #     from core.activity_tracker import get_recent_activities
    #     activities = get_recent_activities(30)
    #
    #     activities_summary = ""
    #     if activities:
    #         # Sort by timestamp descending
    #         activities_summary = "\n".join([
    #             f"- {act['agent'].capitalize()} Agent: {act['activity']}"
    #             for act in reversed(activities)
    #         ])
    #     else:
    #         activities_summary = "No recent background activity logged."
    #
    #     career_agent = self.agents.get("career")
    #     career_active = False
    #     career_search = ""
    #     if career_agent and getattr(career_agent, "active_apply_task", None) and not career_agent.active_apply_task.done():
    #         career_active = True
    #         career_search = getattr(career_agent, "current_job_search", "")
    #
    #     status_context = f"""
    # ground Activity Logs:
    # ivities_summary}
    #
    # ent Active Systems:
    # reer Agent Background Loop: {'ACTIVE' if career_active else 'INACTIVE'}{f' (Searching and applying for: "{career_search}")' if career_active else ''}
    # ading Alert Manager: ACTIVE (monitoring watchlists for price target alerts)
    # mmunication Agent Call Screening: STANDBY (monitoring incoming recruiter calls)
    #     #
    #     system_prompt = """
    # are Manager — Anant's personal AI operating system (J.A.R.V.I.S. style).
    # t has just returned home and said "lets buckle up".
    # hesize a professional, briefing update summarizing the background activities and current system status.
    # ess Anant as "Sir" and speak in a warm, devoted, and executive worker tone.
    # oncise (around 150-200 words) but cover all important updates. Do not ask questions at the end.
    #     #     return await self.router.complete(
    #         system=system_prompt,
    #         messages=[{"role": "user", "content": f"Please compile the status report based on this data:\n{status_context}"}],
    #         task_type="conversation"
    #     )

    async def _handle_buckle_up(self):
        from core.activity_tracker import get_recent_activities
        activities = get_recent_activities(8)
        lines = ['Welcome back, Sir.', await self._handle_system_query('status')]
        if activities:
            lines.append('Recorded activity (historical entries may predate this session):')
            lines.extend(f"- {a.get('timestamp', '')}: {a.get('agent', '')}: {a.get('activity', '')}" for a in activities)
        else:
            lines.append('No background activity recorded.')
        return '\n'.join(lines)

    async def _handle_conversation(self, user_input: str, context: List[Dict], memory_evidence='') -> str:
        messages = context + [{"role": "user", "content": user_input}]
        return await self.router.complete(
            system=self.PERSONALITY_SYSTEM_PROMPT + '\n' + memory_evidence + '''
Current executable workflows: local software projects with architecture/build/test/repair;
source-backed resumes; local document find/read/write; saved tasks/reminders and supported file/app commands.
The conversation response itself executes no tools. Never claim a job started, a file saved,
or an external action completed unless its result is in the current context. When asked about
movie-style JARVIS, acknowledge the goal while describing measured capabilities accurately.''',
            messages=messages, task_type="conversation"
        )

    # Superseded 2026-10-12: retained for rollback; corrected implementation below.
    # async def _handle_system_query(self, user_input: str) -> str:
    #     lower = user_input.lower()
    #     if any(w in lower for w in ["which api", "which model", "what model", "using right now"]):
    #         s = self.router.get_status()
    #         last = s.get("last_provider") or (s.get("working_providers", ["ollama"])[0])
    #         working = s.get("working_providers", [])
    #         calls = {k: v for k, v in s.get("call_counts", {}).items() if v > 0}
    #         calls_str = ", ".join(f"{k}: {v}" for k, v in calls.items()) or "none yet"
    #         return (f"Sir, I'm currently using: **{last}**\n\n"
    #                 f"Working providers: {', '.join(working) or 'Ollama (local only)'}\n"
    #                 f"Calls today: {calls_str}")
    #
    #     if any(w in lower for w in ["second laptop", "background server", "background machine"]):
    #         try:
    #             import main
    #             sec_data = getattr(main, 'second_laptop_data', {})
    #         except ImportError:
    #             sec_data = {}
    #         if "second_laptop_health" in sec_data:
    #             h = sec_data["second_laptop_health"]
    #             tasks = h.get("tasks_running", {})
    #             tasks_str = ", ".join(f"{k}: {'active' if v else 'inactive'}" for k, v in tasks.items())
    #             return (f"**Second Laptop Status (Synced Background Server):**\n\n"
    #                     f"• Machine: i5-8250U | 12GB RAM\n"
    #                     f"• Last Synced: {h.get('timestamp')}\n"
    #                     f"• CPU Usage: {h.get('cpu_pct')}% | RAM Usage: {h.get('ram_pct')}%\n"
    #                     f"• Disk Free: {h.get('disk_free_gb')} GB\n"
    #                     f"• Running Tasks: {tasks_str}")
    #         return "Sir, I don't have any background telemetry data from the second laptop yet. Please ensure the background server daemon is active on that machine."
    #
    #     if any(w in lower for w in ["status", "all systems", "agents", "are you working"]):
    #         agent_statuses = await self.health.get_all_statuses()
    #         hw = self.health.get_hardware_summary()
    #         lines = [f"  {'✓' if v['healthy'] else '✗'} {k.replace('_',' ').title()}"
    #                  for k, v in agent_statuses.items()]
    #         hw_str = ""
    #         if hw.get("available"):
    #             hw_str = (f"\n\n**Hardware:** CPU {hw['cpu_pct']:.0f}% | "
    #                       f"RAM {hw['ram_pct']:.0f}% ({hw['ram_used_gb']:.1f}/{hw['ram_total_gb']:.1f}GB) | "
    #                       f"Disk {hw['disk_free_gb']:.0f}GB free")
    #         working = self.router.working_providers
    #         return (f"**Agent Status:**\n" + "\n".join(lines) +
    #                 f"\n\n**AI:** {', '.join(working[:2]) or 'Ollama (local)'}" + hw_str)
    #
    #     return await self._handle_conversation(
    #         user_input, self.conv_store.get_context_messages(10)
    #     )

    async def _handle_system_query(self, user_input):
        state = self.router.get_status()
        lower = user_input.lower()
        if any(w in lower for w in ['which api', 'which model', 'what model', 'providers']):
            return (f"Sir, last provider: {state.get('last_provider') or 'none used yet'}. "
                    f"Model: {state.get('last_model') or 'none used yet'}.\n"
                    f"Verified available: {', '.join(state['working_providers']) or 'none yet'}. "
                    'Open Connections for each provider’s current state.')
        if any(w in lower for w in ['capabilities', 'what can you']):
            return ('Sir, I can save tasks and timed reminders, search/read/create text files, open supported apps, '
                    'retrieve conversation history, and generate drafts, code and plans with a connected AI. '
                    'WhatsApp and LinkedIn automation need browser sign-in. Recruiter calls are a simulation; '
                    'live trading, email sending and social publishing are not connected.')
        lines = ['Sir, Manager OS is running.',
                 f"AI verified available: {', '.join(state['working_providers']) or 'none yet'}.",
                 f'Agents loaded: {len(self.agents)}. Loaded does not mean an external account is connected.']
        if self.swarm:
            lines.append(f'Active requests: {len(self.swarm.active_tasks)}.')
        life = self.agents.get('life')
        if life and hasattr(life, 'tasks'):
            lines.append(f'Open tasks: {len(life.tasks.list())}.')
        career = self.agents.get('career')
        running = career and getattr(career, 'active_apply_task', None)
        lines.append('Career browser loop: ' + ('running' if running and not running.done() else 'stopped') + '.')
        return '\n'.join(lines)

    async def _light_review(self, request: str, output: str) -> str:
        """Minimal review — only for cloud models, only if output seems off."""
        if len(output) < 80:
            return output
        try:
            review = await self.router.complete(
                system="Reply only YES or NO.",
                messages=[{"role": "user",
                           "content": f"Does this answer '{request[:80]}'? Output: '{output[:200]}'. YES or NO only."}],
                task_type="review", max_tokens=5
            )
            if "NO" in review.upper():
                logger.warning("Review: output off-topic — retrying")
                return await self._handle_conversation(
                    request, self.conv_store.get_context_messages(5)
                )
        except Exception:
            pass
        return output

    def get_morning_briefing(self, hw: dict = None, working_providers: list = None) -> str:
        now = datetime.now()
        hw = hw or {}
        providers = working_providers or ["Ollama (local)"]
        provider_str = ", ".join(providers[:2])
        ram_note = ""
        if hw.get("ram_pct", 0) > 85:
            ram_note = f" RAM at {hw['ram_pct']:.0f}% — consider closing unused apps."
        return (
            f"Good morning, Sir. Today is {now.strftime('%A, %d %B %Y')}. "
            f"It's {now.strftime('%H:%M')}.\n\n"
            f"**System Status:** All agents online. Running on {provider_str}.{ram_note}\n\n"
            f"Say 'add task' to log today's objectives, "
            f"or 'trading briefing' for market summary, Sir."
        )

    async def speak(self, text: str):
        try:
            await self.voice.speak(text)
        except Exception as e:
            logger.error(f"Speak error: {e}")

    async def shutdown(self):
        self.active = False
        try:
            await self.health.stop()
        except Exception:
            pass
        try:
            await self.conv_store.close()
        except Exception:
            pass
        logger.info("Manager shutdown complete")

    def _time_of_day(self) -> str:
        h = datetime.now().hour
        if 5 <= h < 12: return "morning"
        if 12 <= h < 17: return "afternoon"
        return "evening"
