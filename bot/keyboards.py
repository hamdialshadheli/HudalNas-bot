from telegram import ReplyKeyboardMarkup, KeyboardButton


def make_keyboard(rows):
    buttons = []

    for row in rows:
        row_buttons = []

        for text in row:
            row_buttons.append(
                KeyboardButton(text)
            )

        buttons.append(row_buttons)

    return ReplyKeyboardMarkup(
        buttons,
        resize_keyboard=True,
        one_time_keyboard=False,
        is_persistent=True,
    )


# ==========================================================
# الواجهة الرئيسية للمستخدم
# ==========================================================

def user_keyboard(is_admin_user=False):

    rows = [
        ["📖 القرآن والثقافة"],
        ["📚 الملازم"],
        ["🎧 المحاضرات"],
        ["ℹ️ عن البوت"],
    ]

    if is_admin_user:
        rows.append([
            "⚙️ الإدارة"
        ])

    return make_keyboard(rows)


# ==========================================================
# القوائم العامة للمستخدم
# ==========================================================

def public_menu_keyboard(contents=None):

    rows = []

    if contents:
        for content in contents:

            icon = content_type_icon(
                content["content_type"]
            )

            rows.append([
                f"{icon} {content['title']}"
            ])

    rows.append([
        "◀️ رجوع"
    ])

    return make_keyboard(rows)


# ==========================================================
# أيقونة نوع المحتوى
# ==========================================================

def content_type_icon(content_type):

    icons = {
        "text": "📝",
        "document": "📄",
        "photo": "🖼️",
        "video": "🎬",
        "audio": "🎧",
        "voice": "🎤",
        "url": "🔗",
    }

    return icons.get(
        content_type,
        "📄"
    )


# ==========================================================
# لوحة الإدارة الرئيسية
# ==========================================================

def admin_keyboard():

    return make_keyboard([

        ["📂 إدارة القوائم"],

        ["👥 المشرفون", "📊 الإحصائيات"],

        ["👤 واجهة المستخدم"],

    ])


# ==========================================================
# إدارة القوائم الرئيسية
# ==========================================================

def menus_keyboard(menus):

    rows = []

    for menu in menus:

        rows.append([
            f"📂 {menu['name']}"
        ])

    rows.append([
        "➕ إنشاء قائمة رئيسية"
    ])

    rows.append([
        "◀️ رجوع"
    ])

    return make_keyboard(rows)


# ==========================================================
# داخل القائمة الرئيسية للمشرف
# ==========================================================

def admin_menu_keyboard(contents=None):

    rows = []

    if contents:

        for content in contents:

            icon = content_type_icon(
                content["content_type"]
            )

            rows.append([
                f"{icon} {content['title']}"
            ])

    rows.append([
        "➕ إضافة محتوى"
    ])

    rows.append([
        "◀️ رجوع"
    ])

    return make_keyboard(rows)


# ==========================================================
# اختيار نوع المحتوى
# ==========================================================

def content_type_keyboard():

    return make_keyboard([

        ["📝 نص"],

        ["📄 ملف / PDF", "🖼️ صورة"],

        ["🎬 فيديو", "🎧 صوت"],

        ["🎤 رسالة صوتية", "🔗 رابط"],

        ["❌ إلغاء"],

    ])


# ==========================================================
# زر الإلغاء
# ==========================================================

def cancel_keyboard():

    return make_keyboard([
        ["❌ إلغاء"]
    ])
