import asyncio
import logging
import sys
import os
import re
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler, 
    ConversationHandler, filters
)

from config import (
    BOT_TOKEN, ADMIN_ID, BTN_ACC_CREATE, BTN_PASS_SET, BTN_HISTORY,
    BTN_MULTILOGIN_DETAILS, BTN_SUPPORT, BTN_ADMIN_PANEL, BTN_CANCEL
)
from database import init_db
from multilogin import cleanup_expired_sessions

# Handlers
from handlers.start import start_handler
from handlers.acc_create import (
    acc_create_entry, method_choice_received, email_received, password_received, otp_received, 
    cancel_acc_create, STATE_METHOD_CHOICE, STATE_EMAIL, STATE_PASSWORD, STATE_OTP
)
from handlers.pass_set import (
    pass_set_menu, pass_callback_handler, pass_prompt_input, 
    pass_prompt_permanent, pass_prompt_temp,
    pass_input_received, STATE_NEW_PASS
)
from handlers.history import history_handler, history_callback_handler
from handlers.multilogin_info import multilogin_details_handler
from handlers.support import (
    support_entry, support_msg_received, admin_reply_prompt, 
    admin_reply_received, STATE_SUPPORT_MSG, STATE_ADMIN_REPLY
)
from handlers.admin import (
    admin_panel_entry, admin_callback_handler, broadcast_prompt, 
    broadcast_received, manual_approve_prompt, manual_approve_received,
    block_user_prompt, block_user_received,
    STATE_ADMIN_BROADCAST, STATE_ADMIN_MANUAL_APPROVE, STATE_ADMIN_BLOCK_USER
)

# Configure logging
logging.basicConfig(
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("MultiACCCreator")

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status": "online", "bot": "MultiACC Creator", "message": "Bot is alive and running!"}')

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        # Silence HTTP access logs to keep bot.log clean
        pass

def start_health_server_thread():
    """Starts a lightweight HTTP server on $PORT for Render health checks and keep-alive pings"""
    port_str = os.environ.get("PORT", "8080")
    try:
        port = int(port_str)
    except ValueError:
        port = 8080

    def _serve():
        try:
            server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
            logger.info(f"Health-check HTTP server listening on 0.0.0.0:{port}")
            server.serve_forever()
        except Exception as e:
            logger.warning(f"Health-check server could not start on port {port}: {e}")

    t = threading.Thread(target=_serve, daemon=True)
    t.start()

async def periodic_cleanup_task():
    """Background task to clean up old browser sessions every 60 seconds"""
    while True:
        try:
            await asyncio.sleep(60)
            await cleanup_expired_sessions()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.warning(f"Error in cleanup task: {e}")

def main():
    # Verify BOT_TOKEN
    if not BOT_TOKEN or "YOUR_TELEGRAM_BOT_TOKEN" in BOT_TOKEN:
        print("\n" + "=" * 60)
        print(" [!] ERROR: Telegram BOT_TOKEN is missing or not configured!")
        print(" Please open the .env file and set your BOT_TOKEN from @BotFather.")
        print(" Example:")
        print(" BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRstuVWXyz")
        print(" ADMIN_ID=123456789")
        print("=" * 60 + "\n")
        sys.exit(1)

    # Initialize SQLite database
    init_db()
    logger.info("Database initialized successfully.")

    # Build Telegram application
    app = Application.builder().token(BOT_TOKEN).build()

    # 1. Start & Admin commands
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("admin", admin_panel_entry))

    # 2. Account Creation Conversation Handler
    acc_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(f"^({re.escape(BTN_ACC_CREATE)}|.*Acc Create.*)$"), acc_create_entry)
        ],
        states={
            STATE_METHOD_CHOICE: [
                CallbackQueryHandler(method_choice_received, pattern="^create_method_")
            ],
            STATE_EMAIL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, email_received)
            ],
            STATE_PASSWORD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, password_received)
            ],
            STATE_OTP: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, otp_received)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_acc_create),
            MessageHandler(filters.Regex(f"^({re.escape(BTN_CANCEL)}|.*Cancel.*)$"), cancel_acc_create)
        ],
        per_user=True,
        per_chat=True,
        per_message=False
    )
    app.add_handler(acc_conv)

    # 3. Pass Setting Input Conversation Handler
    pass_input_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(pass_prompt_input, pattern="^pass_set_new$"),
            CallbackQueryHandler(pass_prompt_permanent, pattern="^pass_set_perm_direct$"),
            CallbackQueryHandler(pass_prompt_temp, pattern="^pass_set_temp_direct$"),
            CallbackQueryHandler(pass_prompt_permanent, pattern="^pass_mode_perm$")
        ],
        states={
            STATE_NEW_PASS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, pass_input_received)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_acc_create),
            MessageHandler(filters.Regex(f"^({re.escape(BTN_CANCEL)}|.*Cancel.*)$"), cancel_acc_create)
        ],
        per_user=True,
        per_chat=True,
        per_message=False
    )
    app.add_handler(pass_input_conv)

    # 4. Support Conversation Handler
    support_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(f"^({re.escape(BTN_SUPPORT)}|.*Support.*)$"), support_entry)
        ],
        states={
            STATE_SUPPORT_MSG: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, support_msg_received)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_acc_create),
            MessageHandler(filters.Regex(f"^({re.escape(BTN_CANCEL)}|.*Cancel.*)$"), cancel_acc_create)
        ],
        per_user=True,
        per_chat=True,
        per_message=False
    )
    app.add_handler(support_conv)

    # 5. Admin Reply to Support Conversation Handler
    admin_reply_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(admin_reply_prompt, pattern="^adm_reply_")
        ],
        states={
            STATE_ADMIN_REPLY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_reply_received)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_acc_create),
            MessageHandler(filters.Regex(f"^({re.escape(BTN_CANCEL)}|.*Cancel.*)$"), cancel_acc_create)
        ],
        per_user=True,
        per_chat=True,
        per_message=False
    )
    app.add_handler(admin_reply_conv)

    # 6. Admin Broadcast Conversation Handler
    admin_broadcast_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(broadcast_prompt, pattern="^adm_broadcast_prompt$")
        ],
        states={
            STATE_ADMIN_BROADCAST: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_received)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_acc_create),
            MessageHandler(filters.Regex(f"^({re.escape(BTN_CANCEL)}|.*Cancel.*)$"), cancel_acc_create)
        ],
        per_user=True,
        per_chat=True,
        per_message=False
    )
    app.add_handler(admin_broadcast_conv)

    # 7. Admin Manual Approve Conversation Handler
    admin_manual_app_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(manual_approve_prompt, pattern="^adm_manual_approve$")
        ],
        states={
            STATE_ADMIN_MANUAL_APPROVE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, manual_approve_received)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_acc_create),
            MessageHandler(filters.Regex(f"^({re.escape(BTN_CANCEL)}|.*Cancel.*)$"), cancel_acc_create)
        ],
        per_user=True,
        per_chat=True,
        per_message=False
    )
    app.add_handler(admin_manual_app_conv)

    # 8. Admin Block User Conversation Handler
    admin_block_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(block_user_prompt, pattern="^adm_block_user_prompt$")
        ],
        states={
            STATE_ADMIN_BLOCK_USER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, block_user_received)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_acc_create),
            MessageHandler(filters.Regex(f"^({re.escape(BTN_CANCEL)}|.*Cancel.*)$"), cancel_acc_create)
        ],
        per_user=True,
        per_chat=True,
        per_message=False
    )
    app.add_handler(admin_block_conv)

    # 9. Regular Menu Button Handlers
    app.add_handler(MessageHandler(filters.Regex(f"^({re.escape(BTN_PASS_SET)}|.*Pass Set.*)$"), pass_set_menu))
    app.add_handler(MessageHandler(filters.Regex(f"^({re.escape(BTN_HISTORY)}|.*History.*)$"), history_handler))
    app.add_handler(MessageHandler(filters.Regex(f"^({re.escape(BTN_MULTILOGIN_DETAILS)}|.*MultiLogin Details.*)$"), multilogin_details_handler))
    app.add_handler(MessageHandler(filters.Regex(f"^({re.escape(BTN_ADMIN_PANEL)}|.*Admin Panel.*)$"), admin_panel_entry))

    # 10. Callback Handlers
    app.add_handler(CallbackQueryHandler(pass_callback_handler, pattern="^pass_"))
    app.add_handler(CallbackQueryHandler(history_callback_handler, pattern="^hist_"))
    app.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^adm_"))

    print("\n" + "=" * 55)
    print(" [OK] MultiACC Creator Telegram Bot is starting...")
    print(f" [OK] Admin ID: {ADMIN_ID}")
    print("=" * 55 + "\n")

    # Start keep-alive health check server for Render / Uptime monitors
    start_health_server_thread()

    # Start background cleanup task
    async def post_init(application: Application):
        asyncio.create_task(periodic_cleanup_task())

    app.post_init = post_init
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
