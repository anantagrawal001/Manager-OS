import asyncio
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

from core.personal_context import discover, user_history
from core.workflows import ResumeWorkflow, WorkStore, validate_resume, save_resume, preserve_employment, quote_supported
from core.routing import classify
from core.manager import Manager
from core.assistant_work import AssistantWork

SOURCE = 'Alex Example\nalex@example.com\nDatabase developer at Example Co, 2023.\nBuilt SQL reporting pipelines.\nBTech Computer Science 2022.'


def field(text):
    return {'text': text, 'evidence': [{'source': 'document', 'quote': text}]}


def draft():
    return {'name': field('Alex Example'), 'contact': field('alex@example.com'),
            'summary': field('Database developer at Example Co, 2023.'),
            'sections': [{'heading': 'Experience', 'items': [field('Built SQL reporting pipelines.')]},
                         {'heading': 'Education', 'items': [field('BTech Computer Science 2022.')]}]}


class EvidenceTests(unittest.TestCase):
    def test_discovery_excludes_other_people_and_private_directories(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'Alex_resume.txt').write_text(SOURCE)
            (root/'other_resume.txt').write_text(SOURCE.replace('Alex', 'Sam').replace('alex', 'sam'))
            (root/'security').mkdir()
            (root/'security'/'resume.txt').write_text(SOURCE)
            result = discover({'manager': {'owner': 'Alex'}, 'personal_context': {'roots': [directory]}})
            self.assertEqual(len(result['documents']), 1)
            self.assertEqual(result['other_people_or_unmatched'], ['other_resume.txt'])

    def test_validator_rejects_fabricated_quotes_and_metrics(self):
        data = draft()
        validate_resume(data, {'document': SOURCE})
        data['sections'][0]['items'][0]['text'] = 'Improved revenue 95%.'
        with self.assertRaises(ValueError):
            validate_resume(data, {'document': SOURCE})
        data = draft()
        data['name']['evidence'][0]['quote'] = 'Made-up identity'
        with self.assertRaises(ValueError):
            validate_resume(data, {'document': SOURCE})

    def test_assistant_messages_do_not_become_personal_facts(self):
        with tempfile.TemporaryDirectory() as directory:
            result = user_history({'conversation': {'store_path': str(Path(directory)/'none.db')}},
                [{'role': 'assistant', 'content': 'I worked at Fictional Corp'},
                 {'role': 'user', 'content': 'I worked at Example Co'}])
            self.assertEqual(result, ['I worked at Example Co'])

    def test_resume_routing_does_not_override_reminders(self):
        self.assertEqual(classify('create my resume for a SQL role', Manager.INTENT_MAP), 'career')
        self.assertEqual(classify('remind me to create my resume', Manager.INTENT_MAP), 'life')

    def test_employment_headers_and_previous_roles_survive_model_omissions(self):
        source = SOURCE + '\nExample Co\nDatabase Developer\n03/2023 - Present\n• Built SQL reporting pipelines.\nEarlier Co\nData Intern\n06/2022 - 02/2023\n• Checked report totals.\nEducation'
        data = preserve_employment(draft(), source)
        self.assertEqual(len(data['employment']), 2)
        self.assertIn('Earlier Co', data['employment'][1]['header']['text'])
        self.assertIn('Checked report totals', data['employment'][1]['items'][0]['text'])
        validate_resume(data, {'document': source})

    def test_pdf_list_quotes_require_every_fragment_to_exist(self):
        self.assertTrue(quote_supported('SQL\nPython', '• SQL\n• Git\n• Python'))
        self.assertFalse(quote_supported('SQL\nInvented Skill', '• SQL\n• Git\n• Python'))


class WorkflowTests(unittest.IsolatedAsyncioTestCase):
    def config(self, directory):
        return {'manager': {'owner': 'Alex'}, 'personal_context': {'roots': [directory]},
                'conversation': {'store_path': str(Path(directory)/'chat.db')},
                'workflows': {'store_path': str(Path(directory)/'work.db'), 'output_root': str(Path(directory)/'outputs')}}

    async def test_real_files_saved_only_after_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory)/'resume.txt').write_text(SOURCE)
            router = type('Router', (), {'complete': AsyncMock(return_value=json.dumps(draft()))})()
            worker = ResumeWorkflow(self.config(directory), router)
            with patch('core.workflows.render_pdf'):
                await worker.run('Create my resume', {})
            job = worker.store.latest()
            self.assertEqual(job['status'], 'draft_ready')
            self.assertTrue(list((Path(directory)/'outputs').rglob('resume.html')))
            self.assertTrue(router.complete.call_args.kwargs['local_only'])

    async def test_missing_information_survives_restart_and_continues(self):
        with tempfile.TemporaryDirectory() as directory:
            router = type('Router', (), {'complete': AsyncMock(return_value=json.dumps(draft()))})()
            worker = ResumeWorkflow(self.config(directory), router)
            result = await worker.run('Create my resume', {})
            self.assertIn('full name', result)
            router.complete.assert_not_called()
            original_id = worker.store.latest()['id']
            reloaded = ResumeWorkflow(self.config(directory), router)
            self.assertTrue(reloaded.accepts_followup('My name is Alex Example', 'conversation'))
            self.assertFalse(reloaded.accepts_followup('what is the weather', 'conversation'))
            (Path(directory)/'resume.txt').write_text(SOURCE)
            with patch('core.workflows.render_pdf'):
                await reloaded.run('continue resume', {})
            self.assertEqual(reloaded.store.latest()['id'], original_id)
            self.assertEqual(reloaded.store.latest()['status'], 'draft_ready')

    async def test_invalid_model_response_retries_then_reports_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory)/'resume.txt').write_text(SOURCE)
            router = type('Router', (), {'complete': AsyncMock(return_value='I created your resume!')})()
            worker = ResumeWorkflow(self.config(directory), router)
            await worker.run('Create my resume', {})
            self.assertEqual(worker.store.latest()['status'], 'failed')
            self.assertEqual(worker.store.latest()['outputs'], [])
            self.assertEqual(router.complete.await_count, 2)

    async def test_background_work_is_nonblocking_and_does_not_duplicate(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory)/'resume.txt').write_text(SOURCE)
            ready = asyncio.Event()
            async def model(**kwargs):
                await ready.wait()
                return json.dumps(draft())
            router = type('Router', (), {'complete': AsyncMock(side_effect=model)})()
            worker = ResumeWorkflow(self.config(directory), router)
            worker.notify = AsyncMock()
            with patch('core.workflows.render_pdf'):
                await asyncio.wait_for(worker.submit('create my resume', {}), 1)
                self.assertFalse(worker.task.done())
                self.assertIn('already running', await worker.submit('create my resume', {}))
                ready.set()
                await worker.task
            self.assertEqual(router.complete.await_count, 1)
            worker.notify.assert_awaited_once()

    async def test_restart_marks_running_work_interrupted(self):
        with tempfile.TemporaryDirectory() as directory:
            worker = ResumeWorkflow(self.config(directory), None)
            worker.store.save({'id': 'test', 'kind': 'resume', 'status': 'running', 'steps': ['Gathering evidence']})
            restarted = ResumeWorkflow(self.config(directory), None)
            self.assertEqual(restarted.store.latest()['status'], 'interrupted')

    async def test_document_agent_reads_then_saves_real_files(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'profile.txt'
            path.write_text(SOURCE)
            actions = [
                {'tool': 'find_documents', 'args': {'query': 'profile'}},
                {'tool': 'read_document', 'args': {'path': str(path)}},
                {'tool': 'save_document', 'args': {'text': 'Alex Example builds SQL reporting pipelines at Example Co.', 'based_on_local_files': True}},
                {'tool': 'finish', 'args': {'summary': 'Created a document'}}]
            router = type('Router', (), {'complete': AsyncMock(side_effect=[json.dumps(a) for a in actions])})()
            worker = AssistantWork(self.config(directory), router)
            await worker.submit('Summarize my profile', {})
            await worker.task
            job = worker.store.latest('document')
            self.assertEqual(job['status'], 'draft_ready')
            self.assertEqual(len(job['outputs']), 2)
            self.assertEqual(job['read_sources'], [str(path.resolve())])
            self.assertTrue((Path(directory)/'outputs'/job['outputs'][0]).exists())

    async def test_document_agent_cannot_report_completion_without_a_file(self):
        with tempfile.TemporaryDirectory() as directory:
            router = type('Router', (), {'complete': AsyncMock(return_value=json.dumps({'tool': 'finish', 'args': {'summary': 'Done'}}))})()
            worker = AssistantWork(self.config(directory), router)
            await worker.submit('Prepare my work plan', {})
            await worker.task
            self.assertEqual(worker.store.latest('document')['status'], 'failed')
            self.assertEqual(worker.store.latest('document')['outputs'], [])

    async def test_document_tools_cannot_escape_approved_folders_or_run_commands(self):
        with tempfile.TemporaryDirectory() as directory:
            worker = AssistantWork(self.config(directory), None)
            job = {'read_sources': [], 'outputs': []}
            with self.assertRaises(ValueError):
                worker.tool({'tool': 'read_document', 'args': {'path': str(Path(directory).parent/'private.txt')}}, job)
            secret = Path(directory)/'security'/'resume.txt'
            secret.parent.mkdir(); secret.write_text('secret')
            with self.assertRaises(ValueError):
                worker.tool({'tool': 'read_document', 'args': {'path': str(secret)}}, job)
            with self.assertRaises(ValueError):
                worker.tool({'tool': 'shell', 'args': {'command': 'anything'}}, job)

    async def test_resume_and_document_work_keep_independent_followups(self):
        with tempfile.TemporaryDirectory() as directory:
            resume = ResumeWorkflow(self.config(directory), None)
            resume.store.save({'id': 'resume-job', 'kind': 'resume', 'status': 'needs_input', 'steps': []})
            resume.store.save({'id': 'document-job', 'kind': 'document', 'status': 'needs_input', 'steps': []})
            self.assertTrue(resume.accepts_followup('My name is Alex', 'conversation'))
            self.assertEqual(resume.store.latest('resume')['id'], 'resume-job')


if __name__ == '__main__':
    unittest.main()
