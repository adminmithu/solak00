from telegram import Update
from telegram.ext import ContextTypes
from database import get_user_accounts_count, get_stats, is_user_approved
from keyboards import remove_keyboard
from templates import multilogin_details_card, pending_access_card

async def multilogin_details_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays MultiLogin system info and personal usage statistics"""
    user = update.effective_user
    if not user:
        return
        
    user_id = user.id
    if not is_user_approved(user_id):
        await update.message.reply_html(
            pending_access_card(user_id, user.first_name, user.username),
            reply_markup=remove_keyboard()
        )
        return
    user_cnt = get_user_accounts_count(user_id)
    stats = get_stats()
    total_cnt = stats.get("total_accounts", 0)
    
    await update.message.reply_html(
        multilogin_details_card(user_cnt, total_cnt),
        disable_web_page_preview=True
    )
