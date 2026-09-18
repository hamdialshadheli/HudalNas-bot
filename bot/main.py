# ==========================================================
# بوت هدى للناس
# الملف الرئيسي
# ==========================================================

import os

from dotenv import load_dotenv

from telegram import Update

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from bot.database import (
    initialize_database,
    register_user,
    is_admin,
    ensure_admin,
    get_connection,
)

from bot.keyboards import (
    user_keyboard,
    admin_keyboard,
    menus_keyboard,
    menu_management_keyboard,
    public_menu_keyboard,
    content_type_keyboard,
    cancel_keyboard,
    content_type_icon,
)


# ==========================================================
# إعدادات البوت
# ==========================================================

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")


if not BOT_TOKEN:

    raise RuntimeError(
        "BOT_TOKEN غير موجود في GitHub Secrets"
    )


if not ADMIN_ID:

    raise RuntimeError(
        "ADMIN_ID غير موجود في GitHub Secrets"
    )


# ==========================================================
# الواجهة الرئيسية للمستخدم
# ==========================================================

async def show_public_home(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    register_user(
        update.effective_user
    )

    context.user_data.clear()

    admin_status = is_admin(
        update.effective_user.id
    )

    await update.message.reply_text(

        "🌿 مرحباً بك في بوت هدى للناس\n\n"
        "اختر من القائمة الرئيسية:",

        reply_markup=user_keyboard(
            is_admin_user=admin_status
        )
    )


# ==========================================================
# /start
# ==========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await show_public_home(
        update,
        context
    )


# ==========================================================
# لوحة الإدارة
# ==========================================================

async def show_admin_panel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_admin(
        update.effective_user.id
    ):

        await update.message.reply_text(
            "❌ ليس لديك صلاحية الدخول إلى لوحة الإدارة."
        )

        return

    context.user_data.clear()

    await update.message.reply_text(

        "⚙️ لوحة إدارة بوت هدى للناس\n\n"
        "اختر العملية المطلوبة:",

        reply_markup=admin_keyboard()
    )


# ==========================================================
# /admin
# ==========================================================

async def admin_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await show_admin_panel(
        update,
        context
    )


# ==========================================================
# إنشاء قائمة رئيسية
# ==========================================================

async def create_main_menu_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_admin(
        update.effective_user.id
    ):

        await update.message.reply_text(
            "❌ ليس لديك صلاحية."
        )

        return

    context.user_data.clear()

    context.user_data["state"] = (
        "creating_main_menu"
    )

    await update.message.reply_text(

        "📂 إنشاء قائمة رئيسية\n\n"
        "✏️ اكتب اسم القائمة:",

        reply_markup=cancel_keyboard()
    )


# ==========================================================
# إنشاء قائمة فرعية
# ==========================================================

async def create_submenu_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_admin(
        update.effective_user.id
    ):

        await update.message.reply_text(
            "❌ ليس لديك صلاحية."
        )

        return

    parent_id = context.user_data.get(
        "current_menu_id"
    )

    if not parent_id:

        await update.message.reply_text(
            "❌ لم يتم تحديد القائمة الحالية."
        )

        return

    context.user_data["state"] = (
        "creating_submenu"
    )

    context.user_data["parent_id"] = parent_id

    await update.message.reply_text(

        "📂 إنشاء قائمة فرعية\n\n"

        f"📌 داخل: "
        f"{context.user_data.get('current_menu_name', '')}\n\n"

        "✏️ اكتب اسم القائمة الفرعية:",

        reply_markup=cancel_keyboard()
    )


# ==========================================================
# حفظ قائمة جديدة
# ==========================================================

async def save_new_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    if not is_admin(user_id):

        context.user_data.clear()

        await update.message.reply_text(
            "❌ ليس لديك صلاحية."
        )

        return

    menu_name = update.message.text.strip()

    if not menu_name:

        await update.message.reply_text(
            "❌ اسم القائمة لا يمكن أن يكون فارغًا."
        )

        return

    state = context.user_data.get(
        "state"
    )

    if state == "creating_main_menu":

        parent_id = None

    elif state == "creating_submenu":

        parent_id = context.user_data.get(
            "parent_id"
        )

    else:

        return

    connection = get_connection()

    # ------------------------------------------------------
    # التحقق من الاسم
    # ------------------------------------------------------

    if parent_id is None:

        existing = connection.execute(

            """
            SELECT id
            FROM menus
            WHERE name = ?
            AND parent_id IS NULL
            """,

            (menu_name,)
        ).fetchone()

    else:

        existing = connection.execute(

            """
            SELECT id
            FROM menus
            WHERE name = ?
            AND parent_id = ?
            """,

            (
                menu_name,
                parent_id
            )
        ).fetchone()

    if existing:

        connection.close()

        await update.message.reply_text(

            "⚠️ توجد قائمة بهذا الاسم في نفس المستوى.\n\n"
            "اكتب اسمًا آخر:"
        )

        return

    # ------------------------------------------------------
    # الترتيب
    # ------------------------------------------------------

    if parent_id is None:

        order_row = connection.execute(

            """
            SELECT COALESCE(
                MAX(display_order), 0
            ) + 1 AS next_order

            FROM menus

            WHERE parent_id IS NULL
            """
        ).fetchone()

    else:

        order_row = connection.execute(

            """
            SELECT COALESCE(
                MAX(display_order), 0
            ) + 1 AS next_order

            FROM menus

            WHERE parent_id = ?
            """,

            (parent_id,)
        ).fetchone()

    next_order = order_row["next_order"]

    # ------------------------------------------------------
    # إنشاء القائمة
    # ------------------------------------------------------

    cursor = connection.execute(

        """
        INSERT INTO menus (
            name,
            parent_id,
            display_order
        )

        VALUES (?, ?, ?)
        """,

        (
            menu_name,
            parent_id,
            next_order
        )
    )

    new_menu_id = cursor.lastrowid

    connection.commit()

    connection.close()

    # ------------------------------------------------------
    # قائمة فرعية
    # ------------------------------------------------------

    if state == "creating_submenu":

        current_menu_id = parent_id

        context.user_data.clear()

        await update.message.reply_text(

            "✅ تم إنشاء القائمة الفرعية بنجاح.\n\n"

            f"📂 الاسم: {menu_name}\n"
            f"🆔 ID: {new_menu_id}"
        )

        await open_menu(
            update,
            context,
            current_menu_id
        )

        return

    # ------------------------------------------------------
    # قائمة رئيسية
    # ------------------------------------------------------

    context.user_data.clear()

    await update.message.reply_text(

        "✅ تم إنشاء القائمة الرئيسية بنجاح.\n\n"

        f"📂 الاسم: {menu_name}\n"
        f"🆔 ID: {new_menu_id}"
    )

    await show_menus(
        update,
        context
    )


# ==========================================================
# عرض القوائم الرئيسية للمشرف
# ==========================================================

async def show_menus(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_admin(
        update.effective_user.id
    ):

        return

    connection = get_connection()

    menus = connection.execute(

        """
        SELECT
            id,
            name,
            display_order

        FROM menus

        WHERE parent_id IS NULL

        ORDER BY
            display_order ASC,
            id ASC
        """
    ).fetchall()

    connection.close()

    await update.message.reply_text(

        "📂 إدارة القوائم\n\n"
        "اختر قائمة لإدارتها:",

        reply_markup=menus_keyboard(
            menus
        )
    )


# ==========================================================
# فتح قائمة للمشرف
# ==========================================================

async def open_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    menu_id
):

    if not is_admin(
        update.effective_user.id
    ):

        return

    connection = get_connection()

    menu = connection.execute(

        """
        SELECT
            id,
            name,
            parent_id

        FROM menus

        WHERE id = ?
        """,

        (menu_id,)
    ).fetchone()

    if not menu:

        connection.close()

        await update.message.reply_text(
            "❌ القائمة غير موجودة."
        )

        return

    children = connection.execute(

        """
        SELECT
            id,
            name,
            display_order

        FROM menus

        WHERE parent_id = ?

        ORDER BY
            display_order ASC,
            id ASC
        """,

        (menu_id,)
    ).fetchall()

    connection.close()

    context.user_data["current_menu_id"] = (
        menu["id"]
    )

    context.user_data["current_menu_name"] = (
        menu["name"]
    )

    context.user_data["current_parent_id"] = (
        menu["parent_id"]
    )

    await update.message.reply_text(

        f"📂 {menu['name']}\n\n"
        "اختر أحد العناصر:",

        reply_markup=menu_management_keyboard(
            children
        )
    )


# ==========================================================
# البحث عن قائمة
# ==========================================================

def find_menu_by_name(
    menu_name,
    parent_id=None
):

    connection = get_connection()

    if parent_id is None:

        menu = connection.execute(

            """
            SELECT
                id,
                name,
                parent_id

            FROM menus

            WHERE name = ?

            AND parent_id IS NULL
            """,

            (menu_name,)
        ).fetchone()

    else:

        menu = connection.execute(

            """
            SELECT
                id,
                name,
                parent_id

            FROM menus

            WHERE name = ?

            AND parent_id = ?
            """,

            (
                menu_name,
                parent_id
            )
        ).fetchone()

    connection.close()

    return menu


# ==========================================================
# إضافة محتوى - البداية
# ==========================================================

async def start_add_content(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_admin(
        update.effective_user.id
    ):

        return

    context.user_data.clear()

    context.user_data["state"] = (
        "select_content_menu"
    )

    await show_content_menu_selector(
        update,
        context,
        None
    )


# ==========================================================
# اختيار القائمة لإضافة المحتوى
# ==========================================================

async def show_content_menu_selector(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    parent_id
):

    connection = get_connection()

    if parent_id is None:

        menus = connection.execute(

            """
            SELECT
                id,
                name,
                parent_id

            FROM menus

            WHERE parent_id IS NULL

            ORDER BY
                display_order ASC,
                id ASC
            """
        ).fetchall()

        title = (
            "➕ إضافة محتوى\n\n"
            "📂 اختر القائمة الرئيسية:"
        )

    else:

        menus = connection.execute(

            """
            SELECT
                id,
                name,
                parent_id

            FROM menus

            WHERE parent_id = ?

            ORDER BY
                display_order ASC,
                id ASC
            """,

            (parent_id,)
        ).fetchall()

        parent = connection.execute(

            """
            SELECT name
            FROM menus
            WHERE id = ?
            """,

            (parent_id,)
        ).fetchone()

        parent_name = (
            parent["name"]
            if parent
            else ""
        )

        title = (

            "➕ إضافة محتوى\n\n"

            f"📂 داخل: {parent_name}\n\n"

            "اختر القائمة التي تريد إضافة "
            "المحتوى إليها:"
        )

    connection.close()

    rows = []

    for menu in menus:

        rows.append([
            f"📂 {menu['name']}"
        ])

    rows.append([
        "📌 إضافة هنا"
    ])

    rows.append([
        "◀️ رجوع"
    ])

    await update.message.reply_text(

        title,

        reply_markup=make_simple_keyboard(
            rows
        )
    )

    context.user_data[
        "content_selector_parent_id"
    ] = parent_id


# ==========================================================
# لوحة بسيطة داخل main.py
# ==========================================================

def make_simple_keyboard(rows):

    from telegram import ReplyKeyboardMarkup, KeyboardButton

    buttons = []

    for row in rows:

        buttons.append([
            KeyboardButton(text)
            for text in row
        ])

    return ReplyKeyboardMarkup(
        buttons,
        resize_keyboard=True,
        one_time_keyboard=False,
        is_persistent=True,
    )


# ==========================================================
# اختيار القائمة الحالية لإضافة المحتوى
# ==========================================================

async def choose_content_target(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    parent_id = context.user_data.get(
        "content_selector_parent_id"
    )

    text = update.message.text.strip()

    if text == "📌 إضافة هنا":

        if not parent_id:

            await update.message.reply_text(
                "❌ يجب اختيار قائمة أولًا."
            )

            return

        context.user_data[
            "content_menu_id"
        ] = parent_id

        context.user_data[
            "state"
        ] = "select_content_type"

        await update.message.reply_text(

            "📦 اختر نوع المحتوى:",

            reply_markup=content_type_keyboard()
        )

        return

    if text.startswith("📂 "):

        menu_name = text[3:].strip()

        menu = find_menu_by_name(
            menu_name,
            parent_id
        )

        if not menu:

            await update.message.reply_text(
                "❌ لم يتم العثور على القائمة."
            )

            return

        # ----------------------------------------------
        # أصبح هذا هو المكان الحالي
        # ----------------------------------------------

        context.user_data[
            "content_selector_parent_id"
        ] = menu["id"]

        await show_content_menu_selector(

            update,
            context,
            menu["id"]
        )

        return


# ==========================================================
# اختيار نوع المحتوى
# ==========================================================

async def choose_content_type(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = update.message.text.strip()

    types = {

        "📝 نص": "text",

        "📄 ملف / PDF": "document",

        "🖼️ صورة": "photo",

        "🎬 فيديو": "video",

        "🎧 صوت": "audio",

        "🎤 رسالة صوتية": "voice",

        "🔗 رابط": "url",
    }

    content_type = types.get(
        text
    )

    if not content_type:

        return

    context.user_data[
        "content_type"
    ] = content_type

    context.user_data[
        "state"
    ] = "enter_content_title"

    await update.message.reply_text(

        "✏️ اكتب عنوان المحتوى:\n\n"

        "مثال:\n"
        "الدرس الأول\n"
        "ملزمة الطهارة\n"
        "محاضرة رمضان",

        reply_markup=cancel_keyboard()
    )


# ==========================================================
# حفظ عنوان المحتوى
# ==========================================================

async def save_content_title(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    title = update.message.text.strip()

    if not title:

        await update.message.reply_text(
            "❌ العنوان لا يمكن أن يكون فارغًا."
        )

        return

    content_menu_id = context.user_data.get(
        "content_menu_id"
    )

    content_type = context.user_data.get(
        "content_type"
    )

    if not content_menu_id or not content_type:

        context.user_data.clear()

        await update.message.reply_text(
            "❌ حدث خطأ في بيانات المحتوى."
        )

        return

    context.user_data[
        "content_title"
    ] = title

    context.user_data[
        "state"
    ] = "waiting_content"

    instructions = {

        "text":
            "📝 أرسل الآن النص الذي تريد حفظه.",

        "document":
            "📄 أرسل الآن ملف PDF أو أي ملف.",

        "photo":
            "🖼️ أرسل الآن الصورة.",

        "video":
            "🎬 أرسل الآن الفيديو.",

        "audio":
            "🎧 أرسل الآن الملف الصوتي.",

        "voice":
            "🎤 أرسل الآن الرسالة الصوتية.",

        "url":
            "🔗 أرسل الآن الرابط."
    }

    await update.message.reply_text(

        instructions.get(
            content_type,
            "📦 أرسل المحتوى الآن."
        ),

        reply_markup=cancel_keyboard()
    )


# ==========================================================
# حفظ المحتوى
# ==========================================================

async def save_content(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    content_menu_id = context.user_data.get(
        "content_menu_id"
    )

    content_type = context.user_data.get(
        "content_type"
    )

    title = context.user_data.get(
        "content_title"
    )

    if not content_menu_id or not content_type or not title:

        context.user_data.clear()

        await update.message.reply_text(
            "❌ بيانات المحتوى غير مكتملة."
        )

        return

    text_content = None

    file_id = None

    url = None

    message = update.message

    # ------------------------------------------------------
    # النص
    # ------------------------------------------------------

    if content_type == "text":

        if not message.text:

            await update.message.reply_text(
                "❌ أرسل نصًا فقط."
            )

            return

        text_content = message.text

    # ------------------------------------------------------
    # الرابط
    # ------------------------------------------------------

    elif content_type == "url":

        if not message.text:

            await update.message.reply_text(
                "❌ أرسل الرابط كنص."
            )

            return

        url = message.text.strip()

        if not (
            url.startswith("http://")
            or
            url.startswith("https://")
        ):

            await update.message.reply_text(

                "❌ الرابط يجب أن يبدأ بـ:\n"
                "http:// أو https://"
            )

            return

    # ------------------------------------------------------
    # الملف
    # ------------------------------------------------------

    elif content_type == "document":

        if not message.document:

            await update.message.reply_text(
                "❌ أرسل ملفًا أو PDF."
            )

            return

        file_id = message.document.file_id

    # ------------------------------------------------------
    # الصورة
    # ------------------------------------------------------

    elif content_type == "photo":

        if not message.photo:

            await update.message.reply_text(
                "❌ أرسل صورة."
            )

            return

        file_id = message.photo[-1].file_id

    # ------------------------------------------------------
    # الفيديو
    # ------------------------------------------------------

    elif content_type == "video":

        if not message.video:

            await update.message.reply_text(
                "❌ أرسل فيديو."
            )

            return

        file_id = message.video.file_id

    # ------------------------------------------------------
    # الصوت
    # ------------------------------------------------------

    elif content_type == "audio":

        if not message.audio:

            await update.message.reply_text(
                "❌ أرسل ملفًا صوتيًا."
            )

            return

        file_id = message.audio.file_id

    # ------------------------------------------------------
    # الرسالة الصوتية
    # ------------------------------------------------------

    elif content_type == "voice":

        if not message.voice:

            await update.message.reply_text(
                "❌ أرسل رسالة صوتية."
            )

            return

        file_id = message.voice.file_id

    else:

        await update.message.reply_text(
            "❌ نوع محتوى غير معروف."
        )

        return

    # ======================================================
    # حفظ المحتوى في قاعدة البيانات
    # ======================================================

    connection = get_connection()

    order_row = connection.execute(

        """
        SELECT COALESCE(
            MAX(display_order), 0
        ) + 1 AS next_order

        FROM contents

        WHERE menu_id = ?
        """,

        (content_menu_id,)
    ).fetchone()

    next_order = order_row[
        "next_order"
    ]

    connection.execute(

        """
        INSERT INTO contents (
            menu_id,
            title,
            content_type,
            text_content,
            file_id,
            url,
            display_order
        )

        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,

        (
            content_menu_id,
            title,
            content_type,
            text_content,
            file_id,
            url,
            next_order
        )
    )

    connection.commit()

    connection.close()

    # ======================================================
    # النجاح
    # ======================================================

    context.user_data.clear()

    await update.message.reply_text(

        "✅ تم حفظ المحتوى بنجاح.\n\n"

        f"📌 العنوان: {title}\n"
        f"📦 النوع: {content_type_icon(content_type)}"
    )

    await show_admin_panel(
        update,
        context
    )


# ==========================================================
# فتح قائمة عامة للمستخدم
# ==========================================================

async def open_public_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    menu_id
):

    connection = get_connection()

    menu = connection.execute(

        """
        SELECT
            id,
            name,
            parent_id

        FROM menus

        WHERE id = ?
        """,

        (menu_id,)
    ).fetchone()

    if not menu:

        connection.close()

        await update.message.reply_text(
            "❌ القسم غير موجود."
        )

        return

    children = connection.execute(

        """
        SELECT
            id,
            name,
            display_order

        FROM menus

        WHERE parent_id = ?

        ORDER BY
            display_order ASC,
            id ASC
        """,

        (menu_id,)
    ).fetchall()

    contents = connection.execute(

        """
        SELECT
            id,
            title,
            content_type,
            text_content,
            file_id,
            url,
            display_order

        FROM contents

        WHERE menu_id = ?

        ORDER BY
            display_order ASC,
            id ASC
        """,

        (menu_id,)
    ).fetchall()

    connection.close()

    context.user_data[
        "public_menu_id"
    ] = menu["id"]

    context.user_data[
        "public_parent_id"
    ] = menu["parent_id"]

    await update.message.reply_text(

        f"📂 {menu['name']}\n\n"
        "اختر من القائمة:",

        reply_markup=public_menu_keyboard(
            children,
            contents
        )
    )


# ==========================================================
# فتح قائمة رئيسية من الواجهة العامة
# ==========================================================

async def open_public_root_by_name(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    menu_name
):

    menu = find_menu_by_name(
        menu_name
    )

    if not menu:

        await update.message.reply_text(
            "ℹ️ هذا القسم لم يتم تجهيزه بعد."
        )

        return

    await open_public_menu(

        update,
        context,
        menu["id"]
    )


# ==========================================================
# عرض محتوى للمستخدم
# ==========================================================

async def send_public_content(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    content
):

    content_type = content[
        "content_type"
    ]

    # ------------------------------------------------------
    # النص
    # ------------------------------------------------------

    if content_type == "text":

        await update.message.reply_text(
            content["text_content"] or ""
        )

        return

    # ------------------------------------------------------
    # الملف
    # ------------------------------------------------------

    if content_type == "document":

        await update.message.reply_document(
            document=content["file_id"],
            caption=content["title"]
        )

        return

    # ------------------------------------------------------
    # الصورة
    # ------------------------------------------------------

    if content_type == "photo":

        await update.message.reply_photo(
            photo=content["file_id"],
            caption=content["title"]
        )

        return

    # ------------------------------------------------------
    # الفيديو
    # ------------------------------------------------------

    if content_type == "video":

        await update.message.reply_video(
            video=content["file_id"],
            caption=content["title"]
        )

        return

    # ------------------------------------------------------
    # الصوت
    # ------------------------------------------------------

    if content_type == "audio":

        await update.message.reply_audio(
            audio=content["file_id"],
            caption=content["title"]
        )

        return

    # ------------------------------------------------------
    # الرسالة الصوتية
    # ------------------------------------------------------

    if content_type == "voice":

        await update.message.reply_voice(
            voice=content["file_id"]
        )

        return

    # ------------------------------------------------------
    # الرابط
    # ------------------------------------------------------

    if content_type == "url":

        await update.message.reply_text(
            f"🔗 {content['title']}\n\n"
            f"{content['url']}"
        )

        return


# ==========================================================
# الرجوع في الواجهة العامة
# ==========================================================

async def go_back_public(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    current_id = context.user_data.get(
        "public_menu_id"
    )

    if not current_id:

        await show_public_home(
            update,
            context
        )

        return

    connection = get_connection()

    menu = connection.execute(

        """
        SELECT
            id,
            parent_id

        FROM menus

        WHERE id = ?
        """,

        (current_id,)
    ).fetchone()

    connection.close()

    if not menu:

        await show_public_home(
            update,
            context
        )

        return

    parent_id = menu[
        "parent_id"
    ]

    if parent_id is None:

        await show_public_home(
            update,
            context
        )

        return

    await open_public_menu(

        update,
        context,
        parent_id
    )


# ==========================================================
# الرجوع في الإدارة
# ==========================================================

async def go_back_admin(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    parent_id = context.user_data.get(
        "current_parent_id"
    )

    if parent_id:

        await open_menu(
            update,
            context,
            parent_id
        )

        return

    context.user_data.clear()

    await show_menus(
        update,
        context
    )


# ==========================================================
# إلغاء
# ==========================================================

async def cancel_action(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data.clear()

    await update.message.reply_text(

        "❌ تم إلغاء العملية.",

        reply_markup=admin_keyboard()
    )


# ==========================================================
# استقبال الرسائل
# ==========================================================

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    user = update.effective_user

    if not user:
        return

    register_user(user)

    text = (
        update.message.text.strip()
        if update.message.text
        else ""
    )

    user_id = user.id

    state = context.user_data.get(
        "state"
    )

    # ======================================================
    # إلغاء
    # ======================================================

    if text == "❌ إلغاء":

        await cancel_action(
            update,
            context
        )

        return

    # ======================================================
    # إنشاء قائمة
    # ======================================================

    if state in [

        "creating_main_menu",
        "creating_submenu"

    ]:

        await save_new_menu(
            update,
            context
        )

        return

    # ======================================================
    # اختيار مكان إضافة المحتوى
    # ======================================================

    if state == "select_content_menu":

        await choose_content_target(
            update,
            context
        )

        return

    # ======================================================
    # اختيار نوع المحتوى
    # ======================================================

    if state == "select_content_type":

        await choose_content_type(
            update,
            context
        )

        return

    # ======================================================
    # عنوان المحتوى
    # ======================================================

    if state == "enter_content_title":

        await save_content_title(
            update,
            context
        )

        return

    # ======================================================
    # استقبال المحتوى
    # ======================================================

    if state == "waiting_content":

        await save_content(
            update,
            context
        )

        return

    # ======================================================
    # الإدارة
    # ======================================================

    if text == "⚙️ الإدارة":

        await show_admin_panel(
            update,
            context
        )

        return

    # ======================================================
    # واجهة المستخدم
    # ======================================================

    if text == "👤 واجهة المستخدم":

        await show_public_home(
            update,
            context
        )

        return

    # ======================================================
    # إدارة القوائم
    # ======================================================

    if text == "📂 إدارة القوائم":

        await show_menus(
            update,
            context
        )

        return

    # ======================================================
    # إنشاء قائمة رئيسية
    # ======================================================

    if text == "➕ إنشاء قائمة رئيسية":

        await create_main_menu_start(
            update,
            context
        )

        return

    # ======================================================
    # إنشاء قائمة فرعية
    # ======================================================

    if text == "➕ إنشاء قائمة فرعية":

        await create_submenu_start(
            update,
            context
        )

        return

    # ======================================================
    # إضافة محتوى
    # ======================================================

    if text == "➕ إضافة محتوى":

        if not is_admin(user_id):

            return

        await start_add_content(
            update,
            context
        )

        return

    # ======================================================
    # الرجوع
    # ======================================================

    if text == "◀️ رجوع":

        # --------------------------------------------------
        # واجهة المستخدم
        # --------------------------------------------------

        if context.user_data.get(
            "public_menu_id"
        ):

            await go_back_public(
                update,
                context
            )

            return

        # --------------------------------------------------
        # اختيار مكان المحتوى
        # --------------------------------------------------

        if state == "select_content_menu":

            parent_id = context.user_data.get(
                "content_selector_parent_id"
            )

            if parent_id:

                connection = get_connection()

                parent = connection.execute(

                    """
                    SELECT parent_id
                    FROM menus
                    WHERE id = ?
                    """,

                    (parent_id,)
                ).fetchone()

                connection.close()

                if parent and parent["parent_id"]:

                    await show_content_menu_selector(

                        update,
                        context,
                        parent["parent_id"]
                    )

                    return

            context.user_data.clear()

            await show_admin_panel(
                update,
                context
            )

            return

        # --------------------------------------------------
        # إدارة المشرف
        # --------------------------------------------------

        if is_admin(user_id):

            if context.user_data.get(
                "current_menu_id"
            ):

                await go_back_admin(
                    update,
                    context
                )

            else:

                context.user_data.clear()

                await show_admin_panel(
                    update,
                    context
                )

        return

    # ======================================================
    # فتح قائمة للمشرف
    # ======================================================

    if text.startswith("📂 "):

        if not is_admin(user_id):

            return

        menu_name = text[3:].strip()

        current_menu_id = context.user_data.get(
            "current_menu_id"
        )

        if current_menu_id:

            menu = find_menu_by_name(
                menu_name,
                current_menu_id
            )

        else:

            menu = find_menu_by_name(
                menu_name
            )

        if menu:

            await open_menu(
                update,
                context,
                menu["id"]
            )

        else:

            await update.message.reply_text(
                "❌ لم يتم العثور على القائمة."
            )

        return

    # ======================================================
    # القوائم العامة الرئيسية
    # ======================================================

    if text == "📖 القرآن والثقافة":

        await open_public_root_by_name(

            update,
            context,
            "القرآن والثقافة"
        )

        return

    if text == "📚 الملازم":

        await open_public_root_by_name(

            update,
            context,
            "الملازم"
        )

        return

    if text == "🎧 المحاضرات":

        await open_public_root_by_name(

            update,
            context,
            "المحاضرات"
        )

        return

    # ======================================================
    # عن البوت
    # ======================================================

    if text == "ℹ️ عن البوت":

        await update.message.reply_text(

            "🌿 هدى للناس\n\n"
            "منصة Telegram لتنظيم وعرض المحتوى."
        )

        return

    # ======================================================
    # فتح قائمة فرعية أو محتوى للمستخدم
    # ======================================================

    public_menu_id = context.user_data.get(
        "public_menu_id"
    )

    if public_menu_id:

        # --------------------------------------------------
        # قائمة فرعية
        # --------------------------------------------------

        if text.startswith("📂 "):

            menu_name = text[3:].strip()

            menu = find_menu_by_name(

                menu_name,
                public_menu_id
            )

            if menu:

                await open_public_menu(

                    update,
                    context,
                    menu["id"]
                )

                return

        # --------------------------------------------------
        # محتوى
        # --------------------------------------------------

        connection = get_connection()

        contents = connection.execute(

            """
            SELECT
                id,
                title,
                content_type,
                text_content,
                file_id,
                url,
                display_order

            FROM contents

            WHERE menu_id = ?

            ORDER BY
                display_order ASC,
                id ASC
            """,

            (public_menu_id,)
        ).fetchall()

        connection.close()

        for content in contents:

            icon = content_type_icon(
                content["content_type"]
            )

            expected_text = (
                f"{icon} {content['title']}"
            )

            if text == expected_text:

                await send_public_content(

                    update,
                    context,
                    content
                )

                return

        return

    # ======================================================
    # وظائف الإدارة غير المفعلة
    # ======================================================

    if text == "✏️ تعديل المحتوى":

        if not is_admin(user_id):
            return

        await update.message.reply_text(

            "✏️ تعديل المحتوى\n\n"
            "سيتم تفعيل هذه الوظيفة بعد اكتمال نظام الإضافة."
        )

        return

    if text == "🗑️ حذف المحتوى":

        if not is_admin(user_id):
            return

        await update.message.reply_text(

            "🗑️ حذف المحتوى\n\n"
            "سيتم تفعيلها لاحقًا."
        )

        return

    if text == "↕️ ترتيب العناصر":

        if not is_admin(user_id):
            return

        await update.message.reply_text(

            "↕️ ترتيب العناصر\n\n"
            "سيتم تفعيلها لاحقًا."
        )

        return

    if text == "👥 المشرفون":

        if not is_admin(user_id):
            return

        await update.message.reply_text(

            "👥 المشرفون\n\n"
            "سيتم تفعيلها لاحقًا."
        )

        return

    if text == "📊 الإحصائيات":

        if not is_admin(user_id):
            return

        await update.message.reply_text(

            "📊 الإحصائيات\n\n"
            "سيتم تفعيلها لاحقًا."
        )

        return


# ==========================================================
# تشغيل البوت
# ==========================================================

def main():

    print(
        "========================================",
        flush=True
    )

    print(
        "🌿 Huda People Bot is starting...",
        flush=True
    )

    print(
        "========================================",
        flush=True
    )

    initialize_database()

    ensure_admin(
        int(ADMIN_ID)
    )

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    application.add_handler(
        CommandHandler(
            "admin",
            admin_command
        )
    )

    application.add_handler(
        MessageHandler(
            filters.ALL & ~filters.COMMAND,
            handle_message
        )
    )

    print(
        "========================================",
        flush=True
    )

    print(
        "✅ Huda People Bot is running...",
        flush=True
    )

    print(
        "========================================",
        flush=True
    )

    application.run_polling(
        drop_pending_updates=False
    )


# ==========================================================
# نقطة تشغيل البرنامج
# ==========================================================

if __name__ == "__main__":

    main()
