from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from config import (
    BTN_ACC_CREATE, BTN_PASS_SET, BTN_HISTORY, BTN_MULTILOGIN_DETAILS, 
    BTN_SUPPORT, BTN_ADMIN_PANEL, BTN_CANCEL
)

# Helper functions for styled buttons with background colors
def btn_success(text: str, callback_data: str) -> InlineKeyboardButton:
    """Button with green background"""
    return InlineKeyboardButton(text, callback_data=callback_data, api_kwargs={"style": "success"})

def btn_danger(text: str, callback_data: str) -> InlineKeyboardButton:
    """Button with red background"""
    return InlineKeyboardButton(text, callback_data=callback_data, api_kwargs={"style": "danger"})

def btn_primary(text: str, callback_data: str) -> InlineKeyboardButton:
    """Button with blue/primary background"""
    return InlineKeyboardButton(text, callback_data=callback_data, api_kwargs={"style": "primary"})

def btn_default(text: str, callback_data: str) -> InlineKeyboardButton:
    """Standard neutral button"""
    return InlineKeyboardButton(text, callback_data=callback_data)

def get_main_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Main menu reply keyboard with background colors for ALL buttons"""
    keyboard = [
        [
            KeyboardButton(BTN_ACC_CREATE, api_kwargs={"style": "success"}),
            KeyboardButton(BTN_PASS_SET, api_kwargs={"style": "primary"})
        ],
        [
            KeyboardButton(BTN_HISTORY, api_kwargs={"style": "primary"}),
            KeyboardButton(BTN_MULTILOGIN_DETAILS, api_kwargs={"style": "primary"})
        ],
        [
            KeyboardButton(BTN_SUPPORT, api_kwargs={"style": "primary"})
        ]
    ]
    if is_admin:
        keyboard.append([
            KeyboardButton(BTN_ADMIN_PANEL, api_kwargs={"style": "danger"})
        ])
        
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Cancel reply keyboard with red danger background"""
    return ReplyKeyboardMarkup(
        [[KeyboardButton(BTN_CANCEL, api_kwargs={"style": "danger"})]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def remove_keyboard() -> ReplyKeyboardRemove:
    """Removes reply keyboard"""
    return ReplyKeyboardRemove()

def get_pass_settings_inline(current_pass: str = None, current_mode: str = "ask_each_time") -> InlineKeyboardMarkup:
    """Password manager inline buttons with clear color actions"""
    keyboard = []
    
    if current_pass:
        # When a password already exists
        if current_mode == "permanent":
            keyboard.append([btn_primary("⏱️ Switch to: Ask Each Time", "pass_mode_temp")])
        else:
            keyboard.append([btn_success("🔒 Switch to: Permanent (All-Time)", "pass_mode_perm")])
            
        keyboard.append([btn_primary("✏️ Change Password", "pass_set_new")])
        keyboard.append([btn_danger("🗑️ Clear / Remove Password", "pass_clear")])
    else:
        # When no password is set yet
        keyboard.append([btn_success("🔒 Set Permanent Password", "pass_set_perm_direct")])
        keyboard.append([btn_primary("⏱️ Set 1-Time Password", "pass_set_temp_direct")])
        
    keyboard.append([btn_danger("✖️ Close Menu", "pass_close")])
    return InlineKeyboardMarkup(keyboard)

def get_pass_scope_inline() -> InlineKeyboardMarkup:
    """Scope buttons: Permanent (green), Ask Each Time (blue), Cancel (red)"""
    keyboard = [
        [
            btn_success("🔒 Permanent (All-Time)", "pass_scope_permanent"),
            btn_primary("⏱️ Ask Each Time", "pass_scope_temp")
        ],
        [btn_danger("❌ Cancel", "pass_close")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_create_method_inline() -> InlineKeyboardMarkup:
    """Creation method selection: Auto (green), Custom (blue), Cancel (red)"""
    keyboard = [
        [btn_success("⚡ Auto Create (1-Click Temp Mail)", "create_method_auto")],
        [btn_primary("✍️ Custom Email (Manual OTP)", "create_method_custom")],
        [btn_danger("❌ Cancel", "create_method_cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_approval_inline(user_id: int) -> InlineKeyboardMarkup:
    """Admin approval buttons: Approve (green), Reject (red)"""
    keyboard = [
        [
            btn_success("✅ Approve Access", f"adm_app_{user_id}"),
            btn_danger("❌ Reject", f"adm_rej_{user_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_panel_inline() -> InlineKeyboardMarkup:
    """Admin panel: actions styled with primary, success, and danger backgrounds"""
    keyboard = [
        [
            btn_primary("👥 Pending Users", "adm_view_pending"),
            btn_primary("📋 Approved Users", "adm_view_approved")
        ],
        [
            btn_primary("📢 Broadcast to All", "adm_broadcast_prompt"),
            btn_primary("📊 System Stats", "adm_stats_refresh")
        ],
        [
            btn_success("🔑 Approve User ID", "adm_manual_approve"),
            btn_danger("🚫 Block User ID", "adm_block_user_prompt")
        ],
        [
            btn_success("📁 Export Accounts List", "adm_export_accs")
        ],
        [btn_danger("🔙 Back to Main Menu", "adm_close")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_support_reply_inline(user_id: int, ticket_id: int) -> InlineKeyboardMarkup:
    """Support reply button: green success background"""
    keyboard = [
        [btn_success("✍️ Reply to User", f"adm_reply_{ticket_id}_{user_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_history_inline(page: int, total_pages: int) -> InlineKeyboardMarkup:
    """History pagination and download button with background colors"""
    keyboard = []
    nav_row = []
    if page > 1:
        nav_row.append(btn_primary("◀️ Prev", f"hist_page_{page-1}"))
    nav_row.append(btn_default(f"📄 {page}/{total_pages}", "hist_noop"))
    if page < total_pages:
        nav_row.append(btn_primary("Next ▶️", f"hist_page_{page+1}"))
    if nav_row:
        keyboard.append(nav_row)
        
    keyboard.append([
        btn_success("📥 Download History (.txt)", "hist_download"),
        btn_danger("✖️ Close", "hist_close")
    ])
    return InlineKeyboardMarkup(keyboard)
