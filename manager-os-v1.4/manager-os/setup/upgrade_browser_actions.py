from setup.source_edit import replace_definition as replace

replace('agents/communication_agent.py', 'CommunicationAgent._handle_message', '''    async def _handle_message(self, request, context):
        import re
        # Parse only explicitly addressed send commands; never invent a fallback contact.
        match = re.fullmatch(r'(?:please )?send (?:a )?(?:whatsapp(?: message)?|message on whatsapp) to (.+?):\\s*(.+)', request.strip(), re.I | re.S)
        if not match:
            match = re.fullmatch(r'(?:please )?send (?:a )?message to (.+?) on whatsapp:\\s*(.+)', request.strip(), re.I | re.S)
        if not match:
            return ('Sir, to send an exact message use "send WhatsApp to Contact Name: your message". '
                    'Include the recipient and the full message. No message has been sent.')
        recipient, message = match[1].strip(), match[2].strip()
        if not recipient or not message:
            return 'Sir, include both the contact name and the message.'
        success = await send_whatsapp_message(recipient, message)
        if success:
            return f'Sir, WhatsApp shows your outgoing message to {recipient}.'
        return ('Sir, delivery was not confirmed. Check the automation browser and sign in to WhatsApp Web if needed. '
                'Inspect the conversation before repeating the command.')
''')
replace('core/browser_automation.py', 'get_browser_context', '''async def get_browser_context(playwright, profile_key='main'):
    from pathlib import Path
    import re
    if not re.fullmatch(r'[a-zA-Z0-9_-]+', profile_key):
        raise ValueError('Invalid browser profile name')
    config = load_config().get('chrome', {})
    # Dedicated persistent profiles preserve automation sign-ins without locking personal Chrome.
    profile_dir = Path(config.get('user_data_path') or './logs/chrome_automation') / profile_key
    profile_dir.mkdir(parents=True, exist_ok=True)
    try:
        return await playwright.chromium.launch_persistent_context(str(profile_dir.resolve()),
                        headless=False, channel='chrome', no_viewport=True, timeout=15000)
    except Exception as exc:
        if 'executable' not in str(exc).lower() and 'distribution' not in str(exc).lower():
            raise
        return await playwright.chromium.launch_persistent_context(str(profile_dir.resolve()),
                        headless=False, no_viewport=True, timeout=15000)
''')
replace('core/browser_automation.py', 'send_whatsapp_message', '''async def send_whatsapp_message(contact_name, message, attachment_path=None, profile_key='main'):
    if not contact_name.strip() or not message.strip():
        return False
    async with async_playwright() as p:
        context = await get_browser_context(p, profile_key)
        try:
            page = await context.new_page()
            await page.goto('https://web.whatsapp.com/', timeout=30000)
            search = page.locator('#side div[contenteditable="true"]').first
            await search.wait_for(timeout=60000)
            await search.fill(contact_name)
            result = page.locator('#pane-side').get_by_title(contact_name, exact=True)
            await result.first.wait_for(timeout=10000)
            if await result.count() != 1:
                logger.warning('WhatsApp contact is ambiguous; nothing sent')
                return False
            await result.click()
            await page.locator('#main header').get_by_title(contact_name, exact=True).first.wait_for(timeout=10000)
            if attachment_path:
                # Media selector support is not verified; never send a text-only substitute.
                return False
            box = page.locator('#main footer div[contenteditable="true"]').first
            await box.fill(message)
            await box.press('Enter')
            await page.locator('#main .message-out').get_by_text(message, exact=True).last.wait_for(timeout=15000)
            return True
        except Exception as exc:
            logger.warning(f'WhatsApp send not confirmed ({type(exc).__name__})')
            return False
        finally:
            await context.close()
''')
print('Explicit communication actions and dedicated browser profiles installed')
