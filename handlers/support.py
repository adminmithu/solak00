from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from config import ADMIN_ID, BTN_CANCEL
from database import save_support_ticket, get_support_ticket, reply_support_ticket, is_user_approved
from keyboards import get_main_keyboard, get_cancel_keyboard, get_support_reply_inline, remove_keyboard
from templates import support_prompt_card

STATE_SUPPORT_MSG = 1
STATE_ADMIN_REPLY = 2

async def support_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry when user clicks '💬 Support'"""
    user = update.effective_user
    if not user:
        return ConversationHandler.END
        
    await update.message.reply_html(
        support_prompt_card(),
        reply_markup=get_cancel_keyboard()
    )
    return STATE_SUPPORT_MSG

async def support_msg_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User delivers support message"""
    user = update.effective_user
    text = update.message.text.strip()
    is_admin = (user.id == ADMIN_ID)
    is_approved = is_user_approved(user.id)
    user_markup = get_main_keyboard(is_admin) if is_approved else remove_keyboard()
    
    if text == BTN_CANCEL or "cancel" in text.lower():
        await update.message.reply_text("❌ Support cancelled.", reply_markup=user_markup)
        return ConversationHandler.END
        
    ticket_id = save_support_ticket(user.id, text)
    
    # Notify user
    await update.message.reply_html(
        "╔══════════════════════════════════╗\n"
        "║     ✅ <b>SUPPORT TICKET SENT</b>     ║\n"
        "╚══════════════════════════════════╝\n\n"
        f"🎫 <b>Ticket ID:</b> <code>#{ticket_id}</code>\n"
        "Your message has been delivered directly to the Administrator.\n"
        "<i>You will receive a notification as soon as the Admin replies!</i>",
        reply_markup=user_markup
    )
    
    # Forward to Admin
    if ADMIN_ID != 0:
        try:
            admin_card = (
                "╔══════════════════════════════════╗\n"
                "║    💬 <b>NEW SUPPORT INQUIRY</b>     ║\n"
                "╚══════════════════════════════════╝\n\n"
                f"👤 <b>From:</b> {user.first_name} (@{user.username or 'NoUser'})\n"
                f"🆔 <b>User ID:</b> <code>{user.id}</code>\n"
                f"🎫 <b>Ticket:</b> <code>#{ticket_id}</code>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💬 <b>Message:</b>\n{text}\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            )
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=admin_card,
                parse_mode="HTML",
                reply_markup=get_support_reply_inline(user.id, ticket_id)
            )
        except Exception:
            pass
            
    return ConversationHandler.END

async def admin_reply_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin clicks '✍️ Reply to User' inline button"""
    query = update.callback_query
    await query.answer()
    
    # Callback format: adm_reply_{ticket_id}_{user_id}
    parts = query.data.split("_")
    ticket_id = int(parts[2])
    target_user_id = int(parts[3])
    
    context.user_data["reply_ticket_id"] = ticket_id
    context.user_data["reply_target_user_id"] = target_user_id
    
    await query.message.reply_html(
        f"✍️ <b>Replying to User <code>{target_user_id}</code> (Ticket #{ticket_id})</b>:\n\n"
        "Please type your response message below (or send /cancel):",
        reply_markup=get_cancel_keyboard()
    )
    return STATE_ADMIN_REPLY

async def admin_reply_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin sends reply text, forward to user"""
    admin_text = update.message.text.strip()
    if admin_text == BTN_CANCEL or admin_text.lower() == "/cancel":
        await update.message.reply_text("❌ Reply cancelled.", reply_markup=get_main_keyboard(True))
        return ConversationHandler.END
        
    ticket_id = context.user_data.get("reply_ticket_id")
    target_user_id = context.user_data.get("reply_target_user_id")
    
    if ticket_id and target_user_id:
        reply_support_ticket(ticket_id, admin_text)
        
        # Send reply to user
        try:
            user_msg = (
                "╔══════════════════════════════════╗\n"
                "║   📨 <b>SUPPORT DESK REPLY</b>       ║\n"
                "╚══════════════════════════════════╝\n\n"
                f"🎫 <i>Reference: Ticket #{ticket_id}</i>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💬 <b>Admin Response:</b>\n{admin_text}\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "<i>If you need further help, feel free to submit another ticket!</i>"
            )
            await context.bot.send_message(
                chat_id=target_user_id,
                text=user_msg,
                parse_mode="HTML"
            )
            await update.message.reply_html(
                f"✅ <b>Reply successfully sent to user <code>{target_user_id}</code>!</b>",
                reply_markup=get_main_keyboard(True)
            )
        except Exception as e:
            await update.message.reply_html(
                f"⚠️ <b>Failed to deliver message to user:</b> {e}",
                reply_markup=get_main_keyboard(True)
            )
            
    context.user_data.pop("reply_ticket_id", None)
    context.user_data.pop("reply_target_user_id", None)
    return ConversationHandler.END
