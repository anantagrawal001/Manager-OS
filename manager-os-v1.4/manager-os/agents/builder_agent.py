"""
MANAGER OS — Builder Agent
═══════════════════════════
FILE: agents/builder_agent.py
CREATED: 2026-05-24 | Claude Sonnet 4.6
PURPOSE: Builds software on Anant's behalf.
         - Any language, any platform (web, mobile, desktop, CLI, browser ext.)
         - Complete project structure, core code, DB schema, API layer, deployment
         - n8n workflow automation design
         - Code review, bug fixing, security audit
         - Architecture design for new ideas

DO NOT DELETE ANY CODE — comment out with reason and date
"""

from typing import Dict, Any
from loguru import logger
from agents.base_agent import BaseAgent


class BuilderAgent(BaseAgent):
    """
    Software builder agent.
    Anant describes what he wants. Builder creates it.
    """

    def __init__(self, config, router, firewall):
        super().__init__(config, router, firewall)
        from core.project_work import ProjectWork
        self.project_work = ProjectWork(config, router)

    BUILDER_SYSTEM = """
You are an elite full-stack software architect and developer with 15 years of experience.
You build production-ready, secure, well-documented applications.
You always:
- Choose the right technology for the specific use case
- Generate complete, runnable code (not pseudocode)
- Include error handling, input validation, security considerations
- Provide deployment instructions
- Comment code clearly
- Think about scalability from day one

You can build: web apps (React, Vue, Next.js), mobile apps (React Native, Flutter),
APIs (FastAPI, Express, Django), CLI tools (Python, Go), browser extensions,
n8n workflows, desktop apps (Electron, Tauri), microservices, automation scripts.
"""

    async def execute(self, request: str, context: Dict[str, Any]) -> str:
        req_lower = request.lower()
        import re
        if self.project_work.is_followup(request) or re.search(r'\b(build|create|develop|implement|make|generate)\b', req_lower):
            return await self._build_project(request, context)

        if any(w in req_lower for w in ["n8n", "workflow", "automation", "zapier"]):
            return await self._design_n8n_workflow(request, context)
        elif any(w in req_lower for w in ["architecture", "design", "plan", "structure"]):
            return await self._design_architecture(request, context)
        elif any(w in req_lower for w in ["bug", "fix", "error", "broken", "debug"]):
            return await self._fix_code(request, context)
        elif any(w in req_lower for w in ["review", "audit", "security", "optimize"]):
            return await self._review_code(request, context)
        elif any(w in req_lower for w in ["deploy", "deployment", "hosting", "server"]):
            return await self._deployment_guide(request, context)
        else:
            return await self._build_project(request, context)

    # Superseded 2026-10-12: retained for rollback; corrected implementation below.
    # async def _build_project(self, request: str, context: Dict) -> str:
    #     """Build a complete project"""
    #     prompt = f"""
    # d this project: {request}
    #
    # ide:
    # ECHNOLOGY CHOICE: Which stack and why (justify each choice)
    # ROJECT STRUCTURE: Complete folder/file tree
    # ORE CODE: All critical files with complete working code
    # ATABASE SCHEMA: If applicable
    # PI ENDPOINTS: If applicable, all routes with request/response examples
    # ETUP INSTRUCTIONS: How to run it (step by step, assume non-technical user)
    # EPLOYMENT: How to host it (free options first)
    # HAT'S MISSING: What needs real credentials/accounts to complete
    #
    # s:
    # de must be complete and runnable, not pseudocode
    # clude all imports and dependencies
    # d requirements.txt or package.json
    # mment complex logic clearly
    # ndle errors gracefully
    #     #     return await self.router.complete(
    #         system=self.BUILDER_SYSTEM,
    #         messages=[{"role": "user", "content": prompt}],
    #         task_type="code",
    #         max_tokens=4000
    #     )

    async def _build_project_legacy_bundle(self, request, context):
        from core.artifacts import save_project
        prompt = ('Create a small complete runnable project for this request: ' + request +
                  '\nReturn ONLY JSON: {"files":[{"path":"relative/file.ext","content":"complete file contents"}]}. '
                  'Include README.txt with exact run instructions and requirements if needed. '
                  'Prefer a self-contained HTML file for small browser apps. Maximum 12 files. '
                  'No placeholders, no ellipses, no prose outside the JSON.')
        result = await self.router.complete(system=self.BUILDER_SYSTEM,
                  messages=[{'role':'user','content':prompt}], task_type='code', max_tokens=4000)
        try:
            folder, archive = save_project(result)
        except (ValueError, TypeError, KeyError, AttributeError):
            return 'Sir, the model did not produce a valid file bundle. No project files were created. Try a smaller, specific project request.'
        return (f'Sir, created project files in {folder}. ZIP: {archive}. '
                'Open Outputs to download them. Generated code has not been executed or tested.')

    # 2026-10-12: the legacy bundle generator remains above for source history.
    async def _build_project(self, request, context):
        return await self.project_work.submit(request, context)

    async def _design_n8n_workflow(self, request: str, context: Dict) -> str:
        """Design n8n workflow automation"""
        prompt = f"""
Design an n8n workflow for: {request}

Provide:
1. WORKFLOW NAME and purpose
2. TRIGGER NODE: What starts the workflow (webhook, schedule, manual, app event)
3. NODE CHAIN: Each node in order with:
   - Node type (HTTP Request, Code, Google Sheets, etc.)
   - Configuration settings
   - What it does
   - Output to next node
4. ERROR HANDLING: What happens when a node fails
5. TESTING: How to test each node
6. DEPLOYMENT: How to set this up on the second (always-on) laptop

Also provide: JSON structure for each critical node configuration
"""
        return await self.router.complete(
            system=self.BUILDER_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            task_type="code",
            max_tokens=3000
        )

    async def _design_architecture(self, request: str, context: Dict) -> str:
        """System architecture design"""
        prompt = f"""
Design the architecture for: {request}

Provide:
1. HIGH-LEVEL ARCHITECTURE: Diagram (ASCII art or described clearly)
2. TECHNOLOGY STACK: Each layer with specific technology choices + reasoning
3. DATA FLOW: How data moves through the system
4. DATABASE DESIGN: Tables/collections, relationships, indexes
5. API DESIGN: Key endpoints, authentication approach
6. SCALABILITY CONSIDERATIONS: How to grow from MVP to production
7. COST ESTIMATE: Monthly cost at different scales (free → $100/mo → $1000/mo)
8. BUILD ORDER: What to build first for fastest working MVP

Make architecture decisions the same way a senior engineer at a top startup would.
"""
        return await self.router.complete(
            system=self.BUILDER_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            task_type="reasoning",
            max_tokens=3000
        )

    async def _fix_code(self, request: str, context: Dict) -> str:
        """Debug and fix code"""
        prompt = f"""
Debug and fix this issue: {request}

Provide:
1. ROOT CAUSE: What's actually causing the problem
2. FIX: Complete corrected code (not just the changed lines — full context)
3. EXPLANATION: Why this fix works
4. PREVENTION: How to avoid this bug in the future
5. TESTS: Simple test cases to verify the fix works

Be specific. Show the exact code change.
"""
        return await self.router.complete(
            system=self.BUILDER_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            task_type="code",
            max_tokens=3000
        )

    async def _review_code(self, request: str, context: Dict) -> str:
        """Code review and security audit"""
        prompt = f"""
Review and audit: {request}

Check for:
1. BUGS: Logic errors, edge cases, off-by-one errors
2. SECURITY: SQL injection, XSS, authentication weaknesses, exposed secrets
3. PERFORMANCE: N+1 queries, unnecessary loops, memory leaks
4. CODE QUALITY: Readability, naming, structure, DRY violations
5. BEST PRACTICES: Framework-specific issues

For each finding:
- Severity: CRITICAL | HIGH | MEDIUM | LOW
- Location: Which file/function
- Issue: What's wrong
- Fix: Corrected code

Priority: Fix CRITICAL and HIGH issues first.
"""
        return await self.router.complete(
            system=self.BUILDER_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            task_type="code",
            max_tokens=3000
        )

    async def _deployment_guide(self, request: str, context: Dict) -> str:
        """Deployment instructions"""
        prompt = f"""
Deployment guide for: {request}

Provide step-by-step deployment:
1. FREE HOSTING OPTIONS: Best free tier options for this type of app
2. SETUP STEPS: Exact commands and clicks, assume no prior knowledge
3. ENVIRONMENT VARIABLES: Which secrets to set, where
4. DOMAIN SETUP: How to add a custom domain (free via Cloudflare)
5. SSL: How to enable HTTPS
6. MONITORING: Free monitoring setup (uptime, errors)
7. UPDATES: How to push updates going forward

Prioritize options that stay free forever for small traffic.
"""
        return await self.router.complete(
            system=self.BUILDER_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            task_type="code",
            max_tokens=2000
        )

    async def get_status(self) -> Dict:
        return {"healthy": True, "state": "running", "agent": "BuilderAgent"}
