from telegram import ReplyKeyboardMarkup, KeyboardButton


def make_keyboard(rows):
    buttons = []

    for row in rows:
        row_buttons = []

        for text in row:
            row_buttons.append(KeyboardButton(text))

        buttons.append(row_buttons)

    return ReplyKeyboardMarkup(
        buttons,
        resize_keyboard=True,
        one_time_keyboard=False,
        is_persistent=True,
    )


# =========================================================
# واجهة المستخدم الرئيسية
# =========================================================

def user_keyboard(is_admin_user=False):
    rows = [
        ["📖 القرآن والثقافة"],
        ["📚 الملازم"],
        ["🎧 المحاضرات"],
        ["ℹ️ عن البوت"],
    ]

    if is_admin_user:
        rows.append(["⚙️ الإدارة"])

    return make_keyboard(rows)


# =========================================================
# القائمة العامة
# =========================================================

def public_menu_keyboard(
    children=None,
    contents=None,
    media_groups=None,
):
    rows = []

    children = children or []
    contents = contents or []
    media_groups = media_groups or []

    # الفروع
    for menu in children:
        rows.append([
            f"📂 {menu['name']}"
        ])

    # المحتويات الفردية
    for content in contents:
        icon = content_type_icon(
            content["content_type"]
        )

        rows.append([
            f"{icon} {content['title']}"
        ])

    # مجموعات الوسائط
    for group in media_groups:
        icon = media_group_icon(
            group["media_type"]
        )

        rows.append([
            f"{icon} {group['title']}"
        ])

    rows.append(["◀️ رجوع"])

    return make_keyboard(rows)


# =========================================================
# أيقونات المحتوى
# =========================================================

def content_type_icon(content_type):
    icons = {
        "text": "📝",
        "document": "📄",
        "photo": "🖼️",
        "video": "🎬",
        "audio": "🎵",
        "voice": "🎤",
        "url": "🔗",
    }

    return icons.get(
        content_type,
        "📄",
    )


def media_group_icon(media_type):
    icons = {
        "photo": "🖼️",
        "video": "🎬",
        "audio": "🎵",
    }

    return icons.get(
        media_type,
        "📁",
    )


# =========================================================
# لوحة الإدارة الرئيسية
# =========================================================

def admin_keyboard():
    return make_keyboard([
        ["📂 إدارة القوائم"],
        ["👥 المشرفون", "📊 الإحصائيات"],
        ["👤 واجهة المستخدم"],
    ])


# =========================================================
# إدارة القوائم الرئيسية
# =========================================================

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


# =========================================================
# قائمة الإدارة داخل أي قائمة أو فرع
# =========================================================

def admin_menu_keyboard(
    children=None,
    contents=None,
    media_groups=None,
):
    rows = []

    children = children or []
    contents = contents or []
    media_groups = media_groups or []

    # الفروع الموجودة
    for menu in children:
        rows.append([
            f"📂 {menu['name']}"
        ])

    # المحتويات الفردية
    for content in contents:
        icon = content_type_icon(
            content["content_type"]
        )

        rows.append([
            f"{icon} {content['title']}"
        ])

    # مجموعات الوسائط
    for group in media_groups:
        icon = media_group_icon(
            group["media_type"]
        )

        rows.append([
            f"{icon} {group['title']}"
        ])

    # أدوات القائمة
    rows.append([
        "➕ إضافة فرع"
    ])

    rows.append([
        "📦 إضافة محتوى"
    ])

    rows.append([
        "◀️ رجوع"
    ])

    return make_keyboard(rows)


# =========================================================
# قائمة أنواع المحتوى
# =========================================================

def content_menu_keyboard():
    return make_keyboard([
        ["📝 إضافة نص"],
        ["🖼️ إضافة صور متعددة"],
        ["🎬 إضافة فيديوهات متعددة"],
        ["🎵 إضافة أصوات متعددة"],
        ["📄 إضافة ملف"],
        ["🔗 إضافة رابط"],
        ["◀️ رجوع"],
    ])


# =========================================================
# لوحة إنهاء مجموعة الوسائط
# =========================================================

def media_group_finish_keyboard():
    return make_keyboard([
        ["✅ إنهاء"],
        ["❌ إلغاء"],
    ])


# =========================================================
# زر الإلغاء
# =========================================================

def cancel_keyboard():
    return make_keyboard([
        ["❌ إلغاء"]
    ])
