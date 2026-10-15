"""Real Chrome + local model: tool use, progress UI, background chat, and download."""
import asyncio
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
os.environ['MANAGER_NO_BROWSER'] = '1'
os.environ['MANAGER_SILENT'] = '1'

import yaml
import uvicorn
from playwright.async_api import async_playwright


async def run():
    from security import auth
    import main
    with tempfile.TemporaryDirectory() as directory:
        temp = Path(directory)
        docs = temp/'Documents'; docs.mkdir()
        (docs/'weekly-notes.txt').write_text('Alex Example: Completed the SQL migration on Monday. The reporting dashboard still needs validation. Next priority: verify report totals and prepare handover notes.')
        config = yaml.safe_load((ROOT/'config.yaml').read_text(encoding='utf-8'))
        config['server']['port'] = 8012
        config['manager']['owner'] = 'Alex'
        config['personal_context'] = {'roots': [str(docs)]}
        config['workflows'] = {'store_path': str(temp/'work.db'), 'output_root': str(ROOT/'outputs')}
        config['storage']['tasks_path'] = str(temp/'tasks.db')
        config['conversation']['store_path'] = str(temp/'chat.db')
        config['ai_router']['local_only'] = True
        config['self_heal']['enabled'] = False
        config['trading_alerts']['enabled'] = False
        config['voice']['enabled'] = False
        (temp/'config.yaml').write_text(yaml.safe_dump(config), encoding='utf-8')
        os.environ['MANAGER_CONFIG'] = str(temp/'config.yaml')
        original_hash = auth.PASSPHRASE_FILE
        auth.PASSPHRASE_FILE = temp/'passphrase.hash'
        auth.enroll_passphrase('workflow-browser-test')
        server = uvicorn.Server(uvicorn.Config(main.app, host='127.0.0.1', port=8012, log_level='warning'))
        server_task = asyncio.create_task(server.serve())
        errors = []
        try:
            for _ in range(200):
                if server.started:
                    break
                await asyncio.sleep(.1)
            assert server.started
            async with async_playwright() as p:
                browser = await p.chromium.launch(channel='chrome', headless=True)
                page = await browser.new_page(viewport={'width': 1440, 'height': 1000})
                page.on('pageerror', lambda error: errors.append(str(error)))
                await page.goto('http://127.0.0.1:8012')
                await page.locator('#auth-inp').fill('workflow-browser-test')
                await page.locator('#auth-btn').click()
                await page.wait_for_function('ws && ws.readyState === WebSocket.OPEN')
                await page.locator('#inp').fill('Summarize my weekly-notes document into a concise progress update and next steps. Find and read the local file, then save the finished update.')
                await page.locator('#send').click()
                await page.locator('.msg.mgr .bubble').filter(has_text='I started the document task').wait_for(timeout=10000)
                await page.locator('#inp').fill('add task Independent task while document work runs')
                await page.locator('#send').click()
                await page.locator('.msg.mgr .bubble').filter(has_text='saved task #1').wait_for(timeout=10000)
                await page.locator('#work-button').click()
                await page.locator('#work-list article').wait_for(timeout=10000)
                await page.screenshot(path='logs/qa-work-running.png')
                for _ in range(240):
                    job = main.manager.document_work.store.latest('document')
                    if job and job['status'] != 'running':
                        break
                    await asyncio.sleep(1)
                import json
                (ROOT/'logs'/'qa-document-work.json').write_text(json.dumps(job, indent=2), encoding='utf-8')
                assert job['status'] == 'draft_ready', (job['status'], job.get('error'), job.get('question'))
                assert any('weekly-notes' in source for source in job['read_sources'])
                await page.locator('#work-refresh').click()
                await page.get_by_text('Output files saved and checked', exact=True).wait_for()
                await page.screenshot(path='logs/qa-work-ready.png')
                await page.locator('#work-outputs').click()
                output = next(path for path in job['outputs'] if path.endswith('.txt'))
                row = page.locator('.connection-row').filter(has_text=output.replace('\\', '/'))
                async with page.expect_download() as download_info:
                    await row.get_by_text('Download', exact=True).click()
                download = await download_info.value
                text = Path(await download.path()).read_text(encoding='utf-8')
                assert 'SQL' in text and 'validat' in text.lower(), text
                assert not errors, errors
                await browser.close()
                print('BROWSER_WORKFLOWS_OK: real local model found/read source, saved draft, progress panel, independent chat, authenticated download; no JS errors.', flush=True)
        finally:
            for connection in list(main.chat_connections):
                await connection.close()
            server.should_exit = True
            await server_task
            auth.PASSPHRASE_FILE = original_hash
            os.environ.pop('MANAGER_CONFIG', None)


if __name__ == '__main__':
    asyncio.run(run())
