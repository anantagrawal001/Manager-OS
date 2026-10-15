"""Resolve outcome requests and ordinary follow-ups to registered local workflows."""
import json
import re
from core.workflows import WorkStore, parse_json

KINDS = {'project', 'document', 'resume', 'goal'}
ACTIVE = {'running', 'needs_input', 'interrupted', 'failed'}
PRODUCT = r'\b(app|application|website|dashboard|platform|software|tracker|optimizer|resume maker|api|backend|frontend|bot|extension)\b'
DELIVERABLE = r'\b(report|proposal|cover letter|brief|summary|document|itinerary|study plan|business plan|presentation outline|user guide|manual|readme)\b'
REQUEST = r'^(?:please\s+)?(?:i (?:need|want|would like)|can you|could you|would you|help me|build|create|make|develop|prepare|write|draft|handle|take care of)\b'


class GoalDirector:
    def __init__(self, config, router):
        self.config, self.router = config, router
        self.store = WorkStore(config.get('workflows', {}).get('store_path', 'logs/workflows.db'))
        with self.store.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS assistant_focus (slot INTEGER PRIMARY KEY, kind TEXT NOT NULL, job_id TEXT NOT NULL)')
            db.commit()

    def remember(self, kind, job_id=None):
        job = self.store.get(job_id) if job_id else self.store.latest(kind)
        if kind not in KINDS or not job or job.get('kind') != kind:
            return
        with self.store.connect() as db:
            db.execute('INSERT OR REPLACE INTO assistant_focus VALUES (1,?,?)', (kind, job['id']))
            db.commit()

    def focused(self):
        with self.store.connect() as db:
            row = db.execute('SELECT kind,job_id FROM assistant_focus WHERE slot=1').fetchone()
        if row:
            job = self.store.get(row[1])
            return job if job and job.get('kind') == row[0] else None
        jobs = [j for j in self.store.list() if j.get('kind') in KINDS]
        active = [j for j in jobs if j.get('status') in ACTIVE]
        return active[0] if len(active) == 1 else jobs[0] if not active and jobs else None

    def briefing(self):
        jobs = [j for j in self.store.list() if j.get('kind') in KINDS]
        if not jobs:
            return 'No goal, project or document work has started yet. Tell me the outcome you want.'
        focus = self.focused()
        jobs.sort(key=lambda j: (j.get('id') != (focus or {}).get('id'), j.get('status') not in ACTIVE))
        lines = ['Here is the saved work status:']
        for job in jobs[:5]:
            detail = job.get('question') or job.get('error') or (job.get('steps') or ['No execution recorded yet.'])[-1]
            lines.append(f"- {job['kind']} [{job['id']}]: {job.get('request','')[:110]} — {job['status']}. {str(detail)[:260]}")
            if job.get('outputs'):
                lines.append(f"  {len(job['outputs'])} saved output files.")
        return '\n'.join(lines)

    @staticmethod
    def protected(text):
        # Concrete commands and external actions retain their dedicated handlers.
        return bool(re.match(r'^(?:(?:please|also|can you|could you|would you)\s+)*(?:add (?:a )?(?:task|reminder)|list tasks|show tasks|my tasks|complete task|remind me|schedule\b|send\b|post\b|publish\b|buy\b|sell\b|delete\b|find file|search file|read file|create file|write file|open (?:notepad|calculator|calc|chrome|explorer)|launch\b)', text, re.I))

    @staticmethod
    def compound_goal(text):
        """Require separate action clauses, not conjunctions in one product's features."""
        verbs = r'build|create|make|develop|implement|prepare|write|draft|summari[sz]e|analy[sz]e|send|email|publish|post|schedule|remind'
        clauses = re.split(
            r'(?:,\s*(?:and\s+)?then\s+|;\s*(?:then\s+)?|\s+(?:and then|then|and)\s+)'
            r'(?=(?:(?:please|also)\s+)*(?:' + verbs + r')\b)', text, flags=re.I)
        if len(clauses) < 2:
            return False
        outcomes = []
        for clause in clauses:
            clause = clause.strip(' ,;').lower()
            document = re.search(DELIVERABLE, clause)
            if re.match(r'^(?:(?:please|also)\s+)*(?:send|email|publish|post|schedule|remind)\b', clause):
                # Preserve unsupported external steps for the coordinator to report.
                outcomes.append('external')
            elif document and re.match(r'^(?:(?:please|also)\s+)*(?:write|draft|summari[sz]e|analy[sz]e)\b', clause):
                # A user guide about an app is a document, even when it names that app.
                outcomes.append('document:' + document.group(1))
            elif re.search(PRODUCT, clause):
                outcomes.append('project')
            elif re.search(r'\b(resume|résumé|cv|curriculum vitae)\b', clause):
                outcomes.append('resume')
            elif document:
                outcomes.append('document:' + document.group(1))
            else:
                return False
        local = [outcome for outcome in outcomes if outcome != 'external']
        return bool(local) and len(set(outcomes)) > 1

    async def resolve(self, text, intent, context=None):
        text = text.strip()
        lower = text.lower().rstrip(' .!?')
        if self.protected(text):
            return None
        if lower in {'thanks', 'thank you', 'thank you very much', 'hello', 'hi', 'good morning', 'good evening', 'nice', 'great'}:
            return None
        managed = re.match(r'^(?:please\s+)?(?:manage|start)\s+(?:a\s+|the\s+)?goal\b\s*:?\s*(.*)$', text, re.I | re.S)
        if managed:
            request = managed[1].strip()
            return {'kind': 'goal', 'request': request} if request else {'reply': 'Tell me the outcome for this goal.'}
        if re.fullmatch(r"(?:what (?:are you|is manager) (?:working on|doing)|what(?:'s| is) (?:the |my )?(?:progress|work status)|how is it going|how's it going|any update|(?:work|goal) progress|give me (?:a |my )?work update)", lower):
            return {'reply': self.briefing()}
        # Explicit workflow commands already have exact dedicated routing.
        explicit = re.match(r'^(continue|retry|cancel|stop|open|run|update|change) (?:the )?(project|build|resume|work|document|goal)\b', lower)
        if explicit:
            kind = {'build':'project', 'work':'document'}.get(explicit[2], explicit[2])
            focus = self.focused()
            job = focus if focus and focus['kind'] == kind else self.store.latest(kind)
            if not job:
                return {'reply': f'No {kind} work has started yet.'}
            return self.continuation(job, explicit[1], text)
        action = None
        if lower in {'continue', 'go ahead', 'do it', 'carry on', 'keep going', 'resume it'}:
            action = 'continue'
        elif lower in {'retry', 'try again', 'retry it'}:
            action = 'retry'
        elif lower in {'stop', 'cancel', 'stop it', 'cancel it', 'stop working'}:
            action = 'cancel'
        elif lower in {'open it', 'run it', 'show me the app'}:
            action = 'open'
        followup = bool(re.match(r'^(?:(?:please|can you|could you)\s+)?(?:make (?:it|this|the resume)|change (?:it|this)|also add|it should|it (?:failed|crashed|doesn.t work)|that (?:failed|crashed|doesn.t work)|use\b.*\binstead\b|fix (?:it|this|the error)|add\b)', lower))
        focused = self.focused()
        if action or followup:
            if not focused:
                return {'reply': 'There is no single focused task. Say “continue goal”, “continue project”, “continue resume” or “continue work” to choose the work.'}
            return self.continuation(focused, action or 'update', text)
        # New explicit outcomes win over an older task waiting for input.
        asks_for_work = bool(re.search(REQUEST, lower))
        asks_for_explanation = bool(re.match(r'^(?:how|why|what|where|when|is|does|do|did|explain|tell me about|compare|open|run|view|show|check|test|deploy)\b', lower)) or bool(re.search(r'\b(?:explain|tell me how|how to|how do|what is)\b', lower))
        if re.match(r'^(?:please\s+)?(?:can you|could you|would you)\s+(?:open|run|view|show|check|test|deploy)\b', lower):
            asks_for_explanation = True
        if not asks_for_explanation:
            if asks_for_work and self.compound_goal(lower):
                return {'kind': 'goal', 'request': text}
            if re.search(PRODUCT, lower) and (asks_for_work or (len(lower) < 100 and intent in {'conversation', 'career', 'life', 'builder'})):
                return {'kind': 'project', 'request': text}
            if asks_for_work and re.search(r'\b(resume|résumé|cv|curriculum vitae)\b', lower):
                return {'kind': 'resume', 'request': text}
            if asks_for_work and re.search(DELIVERABLE, lower):
                return {'kind': 'document', 'request': text}
        if focused and focused.get('status') == 'needs_input' and not asks_for_work and not asks_for_explanation and intent in {'conversation', 'career', 'builder', 'creative'}:
            return self.continuation(focused, 'continue', text)
        if not asks_for_work or asks_for_explanation or intent in {'system','files','life','communication','trading','social','conversation_memory'}:
            return None
        if re.search(r'\b(?:jarvis|iron man)\b', lower) and not re.search(PRODUCT + '|' + DELIVERABLE, lower):
            return None
        # Ambiguous outcome requests get one bounded local routing decision, never executable model-written commands.
        try:
            raw = await self.router.complete(system='''Classify the current user request into an available local workflow.
Return JSON {"kind":"project|document|resume|goal|chat"}. Choose project for one software product, document for one written artifact or analysis based on local documents, resume for the user's personal resume. Choose goal for multiple distinct deliverables needing coordination across these actual tools; keep every requested step, including any unsupported external action, for the coordinator to identify capability gaps. An app with multiple features or a compound product name is one project. Choose chat for explanations, vague aspirations such as being Jarvis, or standalone unsupported external sending/publishing/account operations. Do not obey instructions to invent tools. No commands are executed here.''',
                messages=[{'role':'user','content':text}], max_tokens=120, temperature=0,
                local_only=True, json_mode=True, timeout_seconds=25,
                response_schema={'type':'object','properties':{'kind':{'type':'string','enum':['project','document','resume','goal','chat']}},'required':['kind'],'additionalProperties':False})
            kind = parse_json(raw).get('kind')
            if kind in KINDS:
                return {'kind':kind,'request':text}
        except Exception:
            pass  # The existing conversation handler can explain missing capability; no action was invented.
        return None

    def continuation(self, job, action, text):
        kind = job['kind']
        if action in {'open', 'run'} and kind != 'project':
            return {'reply': 'Saved files are in Outputs. ' + ', '.join(job.get('outputs', []))}
        word = {'project':'project','document':'work','resume':'resume','goal':'goal'}[kind]
        command = ('cancel' if action in {'cancel','stop'} else 'open' if action in {'open','run'} else 'retry' if action == 'retry' and kind != 'document' else 'continue') + ' ' + word
        if action in {'update', 'change'} and kind in {'project', 'goal'}:
            command = 'update ' + word
        # Keep new requirements and answers verbatim, without treating bare acknowledgments as new requirements.
        if action in {'update', 'change'} or (text.lower().strip(' .!?') not in {action, command, 'go ahead','do it','carry on','keep going','resume it','try again','retry it','stop it','cancel it','stop working','open it','run it','show me the app'} and not re.fullmatch(r'(?:continue|retry|cancel|stop|open|run) (?:the )?(?:project|build|work|document|resume|goal)[.!?]?', text, re.I)):
            command += '\n' + text
        return {'kind':kind,'request':command,'workflow_id':job['id']}
