import asyncio
import json
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from core.routing import classify
from core.manager import Manager
from core.local_tasks import LocalTasks
from core.swarm import SwarmEngine
from core.router import AIRouter
from agents.files_agent import FilesAgent
from agents.life_agent import LifeAgent
from agents.communication_agent import CommunicationAgent
from core.artifacts import save_project
from security import auth


class RoutingTests(unittest.TestCase):
    def test_new_key_is_selected_and_persists_across_restart(self):
        import core.key_manager as keys
        with tempfile.TemporaryDirectory() as folder, patch.object(keys, 'VAULT_PATH', Path(folder)/'vault.enc'), patch.object(keys, 'KEY_FILE', Path(folder)/'key'):
            manager = keys.KeyManager({})
            manager.add_key('groq','old-test-key','test')
            manager.add_key('groq','new-test-key','test')
            self.assertEqual(manager.get_key('groq'),'new-test-key')
            reloaded = keys.KeyManager({})
            self.assertEqual(reloaded.get_key('groq'),'new-test-key')

    def test_concrete_commands_win(self):
        cases = {'show agents status': 'system', 'what model are you using': 'system',
                 'send image to John on WhatsApp': 'communication', 'simulate recruiter call': 'communication',
                 'create file script.py with content print(1)': 'files', 'open calculator': 'files',
                 'add task apply for jobs today': 'life', 'remind me in 2 minutes to review my resume': 'life',
                 'do you remember my interview': 'conversation_memory', 'hello, thanks': 'conversation',
                 'what is the weather?': 'conversation', 'Reply with exactly: Manager is ready.': 'conversation',
                 'reply to this message': 'conversation'}
        for request, expected in cases.items():
            with self.subTest(request=request):
                self.assertEqual(classify(request, Manager.INTENT_MAP), expected)

    def test_auth_never_accepts_unknown_passphrase(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(auth, 'PASSPHRASE_FILE', Path(folder)/'passphrase.hash'):
            self.assertFalse(auth.verify_passphrase('anything'))
            auth.enroll_passphrase('a-test-passphrase')
            self.assertTrue(auth.verify_passphrase('a-test-passphrase'))
            self.assertFalse(auth.verify_passphrase('wrong'))
            with self.assertRaises(ValueError):
                auth.enroll_passphrase('different-passphrase')


class ActionTests(unittest.IsolatedAsyncioTestCase):
    async def test_communications_require_explicit_recipient_and_message(self):
        agent = CommunicationAgent({}, None, None)
        with patch('agents.communication_agent.send_whatsapp_message', new_callable=AsyncMock) as send:
            result = await agent._handle_message('Reply with exactly: Manager is ready.', {})
            self.assertIn('No message has been sent', result)
            send.assert_not_called()
            send.return_value = True
            await agent._handle_message('send WhatsApp to Test Contact: Exact text only', {})
            send.assert_awaited_once_with('Test Contact', 'Exact text only')

    async def test_artifacts_are_saved_and_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            output, archive = save_project(json.dumps({'files':[{'path':'index.html','content':'<h1>Hello</h1>'}]}), folder)
            self.assertTrue(archive.exists())
            self.assertEqual((output/'index.html').read_text(),'<h1>Hello</h1>')
            with self.assertRaises(ValueError):
                save_project(json.dumps({'files':[{'path':'../escape.txt','content':'bad'}]}), folder)

    async def test_tasks_persist_complete_and_notify_once(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'tasks.db'
            tasks = LocalTasks(path)
            number = tasks.add('review resume', (datetime.now()-timedelta(seconds=1)).isoformat())
            reloaded = LocalTasks(path)
            self.assertEqual(reloaded.list()[0]['title'], 'review resume')
            notify = AsyncMock()
            await reloaded.deliver_due(notify)
            await reloaded.deliver_due(notify)
            notify.assert_awaited_once()
            self.assertTrue(reloaded.complete(number))
            self.assertEqual(reloaded.list(), [])

    async def test_failed_delivery_is_retried(self):
        with tempfile.TemporaryDirectory() as folder:
            tasks = LocalTasks(Path(folder)/'tasks.db')
            tasks.add('retry reminder', (datetime.now()-timedelta(seconds=1)).isoformat())
            with self.assertRaises(ConnectionError):
                await tasks.deliver_due(AsyncMock(side_effect=ConnectionError()))
            notify = AsyncMock()
            await tasks.deliver_due(notify)
            notify.assert_awaited_once()

    async def test_file_workflow_without_ai_and_no_overwrite(self):
        router = SimpleNamespace(complete=AsyncMock(side_effect=AssertionError('AI not needed')))
        with tempfile.TemporaryDirectory() as folder:
            agent = FilesAgent({'files': {'search_roots':[folder]}}, router, None)
            filename = Path(folder)/'notes.txt'
            result = await agent.execute(f'create file "{filename}" with content Hello Manager', {})
            self.assertIn('saved', result)
            self.assertEqual(filename.read_text(), 'Hello Manager')
            result = await agent.execute(f'create file "{filename}" with content Other', {})
            self.assertIn('already exists', result)
            self.assertIn(str(filename), await agent.execute('find file notes.txt', {}))
            self.assertIn('Hello Manager', await agent.execute('read file 1', {}))
            self.assertIn('supported apps', await agent._launch_app('open notepad & calc', {}))
            router.complete.assert_not_called()

    async def test_life_commands_save_instead_of_only_describing(self):
        with tempfile.TemporaryDirectory() as folder:
            agent = LifeAgent({'storage':{'tasks_path':str(Path(folder)/'tasks.db')}}, None, None)
            self.assertIn('saved task', await agent.execute('add task apply for jobs today', {}))
            self.assertIn('apply for jobs', await agent.execute('list tasks', {}))
            self.assertIn('reminder #', await agent.execute('remind me in 1 minute to take a break', {}))

    async def test_swarm_executes_selected_agent_once(self):
        first = SimpleNamespace(execute=AsyncMock(return_value='sent'))
        wrong = SimpleNamespace(execute=AsyncMock(return_value='wrong'))
        with tempfile.TemporaryDirectory() as folder, patch.object(SwarmEngine, 'HOOKS_FILE', Path(folder)/'hooks.json'):
            swarm = SwarmEngine({}, {'communication':first,'creative':wrong})
            result = await swarm.dispatch('send image design poster on WhatsApp', 'communication')
            self.assertEqual(result, 'sent')
            first.execute.assert_awaited_once()
            wrong.execute.assert_not_called()

    async def test_provider_failure_has_bounded_fallback_and_truthful_status(self):
        router = AIRouter({'ai_router':{'local_only':True}})
        router._call_provider = AsyncMock(side_effect=ConnectionError())
        result = await router.complete('', [{'role':'user','content':'hi'}])
        self.assertIn('no AI provider responded', result)
        self.assertNotIn('Ollama local is running', result)
        self.assertEqual(router.working_providers, [])
        await router.close()

    async def test_chat_history_contains_current_message_once(self):
        mgr = Manager.__new__(Manager)
        mgr._process_lock = asyncio.Lock()
        mgr.router = SimpleNamespace(complete=AsyncMock(return_value='Hello'), last_provider_used='test')
        mgr.conv_store = SimpleNamespace(get_context_messages=lambda n: [], save=AsyncMock())
        await mgr.process('hello')
        messages = mgr.router.complete.call_args.kwargs['messages']
        self.assertEqual(messages, [{'role':'user','content':'hello'}])


class APITests(unittest.TestCase):
    def setUp(self):
        import main
        from fastapi.testclient import TestClient
        self.main = main
        main._bypass_auth = False
        main.config = {'server':{'port':8000}}
        self.temp = tempfile.TemporaryDirectory()
        self.tasks = LocalTasks(Path(self.temp.name)/'tasks.db')
        main.manager = SimpleNamespace(active=True, process=AsyncMock(return_value='Completed'),
            agents={'life':SimpleNamespace(tasks=self.tasks)}, speak=AsyncMock())
        self.client = TestClient(main.app)
        self.token = auth.create_session()
        self.headers = {'Authorization':f'Bearer {self.token}'}

    def tearDown(self):
        self.client.close()
        self.temp.cleanup()
        self.main.manager = None

    def test_all_sensitive_routes_require_login(self):
        for route in ['/api/history','/api/status','/api/providers','/api/tasks','/api/logs/recent','/api/self-heal/report']:
            self.assertEqual(self.client.get(route).status_code,401,route)
        for route in ['/api/chat','/api/search','/api/sync','/api/morning-briefing','/api/providers/check']:
            self.assertEqual(self.client.post(route,json={}).status_code,401,route)
        self.assertEqual(self.client.post('/api/chat',json={'message':'hi'},headers={**self.headers,'Origin':'https://evil.example'}).status_code,403)

    def test_task_api_round_trip_and_validation(self):
        response = self.client.post('/api/tasks',json={'title':'Test saved task'},headers=self.headers)
        self.assertEqual(response.status_code,200)
        number=response.json()['id']
        self.assertEqual(len(self.client.get('/api/tasks',headers=self.headers).json()['tasks']),1)
        self.assertEqual(self.client.post(f'/api/tasks/{number}/complete',headers=self.headers).status_code,200)
        self.assertEqual(self.client.get('/api/tasks',headers=self.headers).json()['tasks'],[])
        self.assertEqual(self.client.post('/api/chat',json={'message':123},headers=self.headers).status_code,400)
        self.assertEqual(self.client.get('/api/outputs/download?path=../config.yaml',headers=self.headers).status_code,404)
        self.assertEqual(self.client.post('/api/auth/logout',headers=self.headers).status_code,200)
        self.assertEqual(self.client.get('/api/tasks',headers=self.headers).status_code,401)

    def test_websocket_survives_bad_payload_and_deduplicates(self):
        with self.client.websocket_connect(f'/ws?token={self.token}') as ws:
            ws.send_text('invalid json')
            self.assertEqual(ws.receive_json()['type'],'error')
            payload={'id':'test-command','content':'hello'}
            ws.send_json(payload)
            self.assertEqual(ws.receive_json()['type'],'thinking')
            self.assertEqual(ws.receive_json()['content'],'Completed')
            ws.send_json(payload)
            self.assertEqual(ws.receive_json()['content'],'Completed')
            self.main.manager.process.assert_awaited_once()


if __name__ == '__main__':
    unittest.main()
