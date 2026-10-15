"""
MANAGER OS — Browser Automation Engine
FILE: core/browser_automation.py
CREATED: 2026-06-06 | Claude Sonnet 4.6
PURPOSE: Headful Playwright automation running on real Google Chrome.
         Integrates with WhatsApp Web and Instagram signup.
         Supports multiple Chrome profiles and remote debugging CDP connections.
"""

import os
import asyncio
import yaml
from typing import List, Optional
from playwright.async_api import async_playwright
from loguru import logger

def load_config() -> dict:
    """Load configuration variables from config.yaml safely."""
    try:
        with open("config.yaml", "r") as f:
            return yaml.safe_load(f)
    except Exception:
        return {}

# Superseded 2026-10-12: retained for rollback; corrected implementation below.
# async def get_browser_context(playwright, profile_key: str = "main"):
#     """Launch persistent Google Chrome context or connect via CDP."""
#     config = load_config()
#     chrome_config = config.get("chrome", {})
#
#     # 1. Check if Remote Debugging is active on localhost:9222 (remote CDP)
#     debug_port = chrome_config.get("remote_debugging_port", 9222)
#     try:
#         logger.info(f"Checking for active Chrome remote debugging instance on port {debug_port}...")
#         browser = await playwright.chromium.connect_over_cdp(f"http://127.0.0.1:{debug_port}")
#         logger.info("Connected to existing Google Chrome debugging instance via CDP successfully!")
#
#         # Get or create active context
#         if browser.contexts:
#             return browser.contexts[0]
#         context = await browser.new_context()
#         return context
#     except Exception as e:
#         logger.info(f"No active remote debugging instance found (or connection failed: {e}). Launching headful...")
#
#     # 2. Get profile directory mapped from config
#     profile_name = "Default"
#     if "profiles" in chrome_config and profile_key in chrome_config["profiles"]:
#         profile_name = chrome_config["profiles"][profile_key]
#
#     # 3. Resolve user data folder
#     user_data_dir = chrome_config.get("user_data_path")
#     if not user_data_dir:
#         # Default LocalAppData path on Windows
#         user_data_dir = os.path.expandvars(r"%LocalAppData%\Google\Chrome\User Data")
#
#     logger.info(f"Targeting Chrome profile: '{profile_name}' in folder: '{user_data_dir}'")
#
#     # 4. Try to launch persistent context using real Chrome on the system
#     try:
#         context = await playwright.chromium.launch_persistent_context(
#             user_data_dir=user_data_dir,
#             headless=False,
#             channel="chrome",
#             args=[
#                 f"--profile-directory={profile_name}",
#                 "--start-maximized",
#                 "--disable-blink-features=AutomationControlled"
#             ],
#             no_viewport=True
#         )
#         return context
#     except Exception as launch_err:
#         logger.warning(
#             f"Failed to launch main Chrome user profile (likely due to file locks): {launch_err}. "
#             "Falling back to isolated context directory."
#         )
#
#         # Fallback to isolated user data directory in logs to avoid lock crashes
#         fallback_dir = os.path.abspath("./logs/chrome_user_data")
#         os.makedirs(fallback_dir, exist_ok=True)
#         context = await playwright.chromium.launch_persistent_context(
#             user_data_dir=fallback_dir,
#             headless=False,
#             channel="chrome",
#             args=[
#                 "--start-maximized",
#                 "--disable-blink-features=AutomationControlled"
#             ],
#             no_viewport=True
#         )
#         logger.warning("Isolated Chrome session active. Main session logins are not shared.")
#         return context

async def get_browser_context(playwright, profile_key='main'):
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

async def find_message_box(page):
    """Find the WhatsApp Web active message input box robustly."""
    selectors = [
        'footer div[contenteditable="true"]',
        'div[contenteditable="true"][data-tab="10"]',
        'div[contenteditable="true"]'
    ]
    for sel in selectors:
        loc = page.locator(sel)
        count = await loc.count()
        if count > 1 and sel == 'div[contenteditable="true"]':
            return loc.nth(1)
        elif count > 0:
            return loc.first
    raise Exception("Message input box not found")

# Superseded 2026-10-12: retained for rollback; corrected implementation below.
# async def send_whatsapp_message(contact_name: str, message: str, attachment_path: Optional[str] = None, profile_key: str = "main") -> bool:
#     """Send a text and optional file attachment to a WhatsApp contact."""
#     logger.info(f"WhatsApp message automation: contact='{contact_name}', attachment={attachment_path}")
#
#     async with async_playwright() as p:
#         context = await get_browser_context(p, profile_key=profile_key)
#         page = await context.new_page()
#
#         try:
#             logger.info("Opening WhatsApp Web...")
#             await page.goto("https://web.whatsapp.com/")
#
#             search_box_selector = 'div[contenteditable="true"]'
#             logger.info("Waiting for WhatsApp Web to load/authenticate (up to 60s)...")
#             try:
#                 await page.wait_for_selector(search_box_selector, timeout=60000)
#             except Exception:
#                 logger.error("WhatsApp Web failed to load search box. Verification/Login timed out.")
#                 await context.close()
#                 return False
#
#             logger.info("WhatsApp Web loaded. Searching for contact...")
#             search_box = page.locator(search_box_selector).first
#             await search_box.click()
#             await search_box.fill(contact_name)
#             await page.keyboard.press("Enter")
#             await page.wait_for_timeout(2000)
#
#             # Click contact element directly if found in list
#             contact_item = page.locator(f'span[title="{contact_name}"]')
#             if await contact_item.count() > 0:
#                 await contact_item.first.click()
#                 await page.wait_for_timeout(1000)
#             else:
#                 await page.keyboard.press("Enter")
#                 await page.wait_for_timeout(1000)
#
#             if attachment_path and os.path.exists(attachment_path):
#                 logger.info(f"Uploading file: {attachment_path}")
#                 file_input = page.locator('input[type="file"]').first
#                 await file_input.set_input_files(attachment_path)
#                 await page.wait_for_timeout(3000)
#
#                 caption_box = page.locator('div[contenteditable="true"]').nth(1)
#                 if await caption_box.count() > 0:
#                     await caption_box.fill(message)
#                     await page.wait_for_timeout(1000)
#
#                 send_btn = page.locator('span[data-icon="send"], div[aria-label="Send"], button[aria-label="Send"]').first
#                 await send_btn.click()
#                 logger.info("Media sent successfully.")
#             else:
#                 msg_box = await find_message_box(page)
#                 await msg_box.click()
#                 await msg_box.fill(message)
#                 await page.keyboard.press("Enter")
#                 logger.info("Text message sent successfully.")
#
#             await page.wait_for_timeout(3000)
#             await context.close()
#             return True
#
#         except Exception as e:
#             logger.error(f"Error during WhatsApp message send: {e}")
#             await context.close()
#             return False

async def send_whatsapp_message(contact_name, message, attachment_path=None, profile_key='main'):
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

async def create_whatsapp_group(group_name: str, contacts: List[str], message: str, attachment_path: Optional[str] = None, profile_key: str = "main") -> bool:
    """Create a new WhatsApp group, add contacts, and send an optional text/image."""
    logger.info(f"WhatsApp group automation: group='{group_name}', contacts={contacts}")
    
    async with async_playwright() as p:
        context = await get_browser_context(p, profile_key=profile_key)
        page = await context.new_page()
        
        try:
            logger.info("Opening WhatsApp Web...")
            await page.goto("https://web.whatsapp.com/")
            
            search_box_selector = 'div[contenteditable="true"]'
            await page.wait_for_selector(search_box_selector, timeout=60000)
            
            new_chat_btn = page.locator('span[data-icon="new-chat-outline"], span[data-icon="chat"], button[aria-label="New chat"], div[title="New chat"]').first
            await new_chat_btn.click()
            await page.wait_for_timeout(1500)
            
            new_group_opt = page.locator('div[role="button"]:has-text("New group"), span:has-text("New group"), [title="New group"]').first
            await new_group_opt.click()
            await page.wait_for_timeout(1500)
            
            for contact in contacts:
                logger.info(f"Adding contact to group: {contact}")
                contact_input = page.locator('input[placeholder="Type contact name"], div[contenteditable="true"]').first
                await contact_input.click()
                await contact_input.fill(contact)
                await page.wait_for_timeout(1500)
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(1000)
                
            next_btn = page.locator('span[data-icon="arrow-forward"], span[data-icon="checkmark-medium"], button:has(span[data-icon="arrow-forward"])').first
            await next_btn.click()
            await page.wait_for_timeout(1500)
            
            subject_input = page.locator('div[contenteditable="true"], input[type="text"]').first
            await subject_input.click()
            await subject_input.fill(group_name)
            await page.wait_for_timeout(1000)
            
            create_btn = page.locator('span[data-icon="checkmark-medium"], span[data-icon="checkmark"], button:has(span[data-icon="checkmark-medium"])').first
            await create_btn.click()
            logger.info("Waiting for group creation to finalize...")
            await page.wait_for_timeout(5000)
            
            if attachment_path and os.path.exists(attachment_path):
                logger.info(f"Uploading group file: {attachment_path}")
                file_input = page.locator('input[type="file"]').first
                await file_input.set_input_files(attachment_path)
                await page.wait_for_timeout(3000)
                
                caption_box = page.locator('div[contenteditable="true"]').nth(1)
                if await caption_box.count() > 0:
                    await caption_box.fill(message)
                    await page.wait_for_timeout(1000)
                
                send_btn = page.locator('span[data-icon="send"], div[aria-label="Send"], button[aria-label="Send"]').first
                await send_btn.click()
            else:
                msg_box = await find_message_box(page)
                await msg_box.click()
                await msg_box.fill(message)
                await page.keyboard.press("Enter")
                
            logger.info("WhatsApp Group created and message sent successfully.")
            await page.wait_for_timeout(3000)
            await context.close()
            return True
            
        except Exception as e:
            logger.error(f"Error creating WhatsApp group: {e}")
            await context.close()
            return False

async def create_instagram_account(profile_key: str = "main") -> bool:
    """Launch headful Chrome to Instagram signup page and wait for manual user interaction."""
    logger.info("Instagram signup automation launched.")
    
    async with async_playwright() as p:
        context = await get_browser_context(p, profile_key=profile_key)
        page = await context.new_page()
        
        try:
            logger.info("Navigating to Instagram Signup...")
            await page.goto("https://www.instagram.com/accounts/emailsignup/")
            
            logger.info("Chrome is open. Please complete the registration manually on the screen.")
            for _ in range(300):
                if page.is_closed():
                    break
                await asyncio.sleep(1)
                
            await context.close()
            return True
        except Exception as e:
            logger.error(f"Error during Instagram signup launch: {e}")
            await context.close()
            return False
