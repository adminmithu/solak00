import re
import datetime
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from config import ADMIN_ID, BTN_CANCEL
from database import get_user, add_account, is_user_approved
from multilogin import start_registration, submit_otp, close_session, auto_create_account
from keyboards import get_main_keyboard, get_cancel_keyboard, get_create_method_inline, remove_keyboard
from templates import (
    create_method_choice_card, auto_step_email_card, auto_step_waiting_otp_card,
    auto_step_code_received_card, ask_email_card, ask_password_card, 
    ask_otp_card, account_success_card, pending_access_card
)

# Conversation states
STATE_METHOD_CHOICE, STATE_EMAIL, STATE_PASSWORD, STATE_OTP = range(4)

EMAIL_REGEX = r"^[\w\.\+\-]+@[a-zA-Z0-9\-]+\.[a-zA-Z0-9\-\.]+$"

async def acc_create_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point when user clicks '🚀 Acc Create'"""
    user = update.effective_user
    if not user:
        return ConversationHandler.END
        
    user_id = user.id
    is_admin = (user_id == ADMIN_ID)
    if not is_user_approved(user_id):
        await update.message.reply_html(
            pending_access_card(user_id, user.first_name, user.username),
            reply_markup=remove_keyboard()
        )
        return ConversationHandler.END
        
    # Clear previous flow data
    context.user_data.pop("target_email", None)
    context.user_data.pop("target_password", None)
    context.user_data.pop("flow_mode", None)
    
    # Check if user has a configured permanent password
    default_pass = db_user.get("default_pass")
    pass_mode = db_user.get("pass_mode", "ask_each_time")
    
    has_saved_pass = False
    masked_pass = ""
    if default_pass and pass_mode == "permanent":
        context.user_data["target_password"] = default_pass
        has_saved_pass = True
        masked_pass = default_pass[:2] + ("*" * max(4, len(default_pass) - 4)) + default_pass[-2:]
        
    # Show Choice: 1-Click Auto Temp-Mail OR Custom Email
    await update.message.reply_html(
        create_method_choice_card(has_saved_pass=has_saved_pass, saved_pass_masked=masked_pass),
        reply_markup=get_create_method_inline()
    )
    return STATE_METHOD_CHOICE

async def method_choice_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles user selection of creation method (Auto Temp-Mail vs Custom)"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    is_admin = (user_id == ADMIN_ID)
    data = query.data
    
    if data == "create_method_cancel":
        try:
            await query.message.delete()
        except Exception:
            pass
        await query.message.reply_text("❌ Cancelled.", reply_markup=get_main_keyboard(is_admin))
        return ConversationHandler.END
        
    elif data == "create_method_auto":
        # ⚡ 1-Click Auto Temp-Mail Selected
        context.user_data["flow_mode"] = "auto"
        saved_pass = context.user_data.get("target_password")
        
        if saved_pass:
            # We already have a saved password -> start auto creation immediately!
            try:
                await query.message.delete()
            except Exception:
                pass
            return await execute_auto_create(query.message, context, user_id, saved_pass, is_admin)
        else:
            # Need to prompt user for password
            await query.edit_message_text(
                ask_password_card("Müllfach Auto-Generated Temp Mail"),
                parse_mode="HTML"
            )
            p_msg = await query.message.reply_text(
                "💡 <i>Send /cancel to abort.</i>",
                parse_mode="HTML",
                reply_markup=get_cancel_keyboard()
            )
            context.user_data["choice_msg_id"] = query.message.message_id
            context.user_data["prompt_msg_id"] = p_msg.message_id
            return STATE_PASSWORD
            
    elif data == "create_method_custom":
        # ✍️ Custom Email Selected
        context.user_data["flow_mode"] = "custom"
        saved_pass = context.user_data.get("target_password")
        has_saved = bool(saved_pass)
        masked = (saved_pass[:2] + "****" + saved_pass[-2:]) if has_saved else ""
        
        await query.edit_message_text(
            ask_email_card(has_saved_pass=has_saved, saved_pass_masked=masked),
            parse_mode="HTML"
        )
        p_msg = await query.message.reply_text(
            "💡 <i>Send /cancel to abort.</i>",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )
        context.user_data["choice_msg_id"] = query.message.message_id
        context.user_data["prompt_msg_id"] = p_msg.message_id
        return STATE_EMAIL

async def execute_auto_create(msg_target, context, user_id: int, password: str, is_admin: bool):
    """Executes the full automated 1-click Müllfach.de registration flow with live premium card updates and auto-hiding"""
    status_msg = None
    
    async def step_callback(step: str, email: str, code: str):
        nonlocal status_msg
        if step == "step_email":
            card = auto_step_email_card(email)
            if status_msg is None:
                status_msg = await msg_target.reply_html(card)
            else:
                try:
                    await status_msg.edit_text(card, parse_mode="HTML")
                except Exception:
                    pass
        elif step == "step_waiting_otp":
            card = auto_step_waiting_otp_card(email)
            if status_msg:
                try:
                    await status_msg.edit_text(card, parse_mode="HTML")
                except Exception:
                    pass
        elif step == "step_code_received":
            card = auto_step_code_received_card(email, code)
            if status_msg:
                try:
                    await status_msg.edit_text(card, parse_mode="HTML")
                except Exception:
                    pass

    # Run full auto registration
    res = await auto_create_account(user_id, password, step_callback=step_callback)
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Clean up any prompt messages stored in context
    for key in ["choice_msg_id", "prompt_msg_id"]:
        mid = context.user_data.pop(key, None)
        if mid:
            try:
                await context.bot.delete_message(chat_id=user_id, message_id=mid)
            except Exception:
                pass

    if res["success"]:
        email = res["email"]
        password = res["password"]
        
        # Save to database
        add_account(user_id, email, password)
        
        # AUTO-HIDE: Delete the intermediate progress/code card completely!
        if status_msg:
            try:
                await status_msg.delete()
            except Exception:
                pass
            
        # Send ONLY the final clean, premium MultiLogin Account Created card!
        await msg_target.reply_html(
            account_success_card(email, password, now_str),
            reply_markup=get_main_keyboard(is_admin)
        )
    else:
        err = res.get("error", "Unknown registration error.")
        err_card = (
            "╔══════════════════════════════════╗\n"
            "║    ❌ <b>AUTO-CREATION FAILED</b>    ║\n"
            "╚══════════════════════════════════╝\n\n"
            f"<b>Error Details:</b>\n{err}\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💡 <i>You can click 'Acc Create' to try again anytime.</i>"
        )
        if status_msg:
            try:
                await status_msg.edit_text(err_card, parse_mode="HTML")
            except Exception:
                await msg_target.reply_html(err_card, reply_markup=get_main_keyboard(is_admin))
        else:
            await msg_target.reply_html(err_card, reply_markup=get_main_keyboard(is_admin))
            
    # Clean up state
    context.user_data.pop("target_email", None)
    context.user_data.pop("target_password", None)
    context.user_data.pop("flow_mode", None)
    return ConversationHandler.END

async def email_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles receiving custom email address"""
    text = update.message.text.strip()
    user_id = update.effective_user.id
    is_admin = (user_id == ADMIN_ID)
    
    if text == BTN_CANCEL or "cancel" in text.lower():
        await close_session(user_id)
        await update.message.reply_text("❌ Registration cancelled.", reply_markup=get_main_keyboard(is_admin))
        return ConversationHandler.END
        
    if not re.match(EMAIL_REGEX, text):
        await update.message.reply_html(
            "⚠️ <b>Invalid Email Address!</b>\n\n"
            "Please provide a valid email address (e.g. <code>myemail@gmail.com</code>):",
            reply_markup=get_cancel_keyboard()
        )
        return STATE_EMAIL
        
    context.user_data["target_email"] = text
    
    # Check if password is already provided
    if context.user_data.get("target_password"):
        password = context.user_data["target_password"]
        status_msg = await update.message.reply_html(
            "⏳ <b>Connecting to MultiLogin signup portal...</b>\n"
            "<i>Submitting email and credentials. Please wait ~10-15s...</i>"
        )
        
        res = await start_registration(user_id, text, password)
        if not res["success"]:
            try:
                await status_msg.delete()
            except Exception:
                pass
            await update.message.reply_html(
                f"❌ <b>Registration Failed:</b>\n{res['error']}\n\n<i>You can try again anytime.</i>",
                reply_markup=get_main_keyboard(is_admin)
            )
            return ConversationHandler.END
            
        try:
            await status_msg.delete()
        except Exception:
            pass
            
        await update.message.reply_html(
            ask_otp_card(text),
            reply_markup=get_cancel_keyboard()
        )
        return STATE_OTP
    else:
        # Prompt user to input password
        await update.message.reply_html(
            ask_password_card(text),
            reply_markup=get_cancel_keyboard()
        )
        return STATE_PASSWORD

async def password_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles receiving the password"""
    password = update.message.text.strip()
    user_id = update.effective_user.id
    is_admin = (user_id == ADMIN_ID)
    
    if password == BTN_CANCEL or "cancel" in password.lower():
        await close_session(user_id)
        await update.message.reply_text("❌ Registration cancelled.", reply_markup=get_main_keyboard(is_admin))
        return ConversationHandler.END
        
    if len(password) < 8:
        await update.message.reply_html(
            "⚠️ <b>Password too short!</b> MultiLogin requires at least 8 characters.\n"
            "<i>Please enter a stronger password:</i>",
            reply_markup=get_cancel_keyboard()
        )
        return STATE_PASSWORD
        
    flow_mode = context.user_data.get("flow_mode")
    
    # If this was 1-Click Auto Temp-Mail mode
    if flow_mode == "auto":
        return await execute_auto_create(update.message, context, user_id, password, is_admin)
        
    # Else Custom Email flow
    email = context.user_data.get("target_email")
    if not email:
        await update.message.reply_text("Session error. Please restart registration.", reply_markup=get_main_keyboard(is_admin))
        return ConversationHandler.END
        
    context.user_data["target_password"] = password
    
    status_msg = await update.message.reply_html(
        "⏳ <b>Connecting to MultiLogin signup portal...</b>\n"
        "<i>Submitting email and credentials. Please wait ~10-15s...</i>"
    )
    
    res = await start_registration(user_id, email, password)
    if not res["success"]:
        try:
            await status_msg.delete()
        except Exception:
            pass
        await update.message.reply_html(
            f"❌ <b>Registration Failed:</b>\n{res['error']}\n\n<i>You can try again anytime.</i>",
            reply_markup=get_main_keyboard(is_admin)
        )
        return ConversationHandler.END
        
    try:
        await status_msg.delete()
    except Exception:
        pass
        
    await update.message.reply_html(
        ask_otp_card(email),
        reply_markup=get_cancel_keyboard()
    )
    return STATE_OTP

async def otp_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles receiving the manual 6-digit OTP for custom email flow"""
    code = update.message.text.strip().replace(" ", "").replace("-", "")
    user_id = update.effective_user.id
    is_admin = (user_id == ADMIN_ID)
    
    if code == BTN_CANCEL or "cancel" in code.lower():
        await close_session(user_id)
        await update.message.reply_text("❌ Registration cancelled.", reply_markup=get_main_keyboard(is_admin))
        return ConversationHandler.END
        
    if len(code) != 6 or not code.isdigit():
        await update.message.reply_html(
            "⚠️ <b>Invalid Code Format!</b>\n"
            "<i>Please enter the exact 6-digit numeric verification code:</i>",
            reply_markup=get_cancel_keyboard()
        )
        return STATE_OTP
        
    status_msg = await update.message.reply_html(
        "⏳ <b>Submitting verification code to MultiLogin...</b>\n"
        "<i>Finalizing account creation, please wait...</i>"
    )
    
    res = await submit_otp(user_id, code)
    try:
        await status_msg.delete()
    except Exception:
        pass
        
    if res["success"]:
        email = res["email"]
        password = res["password"]
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Save account to database
        add_account(user_id, email, password)
        
        # Send premium success card
        await update.message.reply_html(
            account_success_card(email, password, now_str),
            reply_markup=get_main_keyboard(is_admin)
        )
        
        # Clean up conversation state
        context.user_data.pop("target_email", None)
        context.user_data.pop("target_password", None)
        context.user_data.pop("flow_mode", None)
        return ConversationHandler.END
    else:
        err_msg = res.get("error", "Verification failed.")
        if "Invalid" in err_msg or "Incorrect" in err_msg:
            await update.message.reply_html(
                f"❌ <b>Incorrect Code!</b>\n{err_msg}\n\n"
                "👉 <i>Please re-check your email and enter the code again:</i>",
                reply_markup=get_cancel_keyboard()
            )
            return STATE_OTP
        else:
            await update.message.reply_html(
                f"❌ <b>Verification Failed:</b>\n{err_msg}",
                reply_markup=get_main_keyboard(is_admin)
            )
            return ConversationHandler.END

async def cancel_acc_create(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Explicit cancel handler"""
    user_id = update.effective_user.id
    is_admin = (user_id == ADMIN_ID)
    await close_session(user_id)
    context.user_data.pop("target_email", None)
    context.user_data.pop("target_password", None)
    context.user_data.pop("flow_mode", None)
    await update.message.reply_text("❌ Action cancelled.", reply_markup=get_main_keyboard(is_admin))
    return ConversationHandler.END
