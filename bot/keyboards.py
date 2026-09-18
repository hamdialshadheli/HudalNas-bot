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
        is_persistent=True
    )


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


def public_menu_keyboard(
    children=None,
    contents=None,
    media_groups=None
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
        icon = content_type_icon(content["content_type"])

        rows.append([
            f"{icon} {content['title']}"
        ])

    # مجموعات الوسائط
    for group in media_groups:
        icon = media_group_icon(group["media_type"])

        rows.append([
            f"{icon} {group['title']}"
        ])

    rows.append(["◀️ رجوع"])

    return make_keyboard(rows)


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

    return icons.get(content_type, "📄")


def media_group_icon(media_type):
    icons = {
        "photo": "🖼️",
        "video": "🎬",
        "audio": "🎵",
    }

    return icons.get(media_type, "📁")


def admin_keyboard():
    return make_keyboard([
        ["📂 إدارة القوائم"],
        ["👥 المشرفون", "📊 الإحصائيات"],
        ["👤 واجهة المستخدم"],
    ])


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


def admin_menu_keyboard(
    children=None,
    contents=None,
    media_groups=None
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
        icon = content_type_icon(content["content_type"])

        rows.append([
            f"{icon} {content['title']}"
        ])

    # مجموعات الوسائط
    for group in media_groups:
        icon = media_group_icon(group["media_type"])

        rows.append([
            f"{icon} {group['title']}"
        ])

    # أدوات الإدارة
    rows.append([
        "➕ إضافة فرع"
    ])

    rows.append([
        "📝 إضافة نص"
    ])

    rows.append([
        "🖼️ إضافة صور متعددة"
    ])

    rows.append([
        "🎬 إضافة فيديوهات متعددة"
    ])

    rows.append([
        "🎵 إضافة أصوات متعددة"
    ])

    rows.append([
        "📄 إضافة ملف"
    ])

    rows.append([
        "🔗 إضافة رابط"
    ])

    rows.append([
        "◀️ رجوع"
    ])

    return make_keyboard(rows)


def content_type_keyboard():
    return make_keyboard([
        ["📝 نص"],
        ["📄 ملف / PDF", "🔗 رابط"],
        ["❌ إلغاء"],
    ])


def media_group_type_keyboard():
    return make_keyboard([
        ["🖼️ إضافة صور متعددة"],
        ["🎬 إضافة فيديوهات متعددة"],
        ["🎵 إضافة أصوات متعددة"],
        ["❌ إلغاء"],
    ])


def media_group_finish_keyboard():
    return make_keyboard([
        ["✅ إنهاء"],
        ["❌ إلغاء"],
    ])


def cancel_keyboard():
    return make_keyboard([
        ["❌ إلغاء"]
    ])
