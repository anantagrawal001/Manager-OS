"""
MANAGER OS — Career Agent
══════════════════════════
FILE: agents/career_agent.py
CREATED: 2026-05-24 | Claude Sonnet 4.6
PURPOSE: Complete career management.
         - Resume auto-tailoring (Google XYZ formula, ATS-optimized)
         - Job portal scanning (LinkedIn, Naukri, Indeed, Wellfound)
         - Cold email outreach with personalized templates
         - Interview preparation (mock interviews, scoring, model answers)
         - Recruiter email extraction

GOOGLE XYZ FORMULA: "Accomplished X as measured by Y by doing Z"
Every bullet point must follow this formula — specificity = results.

DO NOT DELETE ANY CODE — comment out with reason and date
"""

from typing import Dict, Any
import asyncio
from loguru import logger
from agents.base_agent import BaseAgent
from core.activity_tracker import log_activity


class CareerAgent(BaseAgent):
    """
    Complete career management agent.
    Handles the full job application pipeline autonomously.
    """

    def __init__(self, config: dict, router, firewall):
        super().__init__(config, router, firewall)
        self.active_apply_task = None
        self.current_job_search = None
        from core.workflows import ResumeWorkflow
        self.resume_workflow = ResumeWorkflow(config, router)

    RESUME_SYSTEM = """
You are an elite resume writer and career coach. You specialize in:
- ATS optimization (Applicant Tracking System)
- The Google XYZ formula: "Accomplished X as measured by Y by doing Z"
- Keyword matching for specific job descriptions
- Making every bullet point quantified and specific
- Removing irrelevant experience
- Tailored professional summaries

Format: Clean, professional, ATS-friendly. Every achievement quantified.
Never invent experience, qualifications or metrics. Use only details supplied by the user.
Never use vague language like "responsible for" or "helped with".
"""

    INTERVIEW_SYSTEM = """
You are a senior hiring manager at a top tech company with 15 years of recruiting experience.
You conduct rigorous, realistic interview simulations.
You ask the hardest questions for the specific role.
You score answers 1-10 with specific feedback.
You show what a perfect 10/10 answer looks like.
"""

    async def execute(self, request: str, context: Dict[str, Any]) -> str:
        req_lower = request.lower()

        if any(w in req_lower for w in ["start", "run", "begin", "launch", "continuous"]) and any(w in req_lower for w in ["job", "apply", "loop"]):
            return await self._start_job_loop(request, context)
        elif any(w in req_lower for w in ["stop", "cancel", "terminate", "kill", "end"]) and any(w in req_lower for w in ["job", "apply", "loop"]):
            return await self._stop_job_loop(request, context)
        elif any(w in req_lower for w in ["resume", "cv", "application"]):
            return await self._handle_resume(request, context)
        elif any(w in req_lower for w in ["interview", "mock", "prepare", "prep"]):
            return await self._handle_interview(request, context)
        elif any(w in req_lower for w in ["job", "apply", "search", "opening", "position"]):
            return await self._handle_job_search(request, context)
        elif any(w in req_lower for w in ["cold email", "recruiter", "outreach", "contact"]):
            return await self._handle_cold_email(request, context)
        else:
            return await self._ask_ai(request, system=self.RESUME_SYSTEM, task_type="writing")

    async def _handle_resume_legacy(self, request: str, context: Dict) -> str:
        """Tailor resume for a specific job"""
        prompt = f"""
{request}

Apply the complete resume optimization process:

1. DIAGNOSE: What's weak, what's missing, what ATS will flag
2. MATCH KEYWORDS: Extract top 15 keywords from the job description
3. REWRITE using Google XYZ formula for every bullet:
   "Accomplished [X] as measured by [Y] by doing [Z]"
4. SUMMARY: Write a tailored 3-sentence professional summary
5. SCORE: Rate the final resume out of 100 for this specific role

If no job description provided, ask for it first.
If no current resume provided, ask for it.

Format output cleanly. Be specific — no vague language.
"""
        return await self.router.complete(
            system=self.RESUME_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            task_type="writing",
            max_tokens=3000
        )

    # 2026-10-12: replace prompt-only resume advice with persistent evidence-backed work.
    async def _handle_resume(self, request: str, context: Dict) -> str:
        return await self.resume_workflow.submit(request, context)

    async def _handle_interview(self, request: str, context: Dict) -> str:
        """Interview preparation and mock interviews"""
        prompt = f"""
{request}

For interview preparation:
1. Research the company's interview style and process
2. Generate the 10 most likely technical questions for this role
3. Generate the 5 most likely behavioral questions (STAR format)
4. For each question, provide:
   - The question
   - What they're really testing
   - A model 10/10 answer
   - Common mistakes to avoid

If this is a mock interview request, ask one question at a time and wait for the answer.
Score each answer 1-10 with specific feedback.
"""
        return await self.router.complete(
            system=self.INTERVIEW_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            task_type="conversation",
            max_tokens=3000
        )

    async def _handle_job_search(self, request: str, context: Dict) -> str:
        """Job search and application strategy"""
        prompt = f"""
{request}

Provide a structured job search plan:
1. Target companies list (10-15 matching the role/experience)
2. Key job boards to monitor (LinkedIn, Naukri, Indeed, Wellfound, AngelList)
3. Search keywords to use
4. LinkedIn outreach message template
5. Daily action plan (how many applications per day)

Also explain: How to find the recruiter's direct email using Apollo.io or Hunter.io
and how to send batch cold emails (max 50 BCC to avoid spam flags).
"""
        return await self.router.complete(
            system=self.RESUME_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            task_type="writing",
            max_tokens=2000
        )

    async def _handle_cold_email(self, request: str, context: Dict) -> str:
        """Cold email outreach to recruiters"""
        prompt = f"""
{request}

Write a high-converting cold email to a recruiter/hiring manager.

Format:
Subject: [Specific, attention-grabbing, role-relevant]

Body:
- Hook: One impressive specific achievement (quantified)
- Connect: Why this specific company
- Ask: Clear, low-friction call to action (15-min call, not "please hire me")
- Signature: Professional

Rules:
- Under 150 words total
- Specific — no generic templates
- One impressive data point that proves value
- No attachments in first email
- BCC etiquette: Max 50 recipients, personalize key details

Also provide: Subject line A/B test variants (2 alternatives)
"""
        return await self.router.complete(
            system=self.RESUME_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            task_type="writing",
            max_tokens=1000
        )

    async def get_status(self) -> Dict:
        return {"healthy": True, "state": "running", "agent": "CareerAgent"}


# ─── NEW 2026-05-27: Accept/Reject Keyword Workflow (Reel 16 — Jobsuit.ai style) ──

    async def _interactive_keyword_tailor(self, resume_text: str, job_desc: str) -> str:
        """
        Presents Sir with accept/reject keyword suggestions before finalizing resume.
        Human-in-the-loop control — Sir approves each keyword insertion.
        Reel 16 insight: Let Sir decide which keywords to accept, not just auto-insert all.
        """
        # Step 1: Extract keywords from job description
        keyword_prompt = f"""
Analyze this job description and extract the TOP 15 most important keywords/skills
that an ATS system would screen for.

Job Description:
{job_desc[:2000]}

Return as JSON array: [{{"keyword": "...", "importance": "HIGH/MEDIUM/LOW", "context": "why this matters"}}]
Return ONLY the JSON array, no other text.
"""
        keywords_raw = await self.router.complete(
            system="You are an ATS expert. Return only valid JSON.",
            messages=[{"role": "user", "content": keyword_prompt}],
            task_type="reasoning"
        )

        # Step 2: Check which keywords are already in resume
        try:
            import json as _json
            clean = keywords_raw.strip().strip("```json").strip("```").strip()
            keywords = _json.loads(clean)
        except Exception:
            keywords = []

        if not keywords:
            return await self._handle_resume(f"Tailor this resume:\n{resume_text}\n\nFor this job:\n{job_desc}", {})

        # Step 3: Build accept/reject presentation
        already_present = []
        to_add = []

        for kw in keywords:
            keyword = kw.get("keyword", "")
            if keyword.lower() in resume_text.lower():
                already_present.append(keyword)
            else:
                to_add.append(kw)

        present_list = ", ".join(already_present) if already_present else "None"
        add_lines = "\n".join(
            f"  {i+1}. [{kw.get('importance','?')}] {kw.get('keyword','')} — {kw.get('context','')[:60]}"
            for i, kw in enumerate(to_add)
        )

        return (
            f"**Resume Keyword Analysis**\n\n"
            f"✅ Already in your resume ({len(already_present)}):\n{present_list}\n\n"
            f"📌 Keywords to consider adding ({len(to_add)}):\n{add_lines}\n\n"
            f"Sir, say:\n"
            f"  • 'accept all' — add all keywords naturally to resume\n"
            f"  • 'accept 1,3,5' — add specific keywords by number\n"
            f"  • 'reject 2,4' — skip those keywords\n"
            f"  • 'finalize' — generate the complete tailored resume now\n\n"
            f"Or just say 'accept all and generate resume' to do it in one step."
        )

    async def _start_job_loop(self, request: str, context: Dict) -> str:
        if self.active_apply_task and not self.active_apply_task.done():
            return f"Sir, the LinkedIn job application loop is already running for: '{self.current_job_search}'."

        # Extract keywords using AI
        keywords = await self._ask_ai(
            f"Identify the job role / keywords the user wants to search for on LinkedIn from this request: '{request}'. "
            "Return ONLY the exact keywords, e.g. 'Python Developer'. Do not include any other words or punctuation.",
            system="You are a data extractor. Return clean text only."
        )
        keywords = keywords.strip().replace("`","").replace("'","").replace("\"","")
        if not keywords or len(keywords) < 2:
            keywords = "Software Engineer"

        profile_key = "main"
        if "work" in request.lower():
            profile_key = "work"
        elif "personal" in request.lower():
            profile_key = "personal"

        self.current_job_search = keywords
        self.active_apply_task = asyncio.create_task(self._run_job_application_loop(keywords, profile_key))

        log_activity("career", f"Started background job application loop for: '{keywords}' on profile: '{profile_key}'")
        return f"Sir, I started background LinkedIn job search for: '{keywords}' on Chrome profile '{profile_key}'. Listings are saved for review; applications are not submitted automatically."

    async def _stop_job_loop(self, request: str, context: Dict) -> str:
        if not self.active_apply_task or self.active_apply_task.done():
            return "Sir, there is no active job application loop currently running."

        self.active_apply_task.cancel()
        self.active_apply_task = None
        log_activity("career", f"Stopped background job application loop for: '{self.current_job_search}'")
        return f"Sir, I have stopped the background job application loop for: '{self.current_job_search}'."

    # Superseded 2026-10-12: retained for rollback; corrected implementation below.
    # async def _run_job_application_loop(self, keywords: str, profile_key: str):
    #     logger.info(f"CareerAgent background loop started for: {keywords}")
    #     from core.browser_automation import get_browser_context
    #     from playwright.async_api import async_playwright
    #     import urllib.parse
    #
    #     try:
    #         async with async_playwright() as p:
    #             context = await get_browser_context(p, profile_key=profile_key)
    #             page = await context.new_page()
    #
    #             encoded_kw = urllib.parse.quote(keywords)
    #             search_url = f"https://www.linkedin.com/jobs/search/?keywords={encoded_kw}"
    #
    #             logger.info(f"Navigating to LinkedIn Job Search: {search_url}")
    #             await page.goto(search_url)
    #             await page.wait_for_timeout(5000)
    #
    #             log_activity("career", f"Opened LinkedIn search for: '{keywords}'")
    #
    #             job_selectors = [
    #                 'li.jobs-search-results__list-item',
    #                 'div.job-card-container',
    #                 'a.job-card-list__title'
    #             ]
    #
    #             while True:
    #                 job_elements = []
    #                 for sel in job_selectors:
    #                     loc = page.locator(sel)
    #                     count = await loc.count()
    #                     if count > 0:
    #                         job_elements = [loc.nth(i) for i in range(count)]
    #                         break
    #
    #                 if not job_elements:
    #                     logger.warning("No LinkedIn job cards found. Waiting 60s to retry...")
    #                     await asyncio.sleep(60)
    #                     await page.reload()
    #                     await page.wait_for_timeout(5000)
    #                     continue
    #
    #                 logger.info(f"Found {len(job_elements)} job listing card(s) on screen.")
    #                 log_activity("career", f"Scanning {len(job_elements)} LinkedIn job listings...")
    #
    #                 for idx, job_card in enumerate(job_elements[:5]):
    #                     try:
    #                         await job_card.click()
    #                         await page.wait_for_timeout(3000)
    #
    #                         title_locator = page.locator('.jobs-unified-top-card__job-title, h2.jobs-details-top-card__job-title')
    #                         title = await title_locator.first.inner_text() if await title_locator.count() > 0 else "Unknown Role"
    #
    #                         company_locator = page.locator('.jobs-unified-top-card__company-name, .jobs-details-top-card__company-name')
    #                         company = await company_locator.first.inner_text() if await company_locator.count() > 0 else "Unknown Company"
    #
    #                         logger.info(f"Selected Job: {title} at {company}")
    #                         log_activity("career", f"Inspecting job listing: '{title} at {company}'")
    #
    #                         easy_apply = page.locator('button.jobs-apply-button[aria-label*="Easy Apply"], button.jobs-apply-button:has-text("Easy Apply")')
    #                         if await easy_apply.count() > 0:
    #                             log_activity("career", f"Found Easy Apply for '{title}' at {company}. Initiating form automation...")
    #                             await easy_apply.click()
    #                             await page.wait_for_timeout(3000)
    #
    #                             for step_num in range(5):
    #                                 submit_btn = page.locator('button[aria-label="Submit application"], button:has-text("Submit application")')
    #                                 if await submit_btn.count() > 0:
    #                                     await submit_btn.click()
    #                                     await page.wait_for_timeout(3000)
    #                                     log_activity("career", f"✅ Successfully applied to '{title}' at {company} via Easy Apply.")
    #
    #                                     dismiss = page.locator('button[aria-label="Dismiss"]')
    #                                     if await dismiss.count() > 0:
    #                                         await dismiss.click()
    #                                         await page.wait_for_timeout(1000)
    #                                     break
    #
    #                                 next_btn = page.locator('button[aria-label="Continue to next step"], button:has-text("Next"), button:has-text("Review")')
    #                                 if await next_btn.count() > 0:
    #                                     await next_btn.click()
    #                                     await page.wait_for_timeout(2000)
    #                                 else:
    #                                     logger.info("Easy Apply flow stuck. Dismissing modal.")
    #                                     dismiss = page.locator('button[aria-label="Dismiss"], button[aria-label="Cancel"]')
    #                                     if await dismiss.count() > 0:
    #                                         await dismiss.click()
    #                                         discard = page.locator('button:has-text("Discard")')
    #                                         if await discard.count() > 0:
    #                                             await discard.click()
    #                                     break
    #                         else:
    #                             apply_btn = page.locator('button.jobs-apply-button')
    #                             if await apply_btn.count() > 0:
    #                                 log_activity("career", f"External Apply found for '{title}' at {company}. Opened listing on screen.")
    #                                 await apply_btn.click()
    #                                 await page.wait_for_timeout(3000)
    #
    #                     except Exception as card_err:
    #                         logger.error(f"Error processing job card {idx}: {card_err}")
    #                         continue
    #
    #                 logger.info("Batch completed. Waiting 5 mins...")
    #                 await asyncio.sleep(300)
    #
    #     except asyncio.CancelledError:
    #         logger.info("Job application background loop cancelled.")
    #     except Exception as e:
    #         logger.error(f"Job application loop encountered error: {e}")
    #         log_activity("career", f"Error in background job application loop: {str(e)[:80]}")

    async def _run_job_application_loop(self, keywords, profile_key):
        import json
        from pathlib import Path
        from urllib.parse import quote
        from playwright.async_api import async_playwright
        from core.browser_automation import get_browser_context
        self.last_job_error = None
        try:
            async with async_playwright() as p:
                browser_context = await get_browser_context(p, 'career_' + profile_key)
                try:
                    page = await browser_context.new_page()
                    await page.goto('https://www.linkedin.com/jobs/search/?keywords=' + quote(keywords), timeout=30000)
                    seen = set()
                    while True:
                        await page.wait_for_timeout(2000)
                        links = page.locator('a[href*="/jobs/view/"]')
                        rows = []
                        for link in (await links.all())[:50]:
                            title = (await link.inner_text()).strip()
                            href = await link.get_attribute('href')
                            if title and href and href not in seen:
                                seen.add(href)
                                rows.append({'title': title, 'url': href.split('?')[0], 'search': keywords,
                                             'status': 'needs_review', 'resume_tailored': False, 'applied': False})
                        if rows:
                            Path('outputs').mkdir(exist_ok=True)
                            with Path('outputs/job-listings.jsonl').open('a', encoding='utf-8') as out:
                                for row in rows:
                                    out.write(json.dumps(row, ensure_ascii=False) + '\n')
                            log_activity('career', f'Saved {len(rows)} job listings for review in outputs/job-listings.jsonl. No applications submitted.')
                        else:
                            self.last_job_error = 'No job listings visible. Sign in or complete verification in the career browser.'
                            log_activity('career', self.last_job_error)
                        await asyncio.sleep(300)
                        await page.reload(timeout=30000)
                finally:
                    await browser_context.close()
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            self.last_job_error = f'Job search stopped ({type(exc).__name__})'
            log_activity('career', self.last_job_error)
