import asyncio
import re
import secrets
import random
import time
import logging
from typing import Optional
import httpx
from database import is_email_used, mark_email_used

logger = logging.getLogger(__name__)

MUELLFACH_API = "https://www.muellfach.de/api.php"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"

def generate_random_email() -> str:
    """
    Generates a guaranteed unique temporary email address using muellfach.de.
    Checks SQLite database to ensure the email was never used before.
    """
    for _ in range(50):
        # Unique timestamp + random hex + random salt
        ts = int(time.time())
        rand_salt = secrets.token_hex(3)
        rand_digits = random.randint(100, 999)
        email = f"ml_{ts}_{rand_salt}{rand_digits}@muellfach.de"
        
        if not is_email_used(email):
            mark_email_used(email)
            return email
            
    # Fallback with uuid
    fallback = f"ml_{secrets.token_hex(8)}@muellfach.de"
    mark_email_used(fallback)
    return fallback

async def wait_for_multilogin_otp(email: str, timeout_sec: int = 60, poll_interval: int = 2) -> Optional[str]:
    """
    Polls Müllfach.de API until MultiLogin verification email arrives,
    then parses and returns the 6-digit OTP.
    """
    local_part = email.split('@')[0]
    headers = {
        "User-Agent": USER_AGENT,
        "Referer": f"https://www.muellfach.de/postfach/muellfach.de/{local_part}"
    }
    
    start_time = asyncio.get_event_loop().time()
    seen_ids = set()
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        while asyncio.get_event_loop().time() - start_time < timeout_sec:
            try:
                res = await client.get(
                    MUELLFACH_API,
                    params={"action": "mails", "address": email},
                    headers=headers
                )
                if res.status_code == 200:
                    data = res.json()
                    mails = data.get("mails", [])
                    for mail in mails:
                        mail_id = mail.get("id")
                        if mail_id in seen_ids:
                            continue
                        seen_ids.add(mail_id)
                        
                        subject = mail.get("subject", "").lower()
                        sender = mail.get("sender_email", "").lower()
                        
                        if "multilogin" in sender or "verification" in subject or "code" in subject:
                            # Fetch email body to get code
                            mail_res = await client.get(
                                MUELLFACH_API,
                                params={"action": "mail", "id": mail_id, "address": email},
                                headers=headers
                            )
                            if mail_res.status_code == 200:
                                mail_data = mail_res.json()
                                mail_obj = mail_data.get("mail", {})
                                body = mail_obj.get("body_html") or mail_obj.get("body_text") or ""
                                match = re.search(r'\b\d{6}\b', body)
                                if match:
                                    code = match.group(0)
                                    logger.info(f"Successfully extracted MultiLogin OTP: {code} for {email}")
                                    return code
            except Exception as e:
                logger.warning(f"Error polling Müllfach API for {email}: {e}")
                
            await asyncio.sleep(poll_interval)
            
    logger.warning(f"Timeout waiting for MultiLogin OTP on {email}")
    return None
