import asyncio
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import AsyncMock

from core.project_tools import ProjectTools
from core.project_work import ProjectWork
from core.routing import classify
from core.manager import Manager


PLAN = {'title': 'Adder', 'app_type': 'cli', 'summary': 'Add two numbers',
        'stack': [{'technology': 'Node.js', 'reason': 'Installed runtime'}],
        'acceptance': [{'id': 'A1', 'description': '2 + 3 equals 5'}],
        'files': [{'path': 'app.js', 'purpose': 'addition'}]}


class ProjectToolTests(unittest.TestCase):
    def test_project_goals_win_over_their_subjects(self):
        for request in ['Build a calendar app', 'Create a LinkedIn optimizer and resume maker',
                        'Make an expense tracker', 'Build a project status dashboard', 'continue project']:
            self.assertEqual(classify(request, Manager.INTENT_MAP), 'builder', request)
        self.assertEqual(classify('add task build a calendar app', Manager.INTENT_MAP), 'life')
        self.assertEqual(classify('create my resume', Manager.INTENT_MAP), 'career')

    def test_file_tools_cannot_escape_and_keep_previous_revision(self):
        with tempfile.TemporaryDirectory() as directory:
            tools = ProjectTools(directory)
            for path in ['../outside.py', 'C:/outside.py', '.manager/state.json', '.venv/code.py', 'NUL.txt']:
                with self.assertRaises(ValueError):
                    tools.write(path, 'bad')
            tools.write('app.py', 'original')
            tools.write('app.py', 'changed')
            self.assertEqual(tools.read('app.py')['content'], 'changed')
            self.assertEqual(len(list((tools.control/'revisions').rglob('app.py'))), 1)

    def test_commands_are_argument_lists_and_have_bounded_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            tools = ProjectTools(directory)
            with self.assertRaises(ValueError):
                tools.command('powershell', ['anything'])
            with self.assertRaises(ValueError):
                tools.command('python', ['-c', 'anything'])
            result = tools.run_process([sys.executable, '-c', 'import time; time.sleep(10)'], timeout=.15)
            self.assertTrue(result['timed_out'])
            self.assertNotEqual(result['exit_code'], 0)
            self.assertFalse(tools.processes)

    def test_environment_does_not_forward_provider_keys(self):
        import os
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {'OPENAI_API_KEY': 'private-key'}):
            tools = ProjectTools(directory)
            self.assertNotIn('OPENAI_API_KEY', tools.environment())
            self.assertTrue(Path(tools.environment()['HOME']).is_relative_to(Path(directory)))


class ProjectWorkflowTests(unittest.IsolatedAsyncioTestCase):
    def config(self, directory):
        return {'workflows': {'store_path': str(Path(directory)/'work.db'),
                'workspace_root': str(Path(directory)/'workspaces'), 'output_root': str(Path(directory)/'outputs'),
                'project_steps_per_run': 12}}

    @unittest.skipUnless(shutil.which('node'), 'Node runtime required')
    async def test_actual_test_failure_is_repaired_before_delivery(self):
        plan = {**PLAN, 'acceptance': PLAN['acceptance'] + [{'id': 'A2', 'description': 'Negative numbers add correctly'}]}
        actions = [plan,
            {'tool': 'write_files', 'args': {'files': [
                {'path': 'app.js', 'content': 'module.exports = (a,b) => a-b;'},
                {'path': 'tests.js', 'content': "const assert=require('node:assert/strict'); const add=require('./app'); assert.equal(add(2,3),5); assert.equal(add(-1,3),2); console.log('2 assertions passed');"},
                {'path': 'README.txt', 'content': 'Run node tests.js to verify this project.'}]}},
            {'tool': 'run_check', 'args': {'runtime': 'node', 'args': ['tests.js'], 'criteria': ['A1','A2']}},
            {'tool': 'write_file', 'args': {'path': 'app.js', 'content': 'module.exports = (a,b) => a+b;'}},
            {'tool': 'run_check', 'args': {'runtime': 'node', 'args': ['tests.js'], 'criteria': ['A1','A2']}},
            {'tool': 'finish', 'args': {'summary': 'Addition works'}},
            {'passed': True, 'blockers': []}]
        with tempfile.TemporaryDirectory() as directory:
            router = type('Router', (), {'complete': AsyncMock(side_effect=[json.dumps(a) for a in actions])})()
            worker = ProjectWork(self.config(directory), router)
            await worker.submit('Build an addition utility', {})
            await worker.task
            job = worker.store.latest('project')
            self.assertEqual(job['status'], 'complete', job.get('error'))
            self.assertFalse(job['checks'][0]['passed'])
            self.assertTrue(job['checks'][1]['passed'])
            self.assertTrue((Path(directory)/'outputs'/job['outputs'][0]).exists())
            # The actual assertion failure was fed back into the next model call.
            feedback = json.dumps(router.complete.call_args_list[3].kwargs['messages'])
            self.assertIn('AssertionError', feedback)
            await worker.close()

    async def test_changed_source_invalidates_prior_checks(self):
        with tempfile.TemporaryDirectory() as directory:
            worker = ProjectWork(self.config(directory), None)
            job = {'id': 'example', 'plan': PLAN, 'checks': []}
            tools = worker.toolkit(job)
            tools.write('app.js', 'first')
            tools.write('README.txt', 'Run the app')
            job['checks'] = [{'passed': True, 'fingerprint': tools.fingerprint(), 'criteria': ['A1'], 'kind': 'runtime'}]
            self.assertTrue(worker.acceptance_covered(job, tools)[0])
            tools.write('app.js', 'second')
            self.assertFalse(worker.acceptance_covered(job, tools)[0])
            await worker.close()

    async def test_web_goal_requires_browser_assertions(self):
        with tempfile.TemporaryDirectory() as directory:
            worker = ProjectWork(self.config(directory), None)
            job = {'id': 'example', 'plan': {**PLAN, 'app_type': 'web'}, 'checks': []}
            tools = worker.toolkit(job)
            tools.write('README.txt', 'Run the app')
            job['checks'] = [{'passed': True, 'fingerprint': tools.fingerprint(), 'criteria': ['A1'], 'kind': 'runtime'}]
            self.assertIn('browser', worker.acceptance_covered(job, tools)[1])
            await worker.close()

    async def test_browser_tool_exercises_a_real_local_page(self):
        with tempfile.TemporaryDirectory() as directory:
            tools = ProjectTools(directory)
            tools.write('index.html', '<!doctype html><title>Test</title><input id="name"><button onclick="document.querySelector(\'#result\').textContent=document.querySelector(\'#name\').value">Create</button><p id="result"></p>')
            try:
                await asyncio.to_thread(tools.start_server, 'static', [])
                result = await asyncio.to_thread(tools.browser_test, [
                    {'action': 'fill', 'selector': '#name', 'value': 'Verified goal'},
                    {'action': 'click', 'selector': 'button'},
                    {'action': 'assert_text', 'selector': '#result', 'text': 'Verified goal'},
                    {'action': 'assert_visible', 'selector': '#name'}])
                self.assertTrue(result['passed'])
                self.assertEqual(result['assertions'], 2)
                http_result = await asyncio.to_thread(tools.http_test, {'path': '/', 'status': 200, 'contains': ['<title>Test</title>']})
                self.assertTrue(http_result['passed'])
            finally:
                await asyncio.to_thread(tools.close)

    async def test_placeholder_tests_and_runtime_data_do_not_fake_verification(self):
        with tempfile.TemporaryDirectory() as directory:
            tools = ProjectTools(directory)
            tools.write('tests/test_example.py', 'def test_upload():\n    pass\n')
            self.assertEqual(tools.placeholder_tests(), ['tests/test_example.py:test_upload'])
            fingerprint = tools.fingerprint()
            (tools.root/'user-upload.json').write_text('{"private":"user data"}')
            self.assertEqual(fingerprint, tools.fingerprint())
            import zipfile
            archive = Path(directory)/'result.zip'
            tools.archive(archive)
            with zipfile.ZipFile(archive) as bundle:
                self.assertNotIn('user-upload.json', bundle.namelist())

    async def test_added_requirement_must_have_its_own_check(self):
        with tempfile.TemporaryDirectory() as directory:
            worker = ProjectWork(self.config(directory), None)
            job = {'id': 'example', 'kind': 'project', 'status': 'running', 'request': 'Build adder',
                'plan': json.loads(json.dumps(PLAN)), 'messages': [{'role': 'user', 'content': 'goal'}], 'checks': []}
            tools = worker.toolkit(job)
            tools.write('README.txt', 'Run node app.js')
            job['checks'] = [{'passed': True, 'fingerprint': tools.fingerprint(), 'criteria': ['A1'], 'kind': 'runtime'}]
            worker.add_requirement(job, 'Also support decimal numbers')
            self.assertIn('A2', worker.acceptance_covered(job, tools)[1])
            await worker.close()


if __name__ == '__main__':
    unittest.main()
