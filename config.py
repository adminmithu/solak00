import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID_RAW = os.getenv("ADMIN_ID", "0").strip()

try:
    ADMIN_ID = int(ADMIN_ID_RAW)
except ValueError:
    ADMIN_ID = 0

# MultiLogin target URLs
MULTILOGIN_SIGNUP_URL = "https://app.multilogin.com/en/auth/new-account"

# UI Button Text Constants
BTN_ACC_CREATE = "🚀 Acc Create"
BTN_PASS_SET = "🔐 Pass Set"
BTN_HISTORY = "📜 History"
BTN_MULTILOGIN_DETAILS = "📊 MultiLogin Details"
BTN_SUPPORT = "💬 Support"
BTN_ADMIN_PANEL = "👑 Admin Panel"
BTN_CANCEL = "❌ Cancel"

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")

# Playwright Configuration
HEADLESS = True
BROWSER_TIMEOUT_MS = 45000
SESSION_EXPIRY_SECONDS = 300  # 5 minutes for OTP submission
