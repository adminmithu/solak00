"""
HTML Template Cards for Telegram Bot with Premium Aesthetic Styling
"""

def pending_access_card(user_id: int, first_name: str, username: str = None) -> str:
    user_tag = f"@{username}" if username else "None"
    return (
        "╔══════════════════════════════════╗\n"
        "║     🔒 <b>ACCESS RESTRICTED</b> 🔒       ║\n"
        "╚══════════════════════════════════╝\n\n"
        f"👋 <b>Welcome, {first_name}!</b>\n\n"
        "⏳ <b>Status:</b> <code>PENDING APPROVAL</code>\n"
        "⚠️ <i>Your account is currently awaiting verification from the system Administrator.</i>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Name:</b> {first_name}\n"
        f"🏷️ <b>Username:</b> {user_tag}\n"
        f"🆔 <b>Your ID:</b> <code>{user_id}</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔔 <i>An administrator has been notified. You will automatically receive full access once approved!</i>"
    )

def admin_approval_request_card(user_id: int, first_name: str, username: str = None, timestamp: str = "") -> str:
    user_tag = f"@{username}" if username else "None"
    return (
        "╔══════════════════════════════════╗\n"
        "║   🔔 <b>NEW ACCESS REQUEST</b> 🔔      ║\n"
        "╚══════════════════════════════════╝\n\n"
        "A new user is requesting bot access:\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Name:</b> {first_name}\n"
        f"🏷️ <b>Username:</b> {user_tag}\n"
        f"🆔 <b>User ID:</b> <code>{user_id}</code>\n"
        f"⏰ <b>Requested At:</b> {timestamp}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "👇 <b>Select an action below:</b>"
    )

def welcome_approved_card(first_name: str) -> str:
    return (
        "╔══════════════════════════════════╗\n"
        "║   ✨ <b>ACCESS GRANTED</b> ✨          ║\n"
        "╚══════════════════════════════════╝\n\n"
        f"🎉 <b>Welcome, {first_name}!</b>\n"
        "Your account has been <b>approved</b> by the Administrator.\n\n"
        "⚡ <b>Available Actions:</b>\n"
        "• <b>🚀 Acc Create:</b> 1-Click MultiLogin account creation with automatic OTP.\n"
        "• <b>🔐 Pass Set:</b> Configure permanent or one-time custom passwords.\n"
        "• <b>📜 History:</b> View all previously created accounts (permanent storage).\n"
        "• <b>📊 MultiLogin Details:</b> Antidetect system specs & your creation stats.\n"
        "• <b>💬 Support:</b> Direct communication channel with Admin.\n\n"
        "<i>Use the menu keyboard below to get started!</i>"
    )

def user_blocked_card(user_id: int) -> str:
    return (
        "╔══════════════════════════════════╗\n"
        "║     🚫 <b>ACCESS BLOCKED</b> 🚫         ║\n"
        "╚══════════════════════════════════╝\n\n"
        "⛔ <b>Your account has been BLOCKED.</b>\n\n"
        "<i>You are not authorized to use this bot. All features have been revoked by the Administrator.</i>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 <b>Your ID:</b> <code>{user_id}</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💬 <i>If you believe this is a mistake, please contact the administrator directly.</i>"
    )

def create_method_choice_card(has_saved_pass: bool = False, saved_pass_masked: str = "") -> str:
    pass_info = (
        f"🔑 <b>Saved Password:</b> <code>{saved_pass_masked}</code>\n"
        if has_saved_pass
        else "🔑 <b>Password Mode:</b> <i>Will prompt for password</i>\n"
    )
    return (
        "╔══════════════════════════════════╗\n"
        "║     🚀 <b>CREATE MULTILOGIN ACC</b>     ║\n"
        "╚══════════════════════════════════╝\n\n"
        f"{pass_info}"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>Select Account Creation Method:</b>\n\n"
        "⚡ <b>Auto Create (1-Click Temp Mail):</b>\n"
        "• <i>Generates guaranteed unique @muellfach.de email</i>\n"
        "• <i>Submits credentials & monitors OTP live</i>\n"
        "• <i>Auto-submits 6-digit code & finishes in seconds!</i>\n\n"
        "✍️ <b>Custom Email (Manual OTP):</b>\n"
        "• <i>Use your personal Gmail/Yahoo/Outlook email</i>\n"
        "• <i>Manually enter 6-digit verification code</i>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "👇 <i>Choose your preferred method below:</i>"
    )

def auto_step_email_card(email: str) -> str:
    return (
        "╔══════════════════════════════════╗\n"
        "║    ⚡ <b>AUTO-CREATION: STEP 1/3</b>   ║\n"
        "╚══════════════════════════════════╝\n\n"
        "✨ <b>Unique Temp Mail Generated!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📧 <b>Email:</b> <code>{email}</code>\n"
        "🌐 <b>Domain:</b> <code>Müllfach.de (Private Inbox)</code>\n"
        "⏳ <b>Status:</b> <i>Submitting to MultiLogin portal...</i>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🚀 <i>Connecting to registration server, please wait...</i>"
    )

def auto_step_waiting_otp_card(email: str) -> str:
    return (
        "╔══════════════════════════════════╗\n"
        "║    ⚡ <b>AUTO-CREATION: STEP 2/3</b>   ║\n"
        "╚══════════════════════════════════╝\n\n"
        "📬 <b>MultiLogin Registration Submitted!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📧 <b>Target:</b> <code>{email}</code>\n"
        "🔍 <b>Listener:</b> <code>Live Müllfach.de Monitor</code>\n"
        "⏳ <b>Status:</b> <i>Awaiting 6-digit verification code...</i>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ <i>Polling inbox in real-time (~5-15s)...</i>"
    )

def auto_step_code_received_card(email: str, code: str) -> str:
    return (
        "╔══════════════════════════════════╗\n"
        "║    ⚡ <b>AUTO-CREATION: STEP 3/3</b>   ║\n"
        "╚══════════════════════════════════╝\n\n"
        "🎉 <b>Verification Code Received!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📧 <b>Email:</b> <code>{email}</code>\n"
        f"🔢 <b>OTP Code:</b> <code>{code}</code> ✅\n"
        "⚙️ <b>Status:</b> <i>Submitting OTP & finalizing account...</i>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "✨ <i>Activating account profile on MultiLogin...</i>"
    )

def ask_email_card(has_saved_pass: bool = False, saved_pass_masked: str = "") -> str:
    pass_info = (
        f"🔑 <b>Auto-Password Active:</b> <code>{saved_pass_masked}</code>\n"
        if has_saved_pass
        else "🔑 <b>Password Mode:</b> <i>Will prompt in next step</i>\n"
    )
    return (
        "╔══════════════════════════════════╗\n"
        "║     🚀 <b>CREATE MULTILOGIN ACC</b>     ║\n"
        "╚══════════════════════════════════╝\n\n"
        f"{pass_info}"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📧 <b>Step 1/2: Provide Target Email</b>\n\n"
        "Please send the <b>Email Address</b> you want to register for this MultiLogin account:\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "💡 <i>Example: john.doe@gmail.com</i>\n"
        "<i>Or send /cancel to abort.</i>"
    )

def ask_password_card(email: str) -> str:
    return (
        "╔══════════════════════════════════╗\n"
        "║       🔐 <b>SET ACCOUNT PASS</b>       ║\n"
        "╚══════════════════════════════════╝\n\n"
        f"📧 <b>Target Email:</b> <code>{email}</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔑 <b>Step 2/3: Account Password</b>\n\n"
        "Please type the <b>Password</b> for this MultiLogin account:\n\n"
        "📌 <b>Requirements:</b>\n"
        "• At least 8 characters\n"
        "• At least 1 uppercase letter (A-Z)\n"
        "• At least 1 lowercase letter (a-z)\n"
        "• At least 1 number (0-9)\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "💡 <i>Tip: You can also save a permanent password in 'Pass Set' to skip this step.</i>"
    )

def ask_otp_card(email: str) -> str:
    return (
        "╔══════════════════════════════════╗\n"
        "║     📩 <b>VERIFICATION CODE</b> 📩     ║\n"
        "╚══════════════════════════════════╝\n\n"
        f"📬 <b>OTP Sent to:</b> <code>{email}</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔢 <b>Final Step: Email Verification</b>\n\n"
        "MultiLogin has dispatched a <b>6-digit verification code</b> to your inbox.\n\n"
        "👉 <b>Please enter the 6 digits below:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "⏳ <i>Session remains active for 5 minutes. Check spam folder if not received.</i>"
    )

def account_success_card(email: str, password: str, date_str: str) -> str:
    return (
        "╔══════════════════════════════════╗\n"
        "║  ✨ <b>MULTILOGIN ACC CREATED</b> ✨   ║\n"
        "╚══════════════════════════════════╝\n\n"
        "🎉 <b>Account has been successfully registered & verified!</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📧 <b>Email:</b> <code>{email}</code>\n"
        f"🔑 <b>Password:</b> <code>{password}</code>\n"
        "🌐 <b>Status:</b> <code>VERIFIED & ACTIVE ✅</code>\n"
        f"📅 <b>Created On:</b> {date_str}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🚀 <b>Login URL:</b> <a href=\"https://app.multilogin.com\">https://app.multilogin.com</a>\n"
        "💡 <i>Credentials have been saved to your account history.</i>"
    )

def pass_settings_card(current_pass: str = None, mode: str = "ask_each_time") -> str:
    masked = f"<code>{current_pass}</code>" if current_pass else "<i>None (Not Set)</i>"
    mode_text = "🔒 <b>Permanent (All-Time)</b>" if mode == "permanent" else "⏱️ <b>Ask Each Time (1-Time)</b>"
    
    return (
        "╔══════════════════════════════════╗\n"
        "║       🔐 <b>PASSWORD MANAGER</b>      ║\n"
        "╚══════════════════════════════════╝\n\n"
        "Configure your default password preference for automatic MultiLogin registrations:\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔑 <b>Current Password:</b> {masked}\n"
        f"⚙️ <b>Storage Mode:</b> {mode_text}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "• <b>Permanent (All-Time):</b> Auto-uses this password for every new account without asking.\n"
        "• <b>Ask Each Time:</b> Disables saved password and prompts you every time you create an account.\n\n"
        "👇 <i>Choose an action below:</i>"
    )

def multilogin_details_card(user_acc_count: int, total_system_acc: int) -> str:
    return (
        "╔══════════════════════════════════╗\n"
        "║      🌐 <b>MULTILOGIN SYSTEM</b>      ║\n"
        "╚══════════════════════════════════╝\n\n"
        "MultiLogin is the world's leading antidetect browser software designed for multi-account management without detection or bans.\n\n"
        "🛡️ <b>Key Capabilities:</b>\n"
        "• <b>Mimic Browser:</b> Chromium-based with unique Canvas/Audio/WebGL spoofing.\n"
        "• <b>Stealthfox:</b> Firefox engine with customized browser fingerprinting.\n"
        "• <b>Proxy Integration:</b> HTTP, HTTPS, SOCKS4, SOCKS5 support.\n"
        "• <b>Cookie Management:</b> Automated import/export of sessions.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>Accounts Created By You:</b> <code>{user_acc_count}</code>\n"
        f"🌐 <b>Total Network Accounts:</b> <code>{total_system_acc}</code>\n"
        "🟢 <b>API System Status:</b> <code>100% Operational</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔗 <b>Official Portal:</b> <a href=\"https://multilogin.com\">multilogin.com</a>"
    )

def support_prompt_card() -> str:
    return (
        "╔══════════════════════════════════╗\n"
        "║       💬 <b>SUPPORT DESK</b>         ║\n"
        "╚══════════════════════════════════╝\n\n"
        "Need help, custom limits, or want to report an issue?\n\n"
        "📝 <b>Please type your message below.</b>\n"
        "<i>Your message will be delivered directly to the Administrator's panel.</i>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 <i>Send /cancel to return to main menu.</i>"
    )

def admin_panel_card(stats: dict) -> str:
    return (
        "╔══════════════════════════════════╗\n"
        "║     👑 <b>ADMIN CONTROL PANEL</b>    ║\n"
        "╚══════════════════════════════════╝\n\n"
        "Welcome to the Central Administration Panel.\n\n"
        "📊 <b>System Overview:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 <b>Total Users:</b> <code>{stats.get('total_users', 0)}</code>\n"
        f"✅ <b>Approved Users:</b> <code>{stats.get('approved_users', 0)}</code>\n"
        f"⏳ <b>Pending Approvals:</b> <code>{stats.get('pending_users', 0)}</code>\n"
        f"🚀 <b>Total Accounts Created:</b> <code>{stats.get('total_accounts', 0)}</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "👇 <i>Select an administrative function:</i>"
    )

def history_empty_card() -> str:
    return (
        "╔══════════════════════════════════╗\n"
        "║     📜 <b>ACCOUNT CREATION HISTORY</b>    ║\n"
        "╚══════════════════════════════════╝\n\n"
        "ℹ️ <b>No accounts found in your history yet!</b>\n\n"
        "Click <b>🚀 Acc Create</b> to generate your first MultiLogin account.\n"
        "<i>All accounts created by you will be permanently stored here.</i>"
    )

def history_card(accounts: list, page: int, total_pages: int, total_count: int) -> str:
    header = (
        "╔══════════════════════════════════╗\n"
        "║     📜 <b>ACCOUNT CREATION HISTORY</b>    ║\n"
        "╚══════════════════════════════════╝\n\n"
        f"📊 <b>Total Accounts Created:</b> <code>{total_count}</code>\n"
        f"📄 <b>Page:</b> <code>{page} of {total_pages}</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    )
    lines = [header]
    start_num = (page - 1) * 5 + 1
    for i, acc in enumerate(accounts, start=start_num):
        email = acc.get("email", "")
        pw = acc.get("password", "")
        dt = acc.get("created_at", "")
        lines.append(
            f"<b>{i}.</b> 📧 <code>{email}</code>\n"
            f"   🔑 <code>{pw}</code>\n"
            f"   📅 <i>{dt}</i>\n"
        )
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    lines.append("💡 <i>Credentials remain permanently saved in local database.</i>")
    return "\n".join(lines)
