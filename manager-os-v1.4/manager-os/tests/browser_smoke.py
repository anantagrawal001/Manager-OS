"""Real local-server/browser smoke test with isolated tasks, history and passphrase."""
import asyncio
import os
import sys
from pathlib import Path
import tempfile
import uuid
import yaml
import uvicorn
from playwright.async_api import async_playwright


async def run():
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    os.chdir(root)
    os.environ['MANAGER_NO_BROWSER'] = '1'
    os.environ['MANAGER_SILENT'] = '1'
    from security import auth
    import main
    with tempfile.TemporaryDirectory() as folder:
        temp = Path(folder)
        config = yaml.safe_load(Path('config.yaml').read_text(encoding='utf-8'))
        config['server']['port'] = 8011
        config['ai_router']['local_only'] = True
        config['storage']['tasks_path'] = str(temp/'tasks.db')
        config['conversation']['store_path'] = str(temp/'conversations.db')
        config['workflows'] = {'store_path': str(temp/'workflows.db'), 'output_root': str(root/'outputs'), 'workspace_root': str(temp/'projects')}
        config['personal_context'] = {'roots': []}
        config['self_heal']['enabled'] = False
        config['trading_alerts']['enabled'] = False
        config['voice']['enabled'] = False
        (temp/'config.yaml').write_text(yaml.safe_dump(config), encoding='utf-8')
        os.environ['MANAGER_CONFIG'] = str(temp/'config.yaml')
        original_passphrase = auth.PASSPHRASE_FILE
        auth.PASSPHRASE_FILE = temp/'passphrase.hash'
        auth.enroll_passphrase('browser-test-passphrase')
        server = uvicorn.Server(uvicorn.Config(main.app, host='127.0.0.1', port=8011, log_level='warning', timeout_graceful_shutdown=3))
        server_task = asyncio.create_task(server.serve())
        errors = []
        output_name = f'qa-browser-{uuid.uuid4().hex}.txt'
        output_file = root / 'outputs' / output_name
        try:
            for _ in range(200):
                if server.started:
                    break
                await asyncio.sleep(.1)
            assert server.started, 'Server failed to start'
            # Test against the real model but fail immediately if unrelated external automation is reached.
            import agents.communication_agent as communications
            async def unexpected_external_action(*args, **kwargs):
                raise AssertionError('External send was reached by a non-send request')
            communications.send_whatsapp_message = unexpected_external_action
            communications.create_whatsapp_group = unexpected_external_action
            async with async_playwright() as p:
                audio_fixture = root / 'logs' / 'voice-check.wav'
                args = []
                if audio_fixture.exists():
                    args = ['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream',
                            '--use-file-for-fake-audio-capture=' + str(audio_fixture)]
                browser = await p.chromium.launch(channel='chrome', headless=True, args=args)
                page = await browser.new_page(viewport={'width':1440, 'height':1000})
                page.on('pageerror', lambda error: errors.append(str(error)))
                await page.goto('http://127.0.0.1:8011')
                await page.locator('#auth-inp').fill('wrong')
                await page.locator('#auth-btn').click()
                await page.get_by_text('Invalid passphrase', exact=True).wait_for()
                assert await page.locator('#app').is_hidden()
                await page.locator('#auth-inp').fill('browser-test-passphrase')
                await page.locator('#auth-btn').click()
                await page.locator('#app').wait_for(state='visible')
                await page.wait_for_function("ws && ws.readyState === WebSocket.OPEN")
                await page.locator('#inp').fill('add task Browser smoke task')
                await page.locator('#send').click()
                await page.get_by_text('Sir, saved task #1: Browser smoke task', exact=True).wait_for()
                await page.locator('#tasks-button').click()
                await page.get_by_text('#1 Browser smoke task', exact=True).wait_for()
                await page.locator('#task-title').fill('Second saved task')
                await page.locator('#task-form button').click()
                await page.get_by_text('#2 Second saved task', exact=True).wait_for()
                await page.locator('[data-task="1"]').click()
                await page.get_by_text('#1 Browser smoke task', exact=True).wait_for(state='hidden')
                await page.screenshot(path='logs/qa-tasks.png')
                await page.locator('#close-panel').click()
                await page.locator('#inp').fill('Reply with exactly: Manager is ready.')
                await page.locator('#send').click()
                await page.locator('.msg.mgr .bubble').filter(has_text='Manager is ready.').wait_for(timeout=90000)
                await page.locator('#inp').fill(f'create file {output_name} with content Download verified')
                await page.locator('#send').click()
                await page.locator('.msg.mgr .bubble').filter(has_text='Sir, saved ').filter(has_text=output_name).wait_for()
                await page.locator('#outputs-button').click()
                row = page.locator('.connection-row').filter(has_text=output_name)
                async with page.expect_download() as download_info:
                    await row.get_by_text('Download', exact=True).click()
                download = await download_info.value
                await download.save_as(str(temp/'download.txt'))
                assert (temp/'download.txt').read_text() == 'Download verified'
                await page.locator('#close-panel').click()
                if audio_fixture.exists():
                    await page.locator('#local-mic-button').click()
                    await page.wait_for_timeout(5500)
                    await page.locator('#local-mic-button').click()
                    await page.wait_for_function("document.getElementById('inp').value.toLowerCase().includes('manager')", timeout=60000)
                    print('BROWSER_LOCAL_MIC_OK: synthetic speech recorded, uploaded locally and transcribed')
                    await page.locator('#inp').fill('')
                await page.reload()
                await page.locator('#app').wait_for(state='visible')
                await page.get_by_text('Sir, saved task #1: Browser smoke task', exact=True).wait_for()
                await page.screenshot(path='logs/qa-dashboard.png')
                await page.locator('#connections-button').click()
                await page.locator('.connection-row').filter(has_text='ollama').wait_for()
                await page.screenshot(path='logs/qa-connections.png')
                await page.locator('#close-panel').click()
                project_worker = main.manager.agents['builder'].project_work
                project = {'id': 'browser-project', 'kind': 'project', 'request': 'Browser project launch test',
                    'status': 'complete', 'steps': ['Verified test fixture'], 'outputs': [],
                    'launch': {'runtime': 'static', 'args': []}}
                project_worker.toolkit(project).write('index.html', '<!doctype html><title>Project launch verified</title><h1>Project launch verified</h1>')
                project_worker.store.save(project)
                project_worker.store.save({'id':'other-document','kind':'document','request':'Other document',
                    'status':'draft_ready','steps':[],'outputs':[]})
                main.manager.goal_director.remember('document','other-document')
                await page.locator('#work-button').click()
                project_card = page.locator('#work-list article').filter(has_text='Browser project launch test')
                await project_card.get_by_role('button',name='Use as current task').click()
                await project_card.get_by_role('button',name='Current task',exact=True).wait_for()
                assert main.manager.goal_director.focused()['id']=='browser-project'
                await page.get_by_role('button', name='Start / restart project').click()
                project_link = page.get_by_role('link', name='Open project')
                await project_link.wait_for()
                project_response = await page.request.get(await project_link.get_attribute('href'))
                assert 'Project launch verified' in await project_response.text()
                await page.locator('#close-panel').click()
                await page.locator('#logout-button').click()
                await page.locator('#auth').wait_for(state='visible')
                assert not errors, errors
                await browser.close()
            print('BROWSER_SMOKE_OK: sign-in, invalid login, chat, local AI, tasks, completion, output download, history reload, connections, lock. No JS errors.')
        finally:
            for connection in list(main.chat_connections):
                await connection.close()
            server.should_exit = True
            await server_task
            auth.PASSPHRASE_FILE = original_passphrase
            os.environ.pop('MANAGER_CONFIG', None)
            if output_file.exists():
                output_file.unlink()  # This test's uniquely named file only.


if __name__ == '__main__':
    asyncio.run(run())
