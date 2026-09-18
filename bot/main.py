import os

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from bot.database import (
    initialize_database,
    register_user,
    ensure_admin,
    is_admin,
    get_connection,
    get_stats,
)

from bot.keyboards import (
    user_keyboard,
    admin_keyboard,
    menus_keyboard,
    admin_menu_keyboard,
    public_menu_keyboard,
    content_type_keyboard,
    cancel_keyboard,
)


# ==========================================================
# الإعدادات
# ==========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")


# ==========================================================
# أدوات مساعدة
# ==========================================================

def get_menu(menu_id):

    connection = get_connection()

    row = connection.execute(
        """
        SELECT *
        FROM menus
        WHERE id = ?
        """,
        (menu_id,)
    ).fetchone()

    connection.close()

    return row


def get_main_menus():

    connection = get_connection()

    rows = connection.execute(
        """
        SELECT *
        FROM menus
        WHERE parent_id IS NULL
        ORDER BY display_order, id
        """
    ).fetchall()

    connection.close()

    return rows


def get_menu_contents(menu_id):

    connection = get_connection()

    rows = connection.execute(
        """
        SELECT *
        FROM contents
        WHERE menu_id = ?
        ORDER BY display_order, id
        """,
        (menu_id,)
    ).fetchall()

    connection.close()

    return rows


# ==========================================================
# /start
# ==========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data.clear()

    user = update.effective_user

    register_user(user)

    admin_user = is_admin(user.id)

    await update.message.reply_text(
        "🌿 أهلاً وسهلاً بك في بوت هدى للناس\n\n"
        "اختر من القائمة:",
        reply_markup=user_keyboard(admin_user),
    )


# ==========================================================
# واجهة الإدارة
# ==========================================================

async def show_admin_panel(update, context):

    context.user_data.clear()

    await update.message.reply_text(
        "⚙️ لوحة الإدارة\n\n"
        "اختر العملية المطلوبة:",
        reply_markup=admin_keyboard(),
    )


# ==========================================================
# إدارة القوائم
# ==========================================================

async def show_menus(update, context):

    context.user_data.clear()

    menus = get_main_menus()

    await update.message.reply_text(
        "📂 إدارة القوائم الرئيسية\n\n"
        "اختر قائمة لفتحها:",
        reply_markup=menus_keyboard(menus),
    )


# ==========================================================
# إنشاء قائمة رئيسية
# ==========================================================

async def create_main_menu_start(update, context):

    context.user_data.clear()

    context.user_data["state"] = "create_main_menu"

    await update.message.reply_text(
        "➕ إنشاء قائمة رئيسية\n\n"
        "أرسل اسم القائمة:",
        reply_markup=cancel_keyboard(),
    )


# ==========================================================
# حفظ القائمة الرئيسية
# ==========================================================

async def save_main_menu(update, context):

    name = update.message.text.strip()

    if not name:
        await update.message.reply_text(
            "⚠️ اسم القائمة لا يمكن أن يكون فارغاً."
        )
        return

    if name in [
        "◀️ رجوع",
        "❌ إلغاء",
        "➕ إنشاء قائمة رئيسية",
        "➕ إضافة محتوى",
    ]:
        await update.message.reply_text(
            "⚠️ هذا اسم محجوز لأحد أزرار النظام.\n"
            "اختر اسماً مختلفاً."
        )
        return

    connection = get_connection()

    max_order = connection.execute(
        """
        SELECT COALESCE(MAX(display_order), 0)
        FROM menus
        WHERE parent_id IS NULL
        """
    ).fetchone()[0]

    connection.execute(
        """
        INSERT INTO menus (
            name,
            parent_id,
            display_order
        )
        VALUES (?, NULL, ?)
        """,
        (
            name,
            max_order + 1,
        )
    )

    connection.commit()
    connection.close()

    context.user_data.clear()

    menus = get_main_menus()

    await update.message.reply_text(
        f"✅ تم إنشاء القائمة الرئيسية:\n\n"
        f"📂 {name}",
        reply_markup=menus_keyboard(menus),
    )


# ==========================================================
# فتح قائمة رئيسية للمشرف
# ==========================================================

async def open_admin_menu(update, context, menu_name):

    menus = get_main_menus()

    menu = None

    for item in menus:

        if item["name"] == menu_name:
            menu = item
            break

    if menu is None:

        await update.message.reply_text(
            "⚠️ لم يتم العثور على القائمة."
        )

        return

    menu_id = menu["id"]

    context.user_data.clear()

    context.user_data["current_menu_id"] = menu_id
    context.user_data["current_menu_name"] = menu["name"]
    context.user_data["mode"] = "admin_menu"

    contents = get_menu_contents(menu_id)

    await update.message.reply_text(
        f"📂 القائمة: {menu['name']}\n\n"
        f"يمكنك الآن إضافة المحتوى داخل هذه القائمة.",
        reply_markup=admin_menu_keyboard(contents),
    )


# ==========================================================
# إضافة محتوى داخل القائمة الحالية
# ==========================================================

async def start_add_content(update, context):

    menu_id = context.user_data.get("current_menu_id")

    if not menu_id:

        await update.message.reply_text(
            "⚠️ يجب فتح القائمة أولاً ثم اختيار "
            "«➕ إضافة محتوى»."
        )

        return

    context.user_data["state"] = "select_content_type"

    await update.message.reply_text(
        "➕ إضافة محتوى\n\n"
        "اختر نوع المحتوى:",
        reply_markup=content_type_keyboard(),
    )


# ==========================================================
# اختيار نوع المحتوى
# ==========================================================

async def choose_content_type(update, context):

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

    content_type = types.get(text)

    if not content_type:

        await update.message.reply_text(
            "⚠️ اختر نوع المحتوى من الأزرار."
        )

        return

    context.user_data["content_type"] = content_type
    context.user_data["state"] = "enter_content_title"

    await update.message.reply_text(
        "✏️ أرسل عنوان المحتوى:"
    )


# ==========================================================
# إدخال عنوان المحتوى
# ==========================================================

async def save_content_title(update, context):

    title = update.message.text.strip()

    if not title:

        await update.message.reply_text(
            "⚠️ العنوان لا يمكن أن يكون فارغاً."
        )

        return

    context.user_data["content_title"] = title
    context.user_data["state"] = "waiting_content"

    content_type = context.user_data["content_type"]

    messages = {

        "text":
            "📝 أرسل النص الآن.",

        "document":
            "📄 أرسل الملف أو PDF الآن.",

        "photo":
            "🖼️ أرسل الصورة الآن.",

        "video":
            "🎬 أرسل الفيديو الآن.",

        "audio":
            "🎧 أرسل الملف الصوتي الآن.",

        "voice":
            "🎤 أرسل الرسالة الصوتية الآن.",

        "url":
            "🔗 أرسل الرابط الآن.",
    }

    await update.message.reply_text(
        messages.get(
            content_type,
            "أرسل المحتوى الآن."
        ),
        reply_markup=cancel_keyboard(),
    )


# ==========================================================
# حفظ المحتوى
# ==========================================================

async def save_content(update, context):

    menu_id = context.user_data.get("current_menu_id")
    content_type = context.user_data.get("content_type")
    title = context.user_data.get("content_title")

    if not menu_id or not content_type or not title:

        await update.message.reply_text(
            "⚠️ حدث خطأ في بيانات المحتوى."
        )

        return

    text_content = None
    file_id = None
    url = None

    message = update.message

    if content_type == "text":

        text_content = message.text

    elif content_type == "document":

        if not message.document:
            await update.message.reply_text(
                "⚠️ أرسل ملفاً أو PDF."
            )
            return

        file_id = message.document.file_id

    elif content_type == "photo":

        if not message.photo:
            await update.message.reply_text(
                "⚠️ أرسل صورة."
            )
            return

        file_id = message.photo[-1].file_id

    elif content_type == "video":

        if not message.video:
            await update.message.reply_text(
                "⚠️ أرسل فيديو."
            )
            return

        file_id = message.video.file_id

    elif content_type == "audio":

        if not message.audio:
            await update.message.reply_text(
                "⚠️ أرسل ملفاً صوتياً."
            )
            return

        file_id = message.audio.file_id

    elif content_type == "voice":

        if not message.voice:
            await update.message.reply_text(
                "⚠️ أرسل رسالة صوتية."
            )
            return

        file_id = message.voice.file_id

    elif content_type == "url":

        if not message.text:

            await update.message.reply_text(
                "⚠️ أرسل الرابط كنص."
            )

            return

        url = message.text.strip()

    connection = get_connection()

    max_order = connection.execute(
        """
        SELECT COALESCE(MAX(display_order), 0)
        FROM contents
        WHERE menu_id = ?
        """,
        (menu_id,)
    ).fetchone()[0]

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
            menu_id,
            title,
            content_type,
            text_content,
            file_id,
            url,
            max_order + 1,
        )
    )

    connection.commit()
    connection.close()

    menu = get_menu(menu_id)

    context.user_data.clear()

    context.user_data["current_menu_id"] = menu_id
    context.user_data["current_menu_name"] = menu["name"]
    context.user_data["mode"] = "admin_menu"

    contents = get_menu_contents(menu_id)

    await update.message.reply_text(
        f"✅ تم إضافة المحتوى بنجاح.\n\n"
        f"📂 القائمة: {menu['name']}",
        reply_markup=admin_menu_keyboard(contents),
    )


# ==========================================================
# إلغاء العملية
# ==========================================================

async def cancel_action(update, context):

    menu_id = context.user_data.get("current_menu_id")

    if menu_id:

        menu = get_menu(menu_id)

        if menu:

            contents = get_menu_contents(menu_id)

            context.user_data.clear()

            context.user_data["current_menu_id"] = menu_id
            context.user_data["current_menu_name"] = menu["name"]
            context.user_data["mode"] = "admin_menu"

            await update.message.reply_text(
                f"📂 القائمة: {menu['name']}",
                reply_markup=admin_menu_keyboard(contents),
            )

            return

    context.user_data.clear()

    await update.message.reply_text(
        "تم إلغاء العملية.",
        reply_markup=user_keyboard(
            is_admin(update.effective_user.id)
        ),
    )


# ==========================================================
# الرجوع من قائمة الإدارة
# ==========================================================

async def go_back_admin(update, context):

    context.user_data.clear()

    menus = get_main_menus()

    await update.message.reply_text(
        "📂 إدارة القوائم الرئيسية:",
        reply_markup=menus_keyboard(menus),
    )


# ==========================================================
# فتح القائمة العامة
# ==========================================================

async def open_public_menu(update, context, menu_name):

    menus = get_main_menus()

    menu = None

    for item in menus:

        if item["name"] == menu_name:

            menu = item
            break

    if menu is None:

        await update.message.reply_text(
            "⚠️ لم يتم العثور على القائمة."
        )

        return

    menu_id = menu["id"]

    context.user_data.clear()

    context.user_data["public_menu_id"] = menu_id
    context.user_data["mode"] = "public_menu"

    contents = get_menu_contents(menu_id)

    await update.message.reply_text(
        f"📂 {menu['name']}",
        reply_markup=public_menu_keyboard(contents),
    )


# ==========================================================
# عرض المحتوى للمستخدم
# ==========================================================

async def send_public_content(update, menu_id, title):

    connection = get_connection()

    content = connection.execute(
        """
        SELECT *
        FROM contents
        WHERE menu_id = ?
        AND title = ?
        LIMIT 1
        """,
        (
            menu_id,
            title,
        )
    ).fetchone()

    connection.close()

    if not content:

        await update.message.reply_text(
            "⚠️ لم يتم العثور على المحتوى."
        )

        return

    content_type = content["content_type"]

    if content_type == "text":

        await update.message.reply_text(
            content["text_content"] or ""
        )

    elif content_type == "document":

        await update.message.reply_document(
            content["file_id"],
            caption=content["title"],
        )

    elif content_type == "photo":

        await update.message.reply_photo(
            content["file_id"],
            caption=content["title"],
        )

    elif content_type == "video":

        await update.message.reply_video(
            content["file_id"],
            caption=content["title"],
        )

    elif content_type == "audio":

        await update.message.reply_audio(
            content["file_id"],
            caption=content["title"],
        )

    elif content_type == "voice":

        await update.message.reply_voice(
            content["file_id"]
        )

    elif content_type == "url":

        await update.message.reply_text(
            f"🔗 {content['url']}"
        )


# ==========================================================
# الرجوع من القائمة العامة
# ==========================================================

async def go_back_public(update, context):

    context.user_data.clear()

    await update.message.reply_text(
        "🌿 القائمة الرئيسية:",
        reply_markup=user_keyboard(
            is_admin(update.effective_user.id)
        ),
    )


# ==========================================================
# الإحصائيات
# ==========================================================

async def show_statistics(update, context):

    users, menus, contents, admins = get_stats()

    await update.message.reply_text(
        "📊 الإحصائيات\n\n"
        f"👥 المستخدمون: {users}\n"
        f"📂 القوائم الرئيسية: {menus}\n"
        f"📄 المحتويات: {contents}\n"
        f"⚙️ المشرفون: {admins}"
    )


# ==========================================================
# واجهة المستخدم
# ==========================================================

async def show_user_interface(update, context):

    context.user_data.clear()

    await update.message.reply_text(
        "👤 واجهة المستخدم",
        reply_markup=user_keyboard(
            is_admin(update.effective_user.id)
        ),
    )


# ==========================================================
# معالجة الرسائل
# ==========================================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message or not update.message.text:

        # السماح بحفظ الملفات والوسائط أثناء إدخال المحتوى
        state = context.user_data.get("state")

        if state == "waiting_content":

            if is_admin(update.effective_user.id):

                await save_content(
                    update,
                    context
                )

        return

    text = update.message.text.strip()

    user_id = update.effective_user.id

    admin_user = is_admin(user_id)

    state = context.user_data.get("state")
    mode = context.user_data.get("mode")

    # ======================================================
    # الإلغاء
    # ======================================================

    if text == "❌ إلغاء":

        await cancel_action(
            update,
            context
        )

        return

    # ======================================================
    # الرجوع
    # ======================================================

    if text == "◀️ رجوع":

        if state in [
            "create_main_menu",
            "select_content_type",
            "enter_content_title",
            "waiting_content",
        ]:

            if context.user_data.get("current_menu_id"):

                menu_id = context.user_data["current_menu_id"]

                menu = get_menu(menu_id)

                if menu:

                    contents = get_menu_contents(menu_id)

                    context.user_data.clear()

                    context.user_data["current_menu_id"] = menu_id
                    context.user_data["current_menu_name"] = menu["name"]
                    context.user_data["mode"] = "admin_menu"

                    await update.message.reply_text(
                        f"📂 القائمة: {menu['name']}",
                        reply_markup=admin_menu_keyboard(contents),
                    )

                    return

            await show_admin_panel(
                update,
                context
            )

            return

        if mode == "admin_menu":

            await go_back_admin(
                update,
                context
            )

            return

        if mode == "public_menu":

            await go_back_public(
                update,
                context
            )

            return

        await start(
            update,
            context
        )

        return

    # ======================================================
    # حالات إدخال البيانات
    # ======================================================

    if admin_user and state == "create_main_menu":

        await save_main_menu(
            update,
            context
        )

        return

    if admin_user and state == "select_content_type":

        await choose_content_type(
            update,
            context
        )

        return

    if admin_user and state == "enter_content_title":

        await save_content_title(
            update,
            context
        )

        return

    if admin_user and state == "waiting_content":

        await save_content(
            update,
            context
        )

        return

    # ======================================================
    # القائمة الرئيسية للمستخدم
    # ======================================================

    if text in [
        "📖 القرآن والثقافة",
        "📚 الملازم",
        "🎧 المحاضرات",
        "ℹ️ عن البوت",
    ]:

        await open_public_menu(
            update,
            context,
            text[2:].strip()
        )

        return

    # ======================================================
    # زر الإدارة
    # ======================================================

    if text == "⚙️ الإدارة":

        if not admin_user:

            await update.message.reply_text(
                "⚠️ هذا القسم مخصص للمشرفين فقط."
            )

            return

        await show_admin_panel(
            update,
            context
        )

        return

    # ======================================================
    # إدارة القوائم
    # ======================================================

    if text == "📂 إدارة القوائم":

        if not admin_user:

            return

        await show_menus(
            update,
            context
        )

        return

    # ======================================================
    # إنشاء قائمة رئيسية
    # ======================================================

    if text == "➕ إنشاء قائمة رئيسية":

        if not admin_user:

            return

        await create_main_menu_start(
            update,
            context
        )

        return

    # ======================================================
    # فتح قائمة رئيسية للمشرف
    # ======================================================

    if admin_user and text.startswith("📂 "):

        menu_name = text.removeprefix(
            "📂 "
        ).strip()

        await open_admin_menu(
            update,
            context,
            menu_name
        )

        return

    # ======================================================
    # إضافة محتوى داخل القائمة الحالية
    # ======================================================

    if text == "➕ إضافة محتوى":

        if not admin_user:

            return

        await start_add_content(
            update,
            context
        )

        return

    # ======================================================
    # الإحصائيات
    # ======================================================

    if text == "📊 الإحصائيات":

        if not admin_user:

            return

        await show_statistics(
            update,
            context
        )

        return

    # ======================================================
    # واجهة المستخدم
    # ======================================================

    if text == "👤 واجهة المستخدم":

        if not admin_user:

            return

        await show_user_interface(
            update,
            context
        )

        return

    # ======================================================
    # محتوى داخل القائمة العامة
    # ======================================================

    public_menu_id = context.user_data.get(
        "public_menu_id"
    )

    if public_menu_id and mode == "public_menu":

        contents = get_menu_contents(
            public_menu_id
        )

        for content in contents:

            icon = {
                "text": "📝",
                "document": "📄",
                "photo": "🖼️",
                "video": "🎬",
                "audio": "🎧",
                "voice": "🎤",
                "url": "🔗",
            }.get(
                content["content_type"],
                "📄"
            )

            if text == f"{icon} {content['title']}":

                await send_public_content(
                    update,
                    public_menu_id,
                    content["title"]
                )

                return

    # ======================================================
    # المستخدم العادي يضغط قائمة 📂
    # ======================================================

    if text.startswith("📂 ") and not admin_user:

        menu_name = text.removeprefix(
            "📂 "
        ).strip()

        await open_public_menu(
            update,
            context,
            menu_name
        )

        return

    # ======================================================
    # رسالة غير معروفة
    # ======================================================

    await update.message.reply_text(
        "⚠️ لم أفهم الأمر.\n"
        "اختر أحد الأزرار الموجودة أمامك."
    )


# ==========================================================
# التشغيل
# ==========================================================

def main():

    if not BOT_TOKEN:

        raise RuntimeError(
            "BOT_TOKEN غير موجود في GitHub Secrets."
        )

    if not ADMIN_ID:

        raise RuntimeError(
            "ADMIN_ID غير موجود في GitHub Secrets."
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
        MessageHandler(
            filters.ALL,
            handle_message
        )
    )

    print("Huda People Bot is running...")

    application.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":

    main()
