from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from database import get_user, set_user_password, clear_user_password, is_user_approved
from keyboards import get_pass_settings_inline, get_pass_scope_inline, get_main_keyboard, get_cancel_keyboard, remove_keyboard
from templates import pass_settings_card, pending_access_card
from config import ADMIN_ID, BTN_CANCEL

# Conversation state for entering new password
STATE_NEW_PASS = 1

async def pass_set_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry when user clicks '🔐 Pass Set' from reply keyboard"""
    user = update.effective_user
    if not user:
        return
        
    if not is_user_approved(user.id):
        await update.message.reply_html(
            pending_access_card(user.id, user.first_name, user.username),
            reply_markup=remove_keyboard()
        )
        return
        
    db_user = get_user(user.id)
    if not db_user:
        return
        
    cur_pass = db_user.get("default_pass")
    cur_mode = db_user.get("pass_mode", "ask_each_time")
    
    await update.message.reply_html(
        pass_settings_card(cur_pass, cur_mode),
        reply_markup=get_pass_settings_inline(cur_pass, cur_mode)
    )

async def pass_prompt_permanent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Directly prompt user to type permanent password"""
    query = update.callback_query
    await query.answer()
    
    context.user_data["pass_mode_intent"] = "permanent"
    await query.message.reply_html(
        "╔══════════════════════════════════╗\n"
        "║   🔒 <b>SET PERMANENT PASSWORD</b>   ║\n"
        "╚══════════════════════════════════╝\n\n"
        "Please type the <b>Permanent Password</b> you want to save (min 8 chars):\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 <i>This password will be auto-applied to all new accounts without asking.</i>\n"
        "<i>Or send /cancel to abort.</i>",
        reply_markup=get_cancel_keyboard()
    )
    return STATE_NEW_PASS

async def pass_prompt_temp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompt user to type 1-time password"""
    query = update.callback_query
    await query.answer()
    
    context.user_data["pass_mode_intent"] = "ask_each_time"
    await query.message.reply_html(
        "╔══════════════════════════════════╗\n"
        "║    ⏱️ <b>SET 1-TIME PASSWORD</b>     ║\n"
        "╚══════════════════════════════════╝\n\n"
        "Please type the <b>1-Time Password</b> (min 8 chars):\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 <i>The bot will prompt you again next time.</i>\n"
        "<i>Or send /cancel to abort.</i>",
        reply_markup=get_cancel_keyboard()
    )
    return STATE_NEW_PASS

async def pass_prompt_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generic prompt user to type a new password"""
    query = update.callback_query
    await query.answer()
    
    context.user_data["pass_mode_intent"] = None
    await query.message.reply_html(
        "╔══════════════════════════════════╗\n"
        "║       🔑 <b>ENTER NEW PASSWORD</b>     ║\n"
        "╚══════════════════════════════════╝\n\n"
        "Please type the new password you want to configure (min 8 chars):\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 <i>Or send /cancel to abort.</i>",
        reply_markup=get_cancel_keyboard()
    )
    return STATE_NEW_PASS

async def pass_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles inline callbacks for pass settings"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    db_user = get_user(user_id)
    if not db_user:
        return
        
    cur_pass = db_user.get("default_pass")
    cur_mode = db_user.get("pass_mode", "ask_each_time")
    
    if data == "pass_close":
        try:
            await query.message.delete()
        except Exception:
            pass
        return
        
    elif data == "pass_clear":
        clear_user_password(user_id)
        await query.edit_message_text(
            pass_settings_card(None, "ask_each_time"),
            parse_mode="HTML",
            reply_markup=get_pass_settings_inline(None, "ask_each_time")
        )
        return
        
    elif data == "pass_mode_perm":
        if cur_pass:
            set_user_password(user_id, cur_pass, mode="permanent")
            await query.edit_message_text(
                pass_settings_card(cur_pass, "permanent"),
                parse_mode="HTML",
                reply_markup=get_pass_settings_inline(cur_pass, "permanent")
            )
        else:
            # If no password set, trigger permanent password input!
            return await pass_prompt_permanent(update, context)
        return
        
    elif data == "pass_mode_temp":
        if cur_pass:
            set_user_password(user_id, cur_pass, mode="ask_each_time")
            await query.edit_message_text(
                pass_settings_card(cur_pass, "ask_each_time"),
                parse_mode="HTML",
                reply_markup=get_pass_settings_inline(cur_pass, "ask_each_time")
            )
        return
        
    elif data == "pass_scope_permanent":
        target_pass = context.user_data.get("pending_pass") or cur_pass
        if target_pass:
            set_user_password(user_id, target_pass, mode="permanent")
            context.user_data.pop("pending_pass", None)
            await query.edit_message_text(
                "╔══════════════════════════════════╗\n"
                "║   ✅ <b>PERMANENT PASSWORD SAVED</b> ║\n"
                "╚══════════════════════════════════╝\n\n"
                f"🔑 <code>{target_pass}</code> is now your permanent password.\n"
                "<i>It will be auto-applied to all future MultiLogin accounts!</i>",
                parse_mode="HTML"
            )
        else:
            return await pass_prompt_permanent(update, context)
        return
        
    elif data == "pass_scope_temp":
        target_pass = context.user_data.get("pending_pass") or cur_pass
        if target_pass:
            set_user_password(user_id, target_pass, mode="ask_each_time")
            context.user_data.pop("pending_pass", None)
            await query.edit_message_text(
                "⏱️ <b>Single-Time Password Mode Activated!</b>\n\n"
                "The bot will ask you for a password every time you create an account.",
                parse_mode="HTML"
            )
        return

async def pass_input_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receives new password text and saves it based on intent"""
    text = update.message.text.strip()
    user_id = update.effective_user.id
    is_admin = (user_id == ADMIN_ID)
    
    if text == BTN_CANCEL or "cancel" in text.lower():
        await update.message.reply_text("❌ Password setting cancelled.", reply_markup=get_main_keyboard(is_admin))
        return ConversationHandler.END
        
    if len(text) < 8:
        await update.message.reply_html(
            "⚠️ <b>Password too short!</b> Must be at least 8 characters.\n"
            "<i>Please enter a valid password:</i>",
            reply_markup=get_cancel_keyboard()
        )
        return STATE_NEW_PASS
        
    intent = context.user_data.pop("pass_mode_intent", None)
    
    if intent == "permanent":
        # Direct permanent save
        set_user_password(user_id, text, mode="permanent")
        await update.message.reply_html(
            "╔══════════════════════════════════╗\n"
            "║   ✅ <b>PERMANENT PASSWORD SAVED</b> ║\n"
            "╚══════════════════════════════════╝\n\n"
            f"🔑 Password: <code>{text}</code>\n"
            "🔒 Mode: <b>Permanent (All-Time)</b>\n\n"
            "<i>This password will now be automatically used for all future account creations!</i>",
            reply_markup=get_main_keyboard(is_admin)
        )
        return ConversationHandler.END
        
    elif intent == "ask_each_time":
        # Direct 1-time save
        set_user_password(user_id, text, mode="ask_each_time")
        await update.message.reply_html(
            "╔══════════════════════════════════╗\n"
            "║   ⏱️ <b>1-TIME PASSWORD SAVED</b>    ║\n"
            "╚══════════════════════════════════╝\n\n"
            f"🔑 Password: <code>{text}</code>\n"
            "⏱️ Mode: <b>Ask Each Time</b>\n\n"
            "<i>The bot will prompt you each time you create an account.</i>",
            reply_markup=get_main_keyboard(is_admin)
        )
        return ConversationHandler.END
        
    else:
        # Prompt user to choose scope
        context.user_data["pending_pass"] = text
        await update.message.reply_html(
            "╔══════════════════════════════════╗\n"
            "║     ⏱️ <b>SELECT PASSWORD MODE</b>     ║\n"
            "╚══════════════════════════════════╝\n\n"
            f"Password entered: <code>{text}</code>\n\n"
            "How would you like to save this password?\n"
            "• <b>Permanent (All-Time):</b> Auto-applied to all accounts without asking.\n"
            "• <b>Ask Each Time:</b> Prompts you each time.\n\n"
            "👇 <i>Choose an option:</i>",
            reply_markup=get_pass_scope_inline()
        )
        await update.message.reply_text("Select an option above 👆", reply_markup=get_main_keyboard(is_admin))
        return ConversationHandler.END
