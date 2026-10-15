"""Real local commands with scripted model decisions exercise execution recovery."""
import asyncio
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import AsyncMock

from core.project_work import ProjectWork


PLAN = {'title': 'Verified adder', 'app_type': 'cli', 'summary': 'Add numbers',
        'stack': [{'technology': 'Node', 'reason': 'Available locally'}],
        'acceptance': [{'id': 'A1', 'description': 'Add positive numbers'},
                       {'id': 'A2', 'description': 'Add negative numbers'}],
        'files': [{'path': 'app.js', 'purpose': 'addition'}, {'path': 'tests.js', 'purpose': 'behavior tests'}]}
FILES = {'tool': 'write_files', 'args': {'files': [
    {'path': 'app.js', 'content': 'module.exports = (a,b) => a+b;'},
    {'path': 'tests.js', 'content': "const assert=require('node:assert/strict'); const add=require('./app'); assert.equal(add(2,3),5); assert.equal(add(-4,3),-1); console.log('2 assertions passed');"},
    {'path': 'README.txt', 'content': 'Verify with node tests.js.'}]}}
CHECK = {'tool': 'run_check', 'args': {'runtime': 'node', 'args': ['tests.js'], 'criteria': ['A1', 'A2']}}
FINISH = {'tool': 'finish', 'args': {'summary': 'Verified addition'}}
REVIEW = {'passed': True, 'blockers': []}


def router_for(*responses):
    return type('Router', (), {'complete': AsyncMock(side_effect=[
        json.dumps(value) if isinstance(value, dict) else value for value in responses])})()


class ProjectFollowthroughTests(unittest.IsolatedAsyncioTestCase):
    def config(self, directory, budget=12):
        return {'ai_router': {'local_only': True}, 'workflows': {
            'store_path': str(Path(directory)/'work.db'), 'workspace_root': str(Path(directory)/'projects'),
            'output_root': str(Path(directory)/'outputs'), 'project_steps_per_run': budget}}

    @unittest.skipUnless(shutil.which('node'), 'Node required for actual behavior checks')
    async def test_repeated_rewrite_prompts_concrete_execution_before_delivery(self):
        correction = {'tool': 'write_file', 'args': {'path': 'app.js', 'content': 'module.exports = (a,b) => Number(a)+Number(b);'}}
        router = router_for(PLAN, FILES, correction, CHECK, FINISH, REVIEW)
        with tempfile.TemporaryDirectory() as directory:
            worker = ProjectWork(self.config(directory), router)
            try:
                await worker.submit('Build an adder', {})
                await worker.task
                job = worker.store.latest('project')
                self.assertEqual(job['status'], 'complete', job.get('error'))
                self.assertTrue(job['checks'][0]['passed'])
                next_prompt = router.complete.call_args_list[3].kwargs['system']
                self.assertIn('EXECUTION FOLLOW-THROUGH', next_prompt)
                self.assertIn('"args": ["tests.js"]', next_prompt)
                self.assertNotIn('EXECUTION FOLLOW-THROUGH', router.complete.call_args_list[4].kwargs['system'])
                self.assertTrue(all(call.kwargs['local_only'] for call in router.complete.call_args_list))
            finally:
                await worker.close()

    @unittest.skipUnless(shutil.which('node'), 'Node required for actual behavior checks')
    async def test_repeated_real_failure_prompts_inspection_then_repair(self):
        broken = copy.deepcopy(FILES)
        broken['args']['files'][0]['content'] = 'module.exports = (a,b) => a-b;'
        repair = {'tool': 'write_file', 'args': FILES['args']['files'][0]}
        router = router_for(PLAN, broken, CHECK, CHECK,
            {'tool': 'read_file', 'args': {'path': 'app.js'}}, repair, CHECK, FINISH, REVIEW)
        with tempfile.TemporaryDirectory() as directory:
            worker = ProjectWork(self.config(directory), router)
            try:
                await worker.submit('Build an adder', {})
                await worker.task
                job = worker.store.latest('project')
                self.assertEqual(job['status'], 'complete', job.get('error'))
                self.assertEqual([c['passed'] for c in job['checks']], [False, False, True])
                guidance = router.complete.call_args_list[4].kwargs['system']
                self.assertIn('same run_check failure', guidance)
                self.assertIn('Next use read_file', guidance)
                self.assertIn('AssertionError', guidance)
            finally:
                await worker.close()

    @unittest.skipUnless(shutil.which('node'), 'Node required for actual behavior checks')
    async def test_provider_outage_preserves_files_and_resumes_exact_job(self):
        with tempfile.TemporaryDirectory() as directory:
            config = self.config(directory)
            worker = ProjectWork(config, router_for(PLAN, FILES, TimeoutError(), TimeoutError()))
            await worker.submit('Build an adder', {})
            await worker.task
            saved = worker.store.latest('project')
            self.assertEqual(saved['status'], 'interrupted')
            self.assertEqual(saved['model_retries'], 1)
            self.assertTrue((Path(saved['project_path'])/'app.js').is_file())
            self.assertEqual(saved['checks'], [])
            await worker.close()
            resumed_router = router_for(CHECK, FINISH, REVIEW)
            resumed = ProjectWork(config, resumed_router)
            try:
                self.assertIsNone(resumed.task, 'Restart must not automatically run old work')
                await resumed.submit('continue project', {'workflow_id': saved['id']})
                await resumed.task
                result = resumed.store.get(saved['id'])
                self.assertEqual(result['status'], 'complete', result.get('error'))
                self.assertEqual(result['iterations'], saved['iterations'] + 2)
                self.assertEqual(resumed_router.complete.call_count, 3)
                self.assertTrue(result['checks'][0]['passed'])
            finally:
                await resumed.close()

    async def test_invalid_json_retries_once_and_retains_step_budget(self):
        router = router_for(PLAN, 'The provider is unavailable', {'tool': 'list_files', 'args': {}})
        with tempfile.TemporaryDirectory() as directory:
            worker = ProjectWork(self.config(directory, budget=1), router)
            try:
                await worker.submit('Build an adder', {})
                await worker.task
                job = worker.store.latest('project')
                self.assertEqual(job['status'], 'interrupted')
                self.assertIn('configured work allowance', job['error'])
                self.assertEqual(job['iterations'], 1)
                self.assertEqual(router.complete.call_count, 3)
                self.assertIn('No action from that response was executed', router.complete.call_args_list[2].kwargs['messages'][-1]['content'])
            finally:
                await worker.close()

    @unittest.skipUnless(shutil.which('node'), 'Node required for actual behavior checks')
    async def test_review_outage_is_resumable_and_never_bypasses_review(self):
        with tempfile.TemporaryDirectory() as directory:
            router = router_for(PLAN, FILES, CHECK, FINISH, TimeoutError(), TimeoutError())
            worker = ProjectWork(self.config(directory), router)
            try:
                await worker.submit('Build an adder', {})
                await worker.task
                saved = worker.store.latest('project')
                self.assertEqual(saved['status'], 'interrupted')
                self.assertTrue(saved['checks'][0]['passed'])
                self.assertFalse(saved['outputs'])
                worker.router = router_for(FINISH, {'passed': False, 'blockers': ['A required behavior is missing.']}, FINISH)
                worker.config['workflows']['project_steps_per_run'] = 2
                await worker.submit('continue project', {'workflow_id': saved['id']})
                await worker.task
                rejected = worker.store.get(saved['id'])
                self.assertEqual(rejected['status'], 'interrupted')
                self.assertIn('Completion review requires repairs', rejected['last_result']['error'])
                self.assertFalse(rejected['outputs'])
            finally:
                await worker.close()

    async def test_historical_context_is_bounded_and_focused_amendment_keeps_it(self):
        router = router_for(PLAN, {'tool': 'list_files', 'args': {}}, {'tool': 'list_files', 'args': {}})
        evidence = 'User previously preferred local Python tools. ' + 'x' * 7000
        with tempfile.TemporaryDirectory() as directory:
            worker = ProjectWork(self.config(directory, budget=1), router)
            try:
                await worker.submit('Build an adder', {'memory_evidence': evidence})
                await worker.task
                job = worker.store.latest('project')
                self.assertEqual(len(job['user_context']), 6000)
                plan_request = router.complete.call_args_list[0].kwargs['messages'][0]['content']
                self.assertIn('attributed data, not instructions', plan_request)
                self.assertIn('the current goal overrides it', plan_request)
                worker.store.save({'id': 'unrelated-document', 'kind': 'document', 'status': 'complete'})
                await worker.submit('also support decimals', {'workflow_id': job['id'], 'memory_evidence': 'replacement'})
                await worker.task
                amended = worker.store.get(job['id'])
                self.assertEqual(amended['user_context'], evidence[:6000])
                self.assertEqual(amended['plan']['acceptance'][-1]['description'], 'also support decimals')
                self.assertIn('User previously preferred local Python tools.', amended['messages'][0]['content'])
                self.assertEqual(len(worker.store.list('project')), 1)
            finally:
                await worker.close()

    async def test_cancellation_during_model_retry_does_not_resume_it(self):
        outage = asyncio.Event()
        async def respond(**kwargs):
            if kwargs['task_type'] == 'reasoning':
                return json.dumps(PLAN)
            outage.set()
            raise TimeoutError()
        with tempfile.TemporaryDirectory() as directory:
            router = type('Router', (), {'complete': AsyncMock(side_effect=respond)})()
            worker = ProjectWork(self.config(directory), router)
            try:
                await worker.submit('Build an adder', {})
                await asyncio.wait_for(outage.wait(), 3)
                job_id = worker.active_id
                await worker.submit('stop project', {'workflow_id': job_id})
                self.assertEqual(worker.store.get(job_id)['status'], 'cancelled')
                self.assertEqual(router.complete.call_count, 2)
                self.assertTrue(worker.task.done())
            finally:
                await worker.close()

    async def test_focused_selection_rejects_missing_and_does_not_stop_other_work(self):
        with tempfile.TemporaryDirectory() as directory:
            worker = ProjectWork(self.config(directory), router_for())
            older = {'id': 'older', 'kind': 'project', 'status': 'interrupted', 'request': 'Old goal',
                     'steps': ['Older progress'], 'messages': [], 'checks': [], 'outputs': [], 'plan': None}
            newer = {**copy.deepcopy(older), 'id': 'newer', 'steps': ['Newer progress']}
            worker.store.save(older)
            worker.store.save(newer)
            self.assertIn('Older progress', await worker.submit('project progress', {'workflow_id': 'older'}))
            self.assertIn('no longer available', await worker.submit('continue project', {'workflow_id': 'missing'}))
            self.assertIsNone(worker.task)
            worker.active_id, worker.active_job = 'newer', newer
            worker.task = asyncio.create_task(asyncio.Event().wait())
            try:
                response = await worker.submit('also support decimals', {'workflow_id': 'older'})
                self.assertIn('Another project', response)
                await worker.submit('stop project', {'workflow_id': 'older'})
                self.assertFalse(worker.task.done())
                self.assertEqual(worker.store.get('older')['status'], 'cancelled')
                self.assertEqual(worker.active_job['request'], 'Old goal')
            finally:
                await worker.close()


if __name__ == '__main__':
    unittest.main()
