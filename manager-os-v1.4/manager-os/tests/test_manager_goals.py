"""Routing through Manager must reach executable workflows with the selected identity."""
import asyncio
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock
from core.manager import Manager
from core.goal_director import GoalDirector


class ManagerGoalTests(unittest.IsolatedAsyncioTestCase):
    async def test_director_amendment_reaches_a_running_project(self):
        from core.project_work import ProjectWork
        with tempfile.TemporaryDirectory() as directory:
            config={'workflows':{'store_path':str(Path(directory)/'work.db')}}
            director=GoalDirector(config,None)
            worker=ProjectWork(config,None)
            job={'id':'active','kind':'project','status':'running','request':'Build an app','checks':[],
                 'plan':{'acceptance':[{'id':'A1','description':'Works'}]},'messages':[{'role':'user','content':'Build an app'}]}
            worker.store.save(job); director.remember('project','active')
            worker.active_id='active'; worker.active_job=job
            worker.task=asyncio.create_task(asyncio.sleep(60))
            try:
                decision=await director.resolve('Can you make it faster?','conversation')
                await worker.submit(decision['request'],{'workflow_id':decision['workflow_id']})
                self.assertEqual(len(job['plan']['acceptance']),2)
                self.assertIn('make it faster',job['request'])
                for request,intent in [('Can you publish my website?','builder'),('Can you send my resume to Alex?','career'),('Add a reminder to drink water in 10 minutes','life')]:
                    self.assertIsNone(await director.resolve(request,intent))
            finally: await worker.close()

    async def test_outcome_and_followup_reach_the_same_project_with_context(self):
        with tempfile.TemporaryDirectory() as directory:
            config = {'workflows': {'store_path': str(Path(directory)/'work.db')},
                      'conversation': {'store_path': str(Path(directory)/'history.db')}}
            router = SimpleNamespace(complete=AsyncMock(return_value='{}'), last_provider_used=None)
            manager = Manager.__new__(Manager)
            manager.config, manager.router = config, router
            manager._process_lock = asyncio.Lock()
            manager.conv_store = SimpleNamespace(get_context_messages=lambda n: [], save=AsyncMock())
            manager.goal_director = GoalDirector(config, router)
            store = manager.goal_director.store
            calls = []

            async def submit(request, context):
                calls.append((request, context.copy()))
                if not context.get('workflow_id'):
                    store.save({'id':'chosen','kind':'project','status':'running','request':request,'outputs':[],'steps':['Started']})
                return 'Actual workflow started'

            workflow = SimpleNamespace(submit=submit, accepts_followup=lambda *args:False)
            resume = SimpleNamespace(accepts_followup=lambda *args:True, submit=AsyncMock())
            manager.agents = {'builder':SimpleNamespace(project_work=workflow),
                              'career':SimpleNamespace(resume_workflow=resume)}
            manager.document_work = None
            manager.swarm = None
            self.assertEqual(await manager.process('I need a personal website for my work'), 'Actual workflow started')
            self.assertTrue(calls[0][1]['new_goal'])
            store.save({'id':'older-resume','kind':'resume','status':'interrupted','request':'Resume','outputs':[],'steps':[]})
            self.assertEqual(await manager.process('continue'), 'Actual workflow started')
            self.assertEqual(calls[1][1]['workflow_id'], 'chosen')
            resume.submit.assert_not_called()
            status = await manager.process('How is it going?')
            self.assertIn('chosen', status)
            self.assertEqual(len(calls), 2)

    async def test_new_resume_does_not_reuse_failed_job(self):
        from core.workflows import ResumeWorkflow
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as directory:
            config={'workflows':{'store_path':str(Path(directory)/'work.db')},'personal_context':{'roots':[]}}
            worker=ResumeWorkflow(config,SimpleNamespace(complete=AsyncMock()))
            worker.store.save({'id':'old','kind':'resume','status':'failed','request':'Old target','steps':[],'outputs':[],'followups':[]})
            with patch('core.workflows.discover',return_value={'documents':[]}), patch('core.workflows.user_history',return_value=[]):
                await worker.submit('Create a new resume', {'new_goal':True})
                await worker.task
            new=worker.store.latest('resume')
            self.assertNotEqual(new['id'],'old')
            self.assertEqual(worker.store.get('old')['request'],'Old target')

    async def test_cancel_selected_document_does_not_cancel_other_running_document(self):
        from core.assistant_work import AssistantWork
        with tempfile.TemporaryDirectory() as directory:
            worker=AssistantWork({'workflows':{'store_path':str(Path(directory)/'work.db')}},None)
            for identifier in ['old','active']:
                worker.store.save({'id':identifier,'kind':'document','status':'running','request':identifier,'steps':[],'outputs':[]})
            worker.active_id='active'
            worker.task=asyncio.create_task(asyncio.sleep(60))
            try:
                await worker.submit('cancel work',{'workflow_id':'old'})
                self.assertFalse(worker.task.done())
                self.assertEqual(worker.store.get('active')['status'],'running')
                self.assertEqual(worker.store.get('old')['status'],'cancelled')
            finally:
                worker.task.cancel()
                await asyncio.gather(worker.task,return_exceptions=True)


if __name__=='__main__': unittest.main()
