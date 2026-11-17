import asyncio
import time
import logging
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright, Browser, Page, Playwright
from config import MULTILOGIN_SIGNUP_URL, HEADLESS, BROWSER_TIMEOUT_MS, SESSION_EXPIRY_SECONDS
from tempmail import generate_random_email, wait_for_multilogin_otp

logger = logging.getLogger(__name__)

# Active registration sessions indexed by user_id
active_sessions: Dict[int, Dict[str, Any]] = {}
playwright_instance: Optional[Playwright] = None

async def get_playwright():
    global playwright_instance
    if playwright_instance is None:
        playwright_instance = await async_playwright().start()
    return playwright_instance

async def close_session(user_id: int):
    session = active_sessions.pop(user_id, None)
    if session:
        try:
            if "browser" in session and session["browser"]:
                await session["browser"].close()
        except Exception as e:
            logger.warning(f"Error closing browser for user {user_id}: {e}")

async def start_registration(user_id: int, email: str, password: str) -> Dict[str, Any]:
    """
    Step 1: Navigate to MultiLogin signup, fill email, password, accept terms, click Continue.
    Waits for Verify Email OTP screen.
    """
    # Close any existing session for this user first
    await close_session(user_id)
    
    pw = await get_playwright()
    browser: Optional[Browser] = None
    try:
        browser = await pw.chromium.launch(
            headless=HEADLESS,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-extensions",
            ]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        )
        page: Page = await context.new_page()
        page.set_default_timeout(BROWSER_TIMEOUT_MS)
        
        # Navigate to registration page
        await page.goto(MULTILOGIN_SIGNUP_URL, wait_until="networkidle")
        
        # Fill email
        await page.fill('input[type="email"]', email)
        
        # Fill passwords
        pw_inputs = await page.query_selector_all('input[type="password"]')
        if len(pw_inputs) < 2:
            await browser.close()
            return {"success": False, "error": "Could not find password fields on signup page."}
        
        await pw_inputs[0].fill(password)
        await pw_inputs[1].fill(password)
        
        # Check Terms of Service checkbox
        cb = await page.query_selector('input[type="checkbox"]')
        if cb:
            await cb.check(force=True)
            
        await asyncio.sleep(0.5)
        
        # Click Continue / Submit button
        submit_btn = await page.query_selector('button[type="submit"]')
        if not submit_btn:
            submit_btn = await page.query_selector("button:has-text('Continue')")
            
        if not submit_btn:
            await browser.close()
            return {"success": False, "error": "Submit button not found."}
            
        await submit_btn.click()
        
        # Poll for Verify Email screen or Error message
        start_wait = time.time()
        while time.time() - start_wait < 20:
            await asyncio.sleep(0.8)
            body_text = await page.inner_text("body")
            
            if "An account with this email already exists" in body_text:
                await browser.close()
                return {"success": False, "error": "An account with this email already exists on MultiLogin!"}
                
            if "Verify Email" in body_text or "Enter the 6-digit code" in body_text:
                # Check for OTP inputs
                otp_inputs = await page.query_selector_all('input[data-otp-input="true"]')
                if len(otp_inputs) >= 6:
                    # Save active session
                    active_sessions[user_id] = {
                        "browser": browser,
                        "context": context,
                        "page": page,
                        "email": email,
                        "password": password,
                        "created_at": time.time()
                    }
                    return {"success": True, "state": "otp_required"}
                    
            # Check for generic errors on page
            error_el = await page.query_selector(".mat-mdc-form-field-error, .error-message, mat-error")
            if error_el:
                err_txt = (await error_el.inner_text()).strip()
                if err_txt:
                    await browser.close()
                    return {"success": False, "error": err_txt}

        # If timed out waiting
        await browser.close()
        return {"success": False, "error": "Timed out waiting for verification code page."}

    except Exception as e:
        logger.exception(f"Exception during registration for user {user_id}: {e}")
        if browser:
            try:
                await browser.close()
            except Exception:
                pass
        return {"success": False, "error": str(e)}

async def submit_otp(user_id: int, otp_code: str) -> Dict[str, Any]:
    """
    Step 2: Enter the 6-digit OTP code into the active session.
    """
    session = active_sessions.get(user_id)
    if not session:
        return {"success": False, "error": "Registration session expired or not found. Please click 'Acc Create' again."}
        
    page: Page = session["page"]
    email: str = session["email"]
    password: str = session["password"]
    
    clean_code = otp_code.strip().replace(" ", "").replace("-", "")
    if len(clean_code) != 6 or not clean_code.isdigit():
        return {"success": False, "error": "Invalid code format! Please enter exactly 6 numeric digits."}
        
    try:
        otp_inputs = await page.query_selector_all('input[data-otp-input="true"]')
        if len(otp_inputs) < 6:
            # Try finding any numeric text inputs on verify page
            otp_inputs = await page.query_selector_all('.code-verification__otp-input')
            
        if len(otp_inputs) < 6:
            await close_session(user_id)
            return {"success": False, "error": "Verification input boxes not found on page. Session reset."}
            
        # Fill each digit
        for i, digit in enumerate(clean_code):
            await otp_inputs[i].fill(digit)
            await asyncio.sleep(0.08)
            
        # Wait for submission and redirection
        start_wait = time.time()
        while time.time() - start_wait < 15:
            await asyncio.sleep(1.0)
            cur_url = page.url
            body_text = await page.inner_text("body")
            
            # Check for error message
            if "Invalid code" in body_text or "Incorrect code" in body_text or "Code is not valid" in body_text:
                return {"success": False, "error": "Invalid verification code entered! Please check your email and try again."}
                
            if "expired" in body_text.lower():
                await close_session(user_id)
                return {"success": False, "error": "Verification code has expired. Please restart registration."}
                
            # Check for success indicators:
            # 1. URL navigated away from /new-account to workspace, app, onboarding, etc.
            # 2. Or "Welcome" / "Select plan" / "Download" on page
            if "/auth/new-account" not in cur_url or "workspace" in cur_url or "onboarding" in cur_url or "Welcome" in body_text or "Download app" in body_text:
                # Registration completed successfully!
                await close_session(user_id)
                return {
                    "success": True,
                    "email": email,
                    "password": password
                }
                
        # If still on verify page without explicit error, check if success anyway
        if "/auth/new-account" not in page.url:
            await close_session(user_id)
            return {
                "success": True,
                "email": email,
                "password": password
            }
            
        return {"success": False, "error": "Verification did not complete. Please re-check code or try again."}

    except Exception as e:
        logger.exception(f"Error submitting OTP for user {user_id}: {e}")
        return {"success": False, "error": str(e)}

async def auto_create_account(user_id: int, password: str, step_callback=None) -> Dict[str, Any]:
    """
    1-Click Full Auto Account Creation using Müllfach.de:
    1. Generates guaranteed unique email
    2. Starts registration on MultiLogin
    3. Auto-polls Müllfach.de for OTP
    4. Auto-submits OTP and finalizes registration
    """
    email = generate_random_email()
    if step_callback:
        await step_callback("step_email", email, None)
        
    reg_res = await start_registration(user_id, email, password)
    if not reg_res["success"]:
        return reg_res
        
    if step_callback:
        await step_callback("step_waiting_otp", email, None)
        
    otp = await wait_for_multilogin_otp(email, timeout_sec=50, poll_interval=2)
    if not otp:
        await close_session(user_id)
        return {"success": False, "error": "Did not receive verification code from Müllfach in time. Please try again."}
        
    if step_callback:
        await step_callback("step_code_received", email, otp)
        
    sub_res = await submit_otp(user_id, otp)
    return sub_res

async def cleanup_expired_sessions():
    """Background task to reap sessions older than SESSION_EXPIRY_SECONDS"""
    now = time.time()
    expired_user_ids = [
        uid for uid, s in active_sessions.items()
        if now - s.get("created_at", 0) > SESSION_EXPIRY_SECONDS
    ]
    for uid in expired_user_ids:
        await close_session(uid)
