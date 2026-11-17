import io
import math
import datetime
from telegram import Update
from telegram.ext import ContextTypes
from database import get_user_accounts_count, get_user_accounts, get_user_all_accounts, is_user_approved
from keyboards import get_history_inline, remove_keyboard
from templates import history_card, history_empty_card, pending_access_card

PAGE_SIZE = 5

async def history_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry when user clicks '📜 History' from the main menu"""
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
    total_count = get_user_accounts_count(user_id)
    
    if total_count == 0:
        await update.message.reply_html(history_empty_card())
        return
        
    total_pages = max(1, math.ceil(total_count / PAGE_SIZE))
    accounts = get_user_accounts(user_id, limit=PAGE_SIZE, offset=0)
    
    await update.message.reply_html(
        history_card(accounts, page=1, total_pages=total_pages, total_count=total_count),
        reply_markup=get_history_inline(page=1, total_pages=total_pages)
    )

async def history_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles pagination and download buttons on history cards"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == "hist_close":
        try:
            await query.message.delete()
        except Exception:
            pass
        return
        
    elif data == "hist_noop":
        return
        
    elif data.startswith("hist_page_"):
        page = int(data.replace("hist_page_", ""))
        total_count = get_user_accounts_count(user_id)
        total_pages = max(1, math.ceil(total_count / PAGE_SIZE))
        offset = (page - 1) * PAGE_SIZE
        accounts = get_user_accounts(user_id, limit=PAGE_SIZE, offset=offset)
        
        await query.edit_message_text(
            history_card(accounts, page=page, total_pages=total_pages, total_count=total_count),
            parse_mode="HTML",
            reply_markup=get_history_inline(page=page, total_pages=total_pages)
        )
        return
        
    elif data == "hist_download":
        all_accs = get_user_all_accounts(user_id)
        if not all_accs:
            await query.answer("No accounts to export.", show_alert=True)
            return
            
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        content = "=== MY MULTILOGIN ACCOUNTS HISTORY ===\n"
        content += f"Exported At: {now_str}\n"
        content += f"Total Accounts: {len(all_accs)}\n"
        content += "=" * 45 + "\n\n"
        
        for i, a in enumerate(all_accs, start=1):
            content += f"[{i}]\n"
            content += f"Email    : {a.get('email')}\n"
            content += f"Password : {a.get('password')}\n"
            content += f"Date     : {a.get('created_at')}\n"
            content += "-" * 35 + "\n"
            
        file_obj = io.BytesIO(content.encode("utf-8"))
        file_obj.name = f"my_multilogin_accounts_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        await context.bot.send_document(
            chat_id=user_id,
            document=file_obj,
            caption=f"📁 <b>Your MultiLogin Accounts Export</b> ({len(all_accs)} accounts)",
            parse_mode="HTML"
        )
        return
