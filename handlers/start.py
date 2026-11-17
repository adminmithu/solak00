import datetime
from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_ID
from database import register_or_get_user, get_user
from keyboards import get_main_keyboard, remove_keyboard, get_approval_inline
from templates import (
    pending_access_card, admin_approval_request_card, welcome_approved_card, user_blocked_card
)

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command, registers user, and performs permission checks"""
    user = update.effective_user
    if not user:
        return
        
    user_id = user.id
    username = user.username
    first_name = user.first_name or "User"
    
    # Register or get user profile from database
    db_user = register_or_get_user(user_id, username, first_name)
    is_admin = (user_id == ADMIN_ID)
    
    # Check if user is blocked
    if db_user.get("status") == "blocked" and not is_admin:
        await update.message.reply_html(
            user_blocked_card(user_id),
            reply_markup=remove_keyboard()
        )
        return

    # Check approval status
    if db_user["status"] != "approved" and not is_admin:
        # User is not approved yet -> show pending card and remove keyboard
        await update.message.reply_html(
            pending_access_card(user_id, first_name, username),
            reply_markup=remove_keyboard()
        )
        
        # Notify admin about new registration request
        if ADMIN_ID != 0:
            try:
                now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=admin_approval_request_card(user_id, first_name, username, now_str),
                    parse_mode="HTML",
                    reply_markup=get_approval_inline(user_id)
                )
            except Exception as e:
                # Admin chat might not be initiated yet or ID invalid
                pass
        return
        
    # User is approved -> show welcome message and full menu keyboard
    await update.message.reply_html(
        welcome_approved_card(first_name),
        reply_markup=get_main_keyboard(is_admin)
    )
