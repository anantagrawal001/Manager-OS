"""Goal selection uses conversational focus, without touching real user data."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock

from core.goal_director import GoalDirector
from core.workflows import WorkStore


class GoalDirectorTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        root = Path(self.directory.name)
        self.config = {
            'manager': {'owner': 'Alex Example'},
            'workflows': {'store_path': str(root / 'work.db'),
                          'workspace_root': str(root / 'workspaces'),
                          'output_root': str(root / 'outputs')},
        }
        self.store = WorkStore(self.config['workflows']['store_path'])
        self.router = type('Router', (), {'complete': AsyncMock(return_value='{}')})()
        self.director = GoalDirector(self.config, self.router)

    def job(self, job_id, kind='project', status='complete', request=None, question=None):
        job = {'id': job_id, 'kind': kind, 'status': status,
               'request': request or {'project': 'Build a report viewer',
                                      'resume': 'Create my resume',
                                      'document': 'Write a project report'}[kind],
               'steps': ['Saved checkpoint'], 'outputs': [], 'messages': [],
               'checks': [], 'read_sources': [], 'followups': [],
               'plan': {'title': 'Report viewer', 'app_type': 'web',
                        'acceptance': [{'id': 'A1', 'description': 'Read a PDF'}]}}
        if question:
            job['question'] = question
        self.store.save(job)
        return job

    def assert_work(self, decision, kind, job_id=None):
        self.assertIsInstance(decision, dict)
        self.assertEqual(decision.get('kind'), kind, decision)
        self.assertIsInstance(decision.get('request'), str)
        self.assertTrue(decision['request'].strip())
        if job_id is None:
            self.assertFalse(decision.get('workflow_id'), decision)
        else:
            self.assertEqual(decision.get('workflow_id'), job_id, decision)

    async def test_background_checkpoint_does_not_steal_selected_project(self):
        project = self.job('focused-project')
        self.director.remember('project', project['id'])
        unrelated = self.job('unrelated-document', 'document', 'running')
        unrelated['steps'].append('Background source collection finished')
        self.store.save(unrelated)

        decision = await self.director.resolve('Make it faster', 'conversation')

        self.assert_work(decision, 'project', project['id'])

    async def test_bare_continue_uses_focus_instead_of_old_resume(self):
        self.job('old-resume', 'resume', 'interrupted')
        project = self.job('focused-project', status='interrupted')
        self.director.remember('project', project['id'])

        decision = await self.director.resolve('continue', 'conversation')

        self.assert_work(decision, 'project', project['id'])

    async def test_focus_survives_restart_and_newer_background_work(self):
        project = self.job('focused-project')
        self.director.remember('project', project['id'])
        self.job('newer-resume', 'resume', 'draft_ready')
        restarted = GoalDirector(self.config, self.router)

        decision = await restarted.resolve('It failed when I uploaded a PDF', 'conversation')

        self.assert_work(decision, 'project', project['id'])
        self.assertIn('uploaded a PDF', decision['request'])
        self.assertEqual(self.store.latest()['id'], 'newer-resume',
                         'Director metadata must not masquerade as a workflow checkpoint')

    async def test_remember_without_id_selects_latest_of_requested_kind(self):
        self.job('older-project')
        newest = self.job('newest-project')
        self.job('newer-document', 'document', 'draft_ready')
        self.director.remember('project')

        decision = await self.director.resolve('continue', 'conversation')

        self.assert_work(decision, 'project', newest['id'])

    async def test_direct_commands_are_not_intercepted_by_project_focus(self):
        project = self.job('focused-project')
        self.director.remember('project', project['id'])
        for request, intent in [
            ('Also remind me in 10 minutes to drink water', 'life'),
            ('add task review the quarterly report', 'life'),
            ('open notepad', 'files'),
            ('read file notes.txt', 'files'),
            ('send message to Alex: The report is ready', 'communication'),
            ('which model are you using?', 'system'),
        ]:
            with self.subTest(request=request):
                self.assertIsNone(await self.director.resolve(request, intent))

    async def test_natural_software_goal_starts_a_new_project(self):
        decision = await self.director.resolve(
            'I need a website to track expenses', 'builder')

        self.assert_work(decision, 'project')
        self.assertIn('track expenses', decision['request'])

    async def test_natural_report_goal_starts_document_work(self):
        decision = await self.director.resolve(
            'I need a report summarizing my project notes', 'conversation')

        self.assert_work(decision, 'document')

    async def test_failure_report_continues_focused_project(self):
        project = self.job('focused-project')
        self.director.remember('project', project['id'])

        decision = await self.director.resolve(
            'It failed when I uploaded a PDF', 'conversation')

        self.assert_work(decision, 'project', project['id'])
        self.assertIn('uploaded a PDF', decision['request'])

    async def test_explanation_question_does_not_mutate_focused_project(self):
        project = self.job('focused-project')
        self.director.remember('project', project['id'])

        decision = await self.director.resolve('How does Python work?', 'conversation')

        self.assertIsNone(decision)
        self.assertEqual(self.store.get(project['id'])['request'], project['request'])

    async def test_essential_answer_targets_focused_work_waiting_for_input(self):
        report = self.job('waiting-document', 'document', 'needs_input',
                          question='Which quarter should the report cover?')
        self.director.remember('document', report['id'])
        self.job('background-project', status='running')

        decision = await self.director.resolve('The second quarter of 2026', 'conversation')

        self.assert_work(decision, 'document', report['id'])
        self.assertIn('second quarter of 2026', decision['request'])

    async def test_pending_question_cannot_swallow_a_send_command(self):
        report = self.job('waiting-document', 'document', 'needs_input',
                          question='Who is the report intended for?')
        self.director.remember('document', report['id'])

        decision = await self.director.resolve(
            'Send message to Alex: I will be late', 'communication')

        self.assertIsNone(decision)
        self.assertEqual(self.store.get(report['id'])['status'], 'needs_input')


if __name__ == '__main__':
    unittest.main()
