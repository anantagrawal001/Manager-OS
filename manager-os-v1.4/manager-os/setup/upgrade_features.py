from pathlib import Path
from setup.source_edit import replace_definition as replace

replace('agents/builder_agent.py', 'BuilderAgent._build_project', '''    async def _build_project(self, request, context):
        from core.artifacts import save_project
        prompt = ('Create a small complete runnable project for this request: ' + request +
                  '\\nReturn ONLY JSON: {"files":[{"path":"relative/file.ext","content":"complete file contents"}]}. '
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
''')

replace('agents/research_agent.py', 'ResearchAgent.execute', '''    async def execute(self, request, context):
        result = await self._ask_ai(request, system=self.RESEARCH_SYSTEM +
                   '\\nNo live web search tool is connected. Offer a knowledge-based overview. '
                   'Do not claim you searched, verified, cross-referenced sources, or retrieved current data.', task_type='search')
        return 'Knowledge-based research draft — live sources have not been retrieved or verified.\\n\\n' + result
''')

replace('agents/trading_agent.py', 'TradingAgent.execute', '''    async def execute(self, request, context):
        import re
        if re.search(r'\\b(buy|sell|execute|place|order)\\b', request, re.I):
            return 'Sir, no live broker is connected and no order was placed. This installation supports informational analysis only.'
        if re.search(r'\\b(portfolio|holdings|positions|pnl|profit|loss)\\b', request, re.I):
            return 'Sir, no broker holdings or transaction history are connected. Provide your holdings for an analysis; I will not invent a portfolio.'
        result = await self._ask_ai(request, system=self.SYSTEM_PROMPT +
                    '\\nNo current market quotes or broker data have been supplied. '
                    'Do not invent prices, signals, confidence percentages, holdings, or market direction. '
                    'Explain concepts or analyze only the figures supplied by the user.', task_type='trading')
        return 'Informational analysis — no live market feed or broker account is connected.\\n\\n' + result
''')

# Collect real job listings instead of claiming resume tailoring and blindly submitting forms.
replace('agents/career_agent.py', 'CareerAgent._run_job_application_loop', '''    async def _run_job_application_loop(self, keywords, profile_key):
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
                                    out.write(json.dumps(row, ensure_ascii=False) + '\\n')
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
''')
p=Path('agents/career_agent.py')
s=p.read_text(encoding='utf-8').replace('Sir, I have started the background LinkedIn job application loop for:', 'Sir, I started background LinkedIn job search for:')
s=s.replace("on Chrome profile '{profile_key}'.\"", "on Chrome profile '{profile_key}'. Listings are saved for review; applications are not submitted automatically.\"")
p.write_text(s,encoding='utf-8')

# Update only after successful save: new keys should actually become the selected key.
p=Path('core/key_manager.py')
s=p.read_text(encoding='utf-8').replace('        self._save_vault()\n        logger.info(f"Key added', '        self.current_index[provider] = len(self.pools[provider]) - 1\n        self._save_vault()\n        logger.info(f"Key added',1)
p.write_text(s,encoding='utf-8')

replace('setup/first_run.py', 'main', '''async def main():
    # Preserve existing credentials and use the reliable core installer.
    import subprocess, sys
    from pathlib import Path
    result = subprocess.run([sys.executable, str(Path(__file__).with_name('bootstrap.py'))])
    if result.returncode:
        raise SystemExit(result.returncode)
''')

# Enrollment must never reset an existing passphrase or silently create a default.
replace('core/identity.py', 'IdentityGuard.enroll', '''    async def enroll(self):
        from security.auth import load_passphrase_hash, enroll_passphrase
        if load_passphrase_hash():
            self.enrolled = True
            return True
        if os.environ.get('SETUP_UNATTENDED') == '1':
            logger.info('Create a passphrase in the dashboard on first use')
            return False
        import getpass
        try:
            passphrase = await asyncio.to_thread(getpass.getpass, 'Create passphrase (8+ characters): ')
            enroll_passphrase(passphrase)
        except (ValueError, EOFError, KeyboardInterrupt):
            return False
        self.enrolled = True
        return True
''')
replace('core/identity.py', 'IdentityGuard._background_enroll', '''    async def _background_enroll(self):
        logger.info('Identity enrollment is available in the dashboard. No default passphrase is created.')
''')
replace('core/identity.py', 'IdentityGuard.verify_passphrase', '''    def verify_passphrase(self, passphrase):
        from security.auth import verify_passphrase
        return verify_passphrase(passphrase)
''')
print('Artifact generation and truthful domain results installed')
