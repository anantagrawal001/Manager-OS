"""
MANAGER OS — Communication Agent
══════════════════════════════════
FILE: agents/communication_agent.py
CREATED: 2026-05-24 | Claude Sonnet 4.6
PURPOSE: Complete communication management.
         - Takes calls on behalf of Anant when unavailable
         - Manages WhatsApp, Gmail, direct messages
         - Drafts replies matching Anant's tone and style
         - Prioritizes inbox — flags urgent, can-wait, ignore
         - Cold outreach campaign management with follow-up sequences

DO NOT DELETE ANY CODE — comment out with reason and date
"""

from typing import Dict, Any, List
import json
import os
from loguru import logger
from agents.base_agent import BaseAgent
from core.browser_automation import send_whatsapp_message, create_whatsapp_group
from core.poster_generator import generate_invite_poster
from core.activity_tracker import log_activity


class CommunicationAgent(BaseAgent):
    """
    Complete communication management for Manager OS.
    Handles all inbound and outbound communications on Anant's behalf.
    """

    COMMUNICATION_SYSTEM = """
You are Anant's personal communication manager. You:
- Draft messages in Anant's professional but warm tone
- Always represent Anant appropriately — never embarrass him
- Prioritize clearly: Urgent (respond now) | Normal (respond today) | Low (respond when free) | Ignore
- For calls you handle: professional, calm, gather key info, commit to nothing without Anant's approval
- Write subject lines that get opened
- Keep messages concise but complete
"""

    async def execute(self, request: str, context: Dict[str, Any]) -> str:
        req_lower = request.lower()

        if any(w in req_lower for w in ["simulate", "simulation", "test"]) and any(w in req_lower for w in ["call", "recruiter", "phone"]):
            return await self._simulate_recruiter_call(request, context)
        elif any(w in req_lower for w in ["call", "phone", "answer", "incoming"]):
            return await self._handle_call_brief(request, context)
        elif any(w in req_lower for w in ["email", "gmail", "inbox", "mail"]):
            return await self._handle_email(request, context)
        elif any(w in req_lower for w in ["whatsapp", "message", "dm", "reply"]):
            return await self._handle_message(request, context)
        elif any(w in req_lower for w in ["outreach", "campaign", "follow up", "follow-up"]):
            return await self._handle_outreach(request, context)
        elif any(w in req_lower for w in ["priority", "inbox", "urgent", "sort"]):
            return await self._handle_inbox_priority(request, context)
        else:
            return await self._ask_ai(request, system=self.COMMUNICATION_SYSTEM)

    async def _handle_call_brief(self, request: str, context: Dict) -> str:
        """Generate call briefing or handle call transcript"""
        prompt = f"""
{request}

For call management:
1. Call summary: Who called, when, what they wanted
2. Urgency rating: CRITICAL | HIGH | NORMAL | LOW
3. Action required from Sir: Yes/No — what specifically
4. Suggested response if Sir wants to call back
5. Was anything committed to the caller? (NEVER commit without Sir's approval)

If this is an incoming call to handle:
- Greet as: "Thank you for calling. This is Anant's personal assistant. How can I help you?"
- Gather: Name, purpose, callback number, urgency
- Commit to nothing: "I'll make sure Anant gets your message and follows up."
"""
        return await self.router.complete(
            system=self.COMMUNICATION_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            task_type="conversation"
        )

    async def _handle_email(self, request: str, context: Dict) -> str:
        """Email drafting and inbox management"""
        prompt = f"""
{request}

For email management:
- Draft emails that sound like Anant wrote them (professional but human)
- Subject lines: specific, compelling, relevant
- Body: clear ask, appropriate length, strong close
- If managing inbox: categorize by urgency, draft quick replies for routine items

Email drafting format:
Subject: [subject line]
---
[email body]
---
Tone check: [how does this read — professional/warm/urgent/casual?]
"""
        return await self.router.complete(
            system=self.COMMUNICATION_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            task_type="writing"
        )

    # Superseded 2026-10-12: retained for rollback; corrected implementation below.
    # async def _handle_message(self, request: str, context: Dict) -> str:
    #     """WhatsApp message sending & group creation automation"""
    #     logger.info(f"CommunicationAgent: processing WhatsApp request: {request}")
    #
    #     # We ask the AI to parse the unstructured prompt into structured instruction parameters
    #     parser_prompt = f"""
    # yze this WhatsApp / communication request from the user: "{request}"
    #
    # tify if this is a request to send a message, create a group, or send a party/event invitation.
    # rate a JSON object matching this structure:
    #     # ntent": "send_message" or "create_group" or "send_invite",
    # ecipient": "name of contact (e.g. John)" or ["recipient 1", "recipient 2"] if multiple/group,
    # essage": "the actual text message drafted to be sent. If it is an invite, include time, date, venue details neatly.",
    # oster_required": true if they requested an invite, poster, party invite, or sending photo/image, false otherwise,
    # oster_details": {{
    #  "title": "the name of the party/event",
    #  "details": "Date, Time, Venue, RSVP instructions",
    #  "theme": "party/celebration/meeting/general"
    #  or null,
    # roup_name": "the name of the group if they want to create a group" or null
    #     #
    # rn ONLY valid JSON. Do not include any backticks, markdown, explanation or commentary.
    #     #     raw_response = ""
    #     try:
    #         raw_response = await self.router.complete(
    #             system="You are a precise data extraction agent. You output ONLY valid raw JSON.",
    #             messages=[{"role": "user", "content": parser_prompt}],
    #             task_type="writing"
    #         )
    #         # Strip markdown formatting if the model wrapped it
    #         cleaned = raw_response.strip().replace("```json", "").replace("```", "").strip()
    #         data = json.loads(cleaned)
    #     except Exception as e:
    #         logger.error(f"Failed to parse structured WhatsApp request: {e}. Raw: {raw_response}")
    #         # Fallback parsing
    #         data = {
    #             "intent": "send_message",
    #             "recipient": "John",  # default fallback if unextractable
    #             "message": request,
    #             "poster_required": False,
    #             "poster_details": None,
    #             "group_name": None
    #         }
    #
    #     intent = data.get("intent", "send_message")
    #     recipient = data.get("recipient", "Unknown")
    #     message = data.get("message", "")
    #     poster_required = data.get("poster_required", False)
    #
    #     logger.info(f"Structured request parsed: intent={intent}, recipient={recipient}, poster={poster_required}")
    #
    #     poster_path = None
    #     if poster_required and data.get("poster_details"):
    #         # Generate the poster
    #         p_details = data["poster_details"]
    #         title = p_details.get("title", "Invitation")
    #         p_text = p_details.get("details", "")
    #         theme = p_details.get("theme", "party")
    #         poster_path = os.path.abspath("./logs/invite_poster.png")
    #         try:
    #             await generate_invite_poster(
    #                 title=title,
    #                 details=p_text,
    #                 theme=theme,
    #                 output_path=poster_path,
    #                 config=self.config
    #             )
    #             logger.info(f"Invitation poster generated at {poster_path}")
    #         except Exception as ex:
    #             logger.error(f"Failed to generate poster: {ex}")
    #             poster_path = None
    #
    #     success = False
    #     if intent == "create_group":
    #         contacts = recipient if isinstance(recipient, list) else [recipient]
    #         g_name = data.get("group_name") or "New Group"
    #         # Trigger group creation
    #         success = await create_whatsapp_group(g_name, contacts, message, poster_path)
    #         if success:
    #             return f"Sir, I have successfully created the WhatsApp group '{g_name}' with {', '.join(contacts)} and sent the message."
    #         else:
    #             return f"Sir, I tried to create the WhatsApp group '{g_name}' but encountered an automation failure. Please ensure WhatsApp Web is authenticated."
    #     else:
    #         # Direct send message (either text or text+poster)
    #         # If recipient is a list, send to the first one or iterate. We'll send to the first matching name.
    #         target_contact = recipient[0] if isinstance(recipient, list) else recipient
    #         success = await send_whatsapp_message(target_contact, message, poster_path)
    #
    #         if success:
    #             if poster_path:
    #                 return f"Sir, I have successfully generated the poster and sent the invitation to {target_contact} via WhatsApp."
    #             else:
    #                 return f"Sir, I have successfully sent the WhatsApp message to {target_contact}."
    #         else:
    #             return f"Sir, I was unable to send the WhatsApp message to {target_contact}. Please make sure you are logged in to WhatsApp Web on the browser window."

    async def _handle_message(self, request, context):
        import re
        # Parse only explicitly addressed send commands; never invent a fallback contact.
        match = re.fullmatch(r'(?:please )?send (?:a )?(?:whatsapp(?: message)?|message on whatsapp) to (.+?):\s*(.+)', request.strip(), re.I | re.S)
        if not match:
            match = re.fullmatch(r'(?:please )?send (?:a )?message to (.+?) on whatsapp:\s*(.+)', request.strip(), re.I | re.S)
        if not match:
            return ('Sir, to send an exact message use "send WhatsApp to Contact Name: your message". '
                    'Include the recipient and the full message. No message has been sent.')
        recipient, message = match[1].strip(), match[2].strip()
        if not recipient or not message:
            return 'Sir, include both the contact name and the message.'
        success = await send_whatsapp_message(recipient, message)
        if success:
            return f'Sir, WhatsApp shows your outgoing message to {recipient}.'
        return ('Sir, delivery was not confirmed. Check the automation browser and sign in to WhatsApp Web if needed. '
                'Inspect the conversation before repeating the command.')

    async def _handle_outreach(self, request: str, context: Dict) -> str:
        """Cold outreach campaign with follow-up sequences"""
        prompt = f"""
{request}

Design a complete outreach sequence:
1. Email 1 (Day 1): Hook + value proposition + CTA
2. Follow-up 1 (Day 4): Add new value, reference first email
3. Follow-up 2 (Day 10): Last attempt, create FOMO
4. LinkedIn connection message (short, personal)

Rules:
- Each touchpoint adds new value — never just "following up"
- Personalization tokens: [Name], [Company], [Recent news/achievement]
- Max 50 BCC per send to avoid spam
- Clear unsubscribe signal: "Reply STOP to opt out"
"""
        return await self.router.complete(
            system=self.COMMUNICATION_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            task_type="writing",
            max_tokens=2000
        )

    async def _handle_inbox_priority(self, request: str, context: Dict) -> str:
        """Inbox prioritization"""
        return (
            "Sir, to prioritize your inbox I'll need access to your Gmail. "
            "Run the Gmail OAuth setup and I'll have your inbox sorted by urgency — "
            "only showing you what actually needs your attention."
        )

    async def get_status(self) -> Dict:
        return {"healthy": True, "state": "running", "agent": "CommunicationAgent"}

    async def _simulate_recruiter_call(self, request: str, context: Dict) -> str:
        """Simulate screening / interview call on behalf of Anant"""
        if not hasattr(self, 'manager') or not self.manager:
            return "Sir, I cannot access the voice engine from this agent context."

        logger.info("Starting recruiter call simulation...")

        # Step 1: Assistant speaks the initial greeting
        greeting = (
            "Hello, this is Anant's personal assistant speaking. "
            "Anant is currently away, but I can answer initial screening questions "
            "or schedule an interview. May I know who is calling and what role this is for?"
        )

        log_activity("communication", "Answering incoming recruiter call: screening initiated.")
        await self.manager.speak(greeting)

        # Step 2: Listen for response
        logger.info("Listening for recruiter's response...")
        recruiter_speech = await self.manager.voice.listen()
        if not recruiter_speech:
            # Safe mock fallback if mic is silent/not connected
            # Removed fabricated recruiter response (2026-10-12).
            return "Sir, no speech was detected in the call simulation. No real call was connected."

        log_activity("communication", f"Recruiter said: '{recruiter_speech}'")

        # Step 3: Run AI router to generate assistant's answer based on resume details
        system_prompt = """
You are Anant's personal AI assistant answering a recruiter's call. 
You speak in a professional, warm, and clear manner.
You represent Anant. Keep answers brief (1-3 sentences) as this is spoken conversation.
Provide high-quality screening answers, scheduling help, or write down a call message.
"""
        response = await self.router.complete(
            system=system_prompt,
            messages=[{"role": "user", "content": f"Recruiter said: {recruiter_speech}"}],
            task_type="conversation"
        )

        # Step 4: Speak response
        log_activity("communication", f"Assistant responded: '{response}'")
        await self.manager.speak(response)

        # Step 5: Final goodbye
        goodbye = "Thank you for calling. I'll make sure Anant gets these details and gets back to you. Have a great day!"
        await self.manager.speak(goodbye)
        log_activity("communication", "Recruiter call completed and message logged.")

        return f"Sir, the recruiter call simulation completed. No telephone call was connected. Simulation transcript: '{recruiter_speech}'. I answered: '{response}'."
