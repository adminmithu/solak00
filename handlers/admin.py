import io
import datetime
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from config import ADMIN_ID, BTN_CANCEL
from database import (
    get_user, approve_user, reject_user, block_user, get_pending_users, 
    get_approved_users, get_stats, get_all_accounts
)
from keyboards import (
    get_admin_panel_inline, get_main_keyboard, get_cancel_keyboard, 
    get_approval_inline, remove_keyboard
)
from templates import admin_panel_card, welcome_approved_card

STATE_ADMIN_BROADCAST = 1
STATE_ADMIN_MANUAL_APPROVE = 2
STATE_ADMIN_BLOCK_USER = 3

async def admin_panel_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry when Admin clicks '👑 Admin Panel'"""
    user = update.effective_user
    if not user or user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Unauthorized. Admin access only.")
        return
        
    stats = get_stats()
    await update.message.reply_html(
        admin_panel_card(stats),
        reply_markup=get_admin_panel_inline()
    )

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles admin callback buttons"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    if user.id != ADMIN_ID:
        return
        
    data = query.data
    
    # 1. Close panel
    if data == "adm_close":
        try:
            await query.message.delete()
        except Exception:
            pass
        return
        
    # 2. Refresh stats
    elif data == "adm_stats_refresh":
        stats = get_stats()
        await query.edit_message_text(
            admin_panel_card(stats),
            parse_mode="HTML",
            reply_markup=get_admin_panel_inline()
        )
        return
        
    # 3. View Pending Users
    elif data == "adm_view_pending":
        pending = get_pending_users()
        if not pending:
            await query.edit_message_text(
                "✅ <b>No Pending Users!</b>\nAll user access requests have been processed.",
                parse_mode="HTML",
                reply_markup=get_admin_panel_inline()
            )
            return
            
        txt = f"⏳ <b>Pending Approval List ({len(pending)}):</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        for u in pending[:10]:
            uname = f"@{u['username']}" if u.get('username') else "NoUsername"
            txt += f"👤 <b>{u.get('first_name', 'User')}</b> ({uname})\n"
            txt += f"🆔 <code>{u['user_id']}</code> | ⏰ {u.get('created_at', '')}\n\n"
            
        txt += "<i>Use the 'Approve by User ID' button below to approve any user.</i>"
        await query.edit_message_text(
            txt,
            parse_mode="HTML",
            reply_markup=get_admin_panel_inline()
        )
        return
        
    # 4. View Approved Users
    elif data == "adm_view_approved":
        approved = get_approved_users()
        if not approved:
            await query.edit_message_text(
                "ℹ️ No approved users found.",
                parse_mode="HTML",
                reply_markup=get_admin_panel_inline()
            )
            return
            
        txt = f"📋 <b>Approved Users ({len(approved)}):</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        for u in approved[:15]:
            uname = f"@{u['username']}" if u.get('username') else "(No Username)"
            txt += f"• 👤 <b>{u.get('first_name', 'User')}</b> ({uname}) ➔ 🆔 <code>{u['user_id']}</code>\n"
            
        if len(approved) > 15:
            txt += f"\n<i>...and {len(approved) - 15} more users.</i>"
            
        await query.edit_message_text(
            txt,
            parse_mode="HTML",
            reply_markup=get_admin_panel_inline()
        )
        return
        
    # 5. One-click Approve / Reject from alert card
    elif data.startswith("adm_app_"):
        target_uid = int(data.replace("adm_app_", ""))
        approve_user(target_uid)
        
        # Notify Admin in query message
        await query.edit_message_text(
            f"✅ <b>User <code>{target_uid}</code> has been APPROVED!</b>\nThey have been granted full menu access.",
            parse_mode="HTML"
        )
        
        # Notify the user directly
        try:
            target_user = get_user(target_uid)
            name = target_user.get("first_name", "User") if target_user else "User"
            await context.bot.send_message(
                chat_id=target_uid,
                text=welcome_approved_card(name),
                parse_mode="HTML",
                reply_markup=get_main_keyboard(False)
            )
        except Exception:
            pass
        return
        
    elif data.startswith("adm_rej_"):
        target_uid = int(data.replace("adm_rej_", ""))
        reject_user(target_uid)
        await query.edit_message_text(
            f"❌ <b>User <code>{target_uid}</code> has been REJECTED.</b>",
            parse_mode="HTML"
        )
        return
        
    # 6. Export accounts to text file
    elif data == "adm_export_accs":
        accs = get_all_accounts(limit=1000)
        if not accs:
            await query.answer("No accounts created yet.", show_alert=True)
            return
            
        content = "=== MULTILOGIN CREATED ACCOUNTS ===\n"
        content += f"Exported At: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        content += f"Total Accounts: {len(accs)}\n"
        content += "=" * 45 + "\n\n"
        
        for a in accs:
            content += f"Email    : {a.get('email')}\n"
            content += f"Password : {a.get('password')}\n"
            content += f"Creator  : {a.get('username') or a.get('user_id')}\n"
            content += f"Date     : {a.get('created_at')}\n"
            content += "-" * 35 + "\n"
            
        file_obj = io.BytesIO(content.encode("utf-8"))
        file_obj.name = f"multilogin_accounts_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        await context.bot.send_document(
            chat_id=ADMIN_ID,
            document=file_obj,
            caption=f"📁 <b>Exported {len(accs)} MultiLogin Accounts</b>",
            parse_mode="HTML"
        )
        return

async def broadcast_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin clicks '📢 Broadcast to All'"""
    query = update.callback_query
    await query.answer()
    
    await query.message.reply_html(
        "╔══════════════════════════════════╗\n"
        "║     📢 <b>BROADCAST MESSAGE</b>      ║\n"
        "╚══════════════════════════════════╝\n\n"
        "Please send the message you want to broadcast to all approved users:\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 <i>Or send /cancel to abort.</i>",
        reply_markup=get_cancel_keyboard()
    )
    return STATE_ADMIN_BROADCAST

async def broadcast_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin delivers broadcast text to be sent out"""
    text = update.message.text.strip()
    if text == BTN_CANCEL or "cancel" in text.lower():
        await update.message.reply_text("❌ Broadcast cancelled.", reply_markup=get_main_keyboard(True))
        return ConversationHandler.END
        
    approved_users = get_approved_users()
    success_count = 0
    fail_count = 0
    
    status_msg = await update.message.reply_html(f"⏳ <b>Broadcasting to {len(approved_users)} users...</b>")
    
    broadcast_text = (
        "╔══════════════════════════════════╗\n"
        "║     📢 <b>ANNOUNCEMENT</b>           ║\n"
        "╚══════════════════════════════════╝\n\n"
        f"{text}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<i>MultiACC Creator System Broadcast</i>"
    )
    
    for u in approved_users:
        uid = u["user_id"]
        try:
            await context.bot.send_message(
                chat_id=uid,
                text=broadcast_text,
                parse_mode="HTML"
            )
            success_count += 1
        except Exception:
            fail_count += 1
            
    try:
        await status_msg.delete()
    except Exception:
        pass
        
    await update.message.reply_html(
        f"✅ <b>Broadcast Completed!</b>\n\n"
        f"• Successfully sent: <code>{success_count}</code>\n"
        f"• Failed / Blocked: <code>{fail_count}</code>",
        reply_markup=get_main_keyboard(True)
    )
    return ConversationHandler.END

async def manual_approve_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin clicks 'Approve by User ID'"""
    query = update.callback_query
    await query.answer()
    
    pending = get_pending_users()
    users_preview = ""
    if pending:
        users_preview = "⏳ <b>Pending Users Awaiting Approval:</b>\n"
        for u in pending[:10]:
            uname = f"@{u['username']}" if u.get('username') else "(No Username)"
            users_preview += f"• 👤 <b>{u.get('first_name', 'User')}</b> ({uname}) ➔ 🆔 <code>{u['user_id']}</code>\n"
        users_preview += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    await query.message.reply_html(
        "╔══════════════════════════════════╗\n"
        "║    🔑 <b>APPROVE BY USER ID</b>      ║\n"
        "╚══════════════════════════════════╝\n\n"
        f"{users_preview}"
        "Please type or paste the <b>Telegram User ID</b> to approve:\n"
        "<i>(Tip: Tap on any ID above to copy it instantly)</i>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 <i>Or send /cancel to abort.</i>",
        reply_markup=get_cancel_keyboard()
    )
    return STATE_ADMIN_MANUAL_APPROVE

async def manual_approve_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin enters User ID to approve"""
    text = update.message.text.strip()
    if text == BTN_CANCEL or "cancel" in text.lower():
        await update.message.reply_text("❌ Action cancelled.", reply_markup=get_main_keyboard(True))
        return ConversationHandler.END
        
    if not text.isdigit():
        await update.message.reply_html(
            "⚠️ <b>Invalid ID!</b> Must be numeric.\n<i>Please enter a valid numeric Telegram ID:</i>",
            reply_markup=get_cancel_keyboard()
        )
        return STATE_ADMIN_MANUAL_APPROVE
        
    target_id = int(text)
    approve_user(target_id)
    
    # Try notifying the user
    try:
        await context.bot.send_message(
            chat_id=target_id,
            text=welcome_approved_card("User"),
            parse_mode="HTML",
            reply_markup=get_main_keyboard(False)
        )
        user_notified = True
    except Exception:
        user_notified = False
        
    notif_text = " (User was notified in chat)" if user_notified else " (User has not started bot yet)"
    await update.message.reply_html(
        f"✅ <b>User ID <code>{target_id}</code> is now APPROVED!</b>{notif_text}",
        reply_markup=get_main_keyboard(True)
    )
    return ConversationHandler.END

async def block_user_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin clicks '🚫 Block User ID'"""
    query = update.callback_query
    await query.answer()
    
    approved = get_approved_users()
    users_preview = ""
    if approved:
        users_preview = "📋 <b>Currently Approved Users:</b>\n"
        for u in approved[:10]:
            uname = f"@{u['username']}" if u.get('username') else "(No Username)"
            users_preview += f"• 👤 <b>{u.get('first_name', 'User')}</b> ({uname}) ➔ 🆔 <code>{u['user_id']}</code>\n"
        users_preview += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    await query.message.reply_html(
        "╔══════════════════════════════════╗\n"
        "║     🚫 <b>BLOCK / REVOKE USER</b>     ║\n"
        "╚══════════════════════════════════╝\n\n"
        f"{users_preview}"
        "Please type or paste the <b>Telegram User ID</b> to BLOCK:\n"
        "<i>(Tip: Tap on any ID above to copy it instantly)</i>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚠️ <i>This user will immediately lose access and all their menu buttons will be wiped.</i>\n"
        "💡 <i>Or send /cancel to abort.</i>",
        reply_markup=get_cancel_keyboard()
    )
    return STATE_ADMIN_BLOCK_USER

async def block_user_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin enters User ID to block"""
    text = update.message.text.strip()
    if text == BTN_CANCEL or "cancel" in text.lower():
        await update.message.reply_text("❌ Action cancelled.", reply_markup=get_main_keyboard(True))
        return ConversationHandler.END
        
    if not text.isdigit():
        await update.message.reply_html(
            "⚠️ <b>Invalid ID!</b> Must be numeric.\n<i>Please enter a valid numeric Telegram ID:</i>",
            reply_markup=get_cancel_keyboard()
        )
        return STATE_ADMIN_BLOCK_USER
        
    target_id = int(text)
    
    # Don't let admin block themselves
    if target_id == ADMIN_ID:
        await update.message.reply_text("⚠️ You cannot block yourself (Admin).", reply_markup=get_main_keyboard(True))
        return ConversationHandler.END
        
    block_user(target_id)
    
    # Try notifying the user and immediately wiping their keyboard
    try:
        await context.bot.send_message(
            chat_id=target_id,
            text="╔══════════════════════════════════╗\n"
                 "║     🔒 <b>ACCESS REVOKED</b> 🔒         ║\n"
                 "╚══════════════════════════════════╝\n\n"
                 "⚠️ <i>Your access to this bot has been revoked by the Administrator.</i>",
            parse_mode="HTML",
            reply_markup=remove_keyboard()
        )
        user_notified = True
    except Exception:
        user_notified = False
        
    notif_text = " (User was notified & keyboard stripped)" if user_notified else " (User could not be notified)"
    await update.message.reply_html(
        f"🚫 <b>User ID <code>{target_id}</code> has been BLOCKED successfully!</b>{notif_text}\n"
        "<i>All access and menu buttons have been revoked.</i>",
        reply_markup=get_main_keyboard(True)
    )
    return ConversationHandler.END
