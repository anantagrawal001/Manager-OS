"""Managed goals coordinate separate deliverables without absorbing single actions."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock

from core.goal_director import GoalDirector
from core.workflows import WorkStore


class CompoundGoalTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.config = {'workflows': {'store_path': str(Path(self.directory.name) / 'work.db')}}
        self.store = WorkStore(self.config['workflows']['store_path'])
        self.router = type('Router', (), {'complete': AsyncMock(return_value='{"kind":"chat"}')})()
        self.director = GoalDirector(self.config, self.router)

    def focus_goal(self, status='running'):
        job = {'id': 'managed-goal', 'kind': 'goal', 'request': 'Prepare application materials',
               'status': status, 'steps': ['Resume child workflow started'], 'outputs': []}
        self.store.save(job)
        self.director.remember('goal', job['id'])
        return job

    async def test_explicit_managed_goal_preserves_complete_outcome(self):
        for text, expected in [
            ('manage goal: Create my resume and draft a cover letter', 'Create my resume and draft a cover letter'),
            ('start goal Prepare my application materials', 'Prepare my application materials'),
            ('Please start a goal: Build a small tracker', 'Build a small tracker'),
        ]:
            with self.subTest(text=text):
                self.assertEqual(await self.director.resolve(text, 'conversation'),
                                 {'kind': 'goal', 'request': expected})
        self.router.complete.assert_not_awaited()

    async def test_empty_managed_goal_does_not_start_a_workflow(self):
        for text in ['manage goal:', 'start goal']:
            with self.subTest(text=text):
                result = await self.director.resolve(text, 'conversation')
                self.assertIn('reply', result)
                self.assertNotIn('kind', result)

    async def test_separate_deliverables_route_to_coordinator(self):
        for text, intent in [
            ('Create my resume and draft a cover letter', 'career'),
            ('Build an expense tracker, then write its user guide', 'builder'),
            ('Build an expense tracker, then write a user guide for the tracker', 'builder'),
            ('Write a project report and draft a separate proposal', 'conversation'),
            ('I need a website; then write its user guide', 'builder'),
        ]:
            with self.subTest(text=text):
                self.assertEqual(await self.director.resolve(text, intent),
                                 {'kind': 'goal', 'request': text})

    async def test_compound_goal_preserves_external_steps_for_gap_reporting(self):
        for text, intent in [
            ('Create my resume and send it to Alex', 'career'),
            ('Build an expense tracker, then publish it online', 'builder'),
            ('Draft a cover letter and email it to the recruiter', 'communication'),
        ]:
            with self.subTest(text=text):
                result = await self.director.resolve(text, intent)
                self.assertEqual(result, {'kind': 'goal', 'request': text})
        self.router.complete.assert_not_awaited()

    async def test_compound_product_name_is_one_project(self):
        for text in ['LinkedIn optimizer and resume maker',
                     'Create a LinkedIn optimizer and resume maker']:
            with self.subTest(text=text):
                self.assertEqual(await self.director.resolve(text, 'career'),
                                 {'kind': 'project', 'request': text})

    async def test_feature_conjunctions_do_not_spawn_managed_goals(self):
        for text in ['Build an expense tracker with search and charts',
                     'Build an app and create a dashboard with filters',
                     'Create a resume maker that can import PDF and export DOCX']:
            with self.subTest(text=text):
                result = await self.director.resolve(text, 'builder')
                self.assertEqual(result.get('kind'), 'project')

    async def test_explicit_goal_commands_select_exact_focused_job(self):
        job = self.focus_goal()
        for text, command in [('continue goal', 'continue goal'), ('retry goal', 'retry goal'),
                              ('cancel goal', 'cancel goal'), ('stop goal', 'cancel goal')]:
            with self.subTest(text=text):
                self.assertEqual(await self.director.resolve(text, 'conversation'),
                                 {'kind': 'goal', 'request': command, 'workflow_id': job['id']})

    async def test_goal_focus_survives_child_work_updates_and_restart(self):
        job = self.focus_goal()
        self.store.save({'id': 'newer-child', 'kind': 'resume', 'status': 'running',
                         'request': 'Create my resume', 'steps': [], 'outputs': []})
        restarted = GoalDirector(self.config, self.router)

        result = await restarted.resolve('Also add an interview briefing', 'conversation')

        self.assertEqual(result['kind'], 'goal')
        self.assertEqual(result['workflow_id'], job['id'])
        self.assertEqual(result['request'], 'update goal\nAlso add an interview briefing')
        self.assertEqual((await restarted.resolve('continue', 'conversation'))['workflow_id'], job['id'])

    async def test_goal_progress_reports_saved_status_without_execution(self):
        job = self.focus_goal()

        result = await self.director.resolve('goal progress', 'conversation')

        self.assertIn(job['id'], result['reply'])
        self.assertIn('running', result['reply'])
        self.assertNotIn('kind', result)
        self.router.complete.assert_not_awaited()

    async def test_selected_goal_does_not_intercept_direct_actions_or_explanations(self):
        self.focus_goal('needs_input')
        for text, intent in [('Can you send my resume to Alex?', 'communication'),
                             ('Also remind me in 10 minutes to drink water', 'life'),
                             ('How do I build a website and write its user guide?', 'builder'),
                             ('How does Python work?', 'conversation')]:
            with self.subTest(text=text):
                self.assertIsNone(await self.director.resolve(text, intent))

    async def test_jarvis_aspiration_does_not_start_execution(self):
        result = await self.director.resolve(
            'I want this to work exactly like Jarvis from Iron Man, equally intelligent and capable',
            'conversation')

        self.assertIsNone(result)
        self.router.complete.assert_not_awaited()

    async def test_bounded_classifier_can_select_goal_for_other_compound_requests(self):
        self.router.complete.return_value = '{"kind":"goal"}'
        text = 'Help me turn the notes into a career package and a practice session'

        self.assertEqual(await self.director.resolve(text, 'conversation'),
                         {'kind': 'goal', 'request': text})
        schema = self.router.complete.call_args.kwargs['response_schema']
        self.assertIn('goal', schema['properties']['kind']['enum'])


if __name__ == '__main__':
    unittest.main()
