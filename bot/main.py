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
    back_keyboard,
    cancel_keyboard,
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
# الواجهة الرئيسية
# ==========================================================

async def show_public_home(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    register_user(update.effective_user)

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

    context.user_data.clear()

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

async def create_menu_start(
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

    context.user_data["state"] = "creating_menu"

    context.user_data["parent_id"] = None

    await update.message.reply_text(
        "📂 إنشاء قائمة جديدة\n\n"
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
            "❌ لم يتم تحديد القائمة الرئيسية."
        )

        return

    context.user_data["state"] = "creating_menu"

    context.user_data["parent_id"] = parent_id

    await update.message.reply_text(
        "📂 إنشاء قائمة فرعية\n\n"
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
            "❌ اسم القائمة لا يمكن أن يكون فارغًا.\n\n"
            "اكتب الاسم مرة أخرى:"
        )

        return

    parent_id = context.user_data.get(
        "parent_id"
    )

    connection = get_connection()

    # ------------------------------------------------------
    # التحقق من الاسم داخل نفس المستوى
    # ------------------------------------------------------

    existing = connection.execute(
        """
        SELECT id
        FROM menus
        WHERE name = ?
        AND (
            parent_id = ?
            OR (
                parent_id IS NULL
                AND ? IS NULL
            )
        )
        """,
        (
            menu_name,
            parent_id,
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
    # تحديد الترتيب
    # ------------------------------------------------------

    order_row = connection.execute(
        """
        SELECT COALESCE(MAX(display_order), 0) + 1
        AS next_order

        FROM menus

        WHERE (
            parent_id = ?
            OR (
                parent_id IS NULL
                AND ? IS NULL
            )
        )
        """,
        (
            parent_id,
            parent_id
        )
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

    context.user_data.clear()

    await update.message.reply_text(
        "✅ تم إنشاء القائمة بنجاح.\n\n"
        f"📂 الاسم: {menu_name}\n"
        f"🆔 ID: {new_menu_id}\n"
        f"🔢 الترتيب: {next_order}",
        reply_markup=admin_keyboard()
    )


# ==========================================================
# عرض القوائم الرئيسية
# ==========================================================

async def show_menus(
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

    connection = get_connection()

    menus = connection.execute(
        """
        SELECT id, name, display_order
        FROM menus
        WHERE parent_id IS NULL
        ORDER BY display_order ASC, id ASC
        """
    ).fetchall()

    connection.close()

    if not menus:

        await update.message.reply_text(
            "📂 إدارة القوائم\n\n"
            "لا توجد قوائم حتى الآن.",
            reply_markup=admin_keyboard()
        )

        return

    await update.message.reply_text(
        "📂 اختر القائمة التي تريد إدارتها:",
        reply_markup=menus_keyboard(menus)
    )


# ==========================================================
# فتح قائمة
# ==========================================================

async def open_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    menu_id
):

    connection = get_connection()

    menu = connection.execute(
        """
        SELECT id, name, parent_id
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
        SELECT id, name, display_order
        FROM menus
        WHERE parent_id = ?
        ORDER BY display_order ASC, id ASC
        """,
        (menu_id,)
    ).fetchall()

    connection.close()

    context.user_data["current_menu_id"] = menu["id"]

    context.user_data["current_menu_name"] = menu["name"]

    context.user_data["current_parent_id"] = menu["parent_id"]

    الصفوف = []

    for child in children:

        الصفوف.append([
            f"📂 {child['name']}"
        ])

    الصفوف.append([
        "➕ إنشاء قائمة فرعية"
    ])

    الصفوف.append([
        "◀️ رجوع"
    ])

    from bot.keyboards import make_keyboard

    await update.message.reply_text(
        f"📂 القائمة: {menu['name']}\n\n"
        "اختر أحد العناصر:",
        reply_markup=make_keyboard(الصفوف)
    )


# ==========================================================
# إلغاء العملية
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
# رجوع
# ==========================================================

async def go_back(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    current_parent_id = context.user_data.get(
        "current_parent_id"
    )

    if current_parent_id:

        connection = get_connection()

        parent = connection.execute(
            """
            SELECT id, name, parent_id
            FROM menus
            WHERE id = ?
            """,
            (current_parent_id,)
        ).fetchone()

        connection.close()

        if parent:

            await open_menu(
                update,
                context,
                parent["id"]
            )

            return

    context.user_data.clear()

    await show_menus(
        update,
        context
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

    النص = update.message.text

    user_id = update.effective_user.id

    register_user(
        update.effective_user
    )


    # ------------------------------------------------------
    # إلغاء
    # ------------------------------------------------------

    if النص == "❌ إلغاء":

        await cancel_action(
            update,
            context
        )

        return


    # ------------------------------------------------------
    # رجوع
    # ------------------------------------------------------

    if النص == "◀️ رجوع":

        await go_back(
            update,
            context
        )

        return


    # ------------------------------------------------------
    # إنشاء قائمة فرعية
    # ------------------------------------------------------

    if النص == "➕ إنشاء قائمة فرعية":

        await create_submenu_start(
            update,
            context
        )

        return


    # ------------------------------------------------------
    # إنشاء قائمة رئيسية
    # ------------------------------------------------------

    if النص == "➕ إنشاء قائمة":

        await create_menu_start(
            update,
            context
        )

        return


    # ------------------------------------------------------
    # إذا كنا في وضع إنشاء قائمة
    # ------------------------------------------------------

    if context.user_data.get(
        "state"
    ) == "creating_menu":

        await save_new_menu(
            update,
            context
        )

        return


    # ------------------------------------------------------
    # الإدارة
    # ------------------------------------------------------

    if النص == "⚙️ الإدارة":

        await show_admin_panel(
            update,
            context
        )

        return


    # ------------------------------------------------------
    # واجهة المستخدم
    # ------------------------------------------------------

    if النص == "👤 واجهة المستخدم":

        context.user_data.clear()

        await show_public_home(
            update,
            context
        )

        return


    # ------------------------------------------------------
    # إدارة القوائم
    # ------------------------------------------------------

    if النص == "📂 إدارة القوائم":

        await show_menus(
            update,
            context
        )

        return


    # ------------------------------------------------------
    # فتح قائمة بالاسم
    # ------------------------------------------------------

    if النص.startswith("📂 "):

        menu_name = النص[3:].strip()

        connection = get_connection()

        current_menu_id = context.user_data.get(
            "current_menu_id"
        )

        if current_menu_id:

            menu = connection.execute(
                """
                SELECT id
                FROM menus
                WHERE name = ?
                AND parent_id = ?
                """,
                (
                    menu_name,
                    current_menu_id
                )
            ).fetchone()

        else:

            menu = connection.execute(
                """
                SELECT id
                FROM menus
                WHERE name = ?
                AND parent_id IS NULL
                """,
                (menu_name,)
            ).fetchone()

        connection.close()

        if menu:

            await open_menu(
                update,
                context,
                menu["id"]
            )

        return


    # ------------------------------------------------------
    # القرآن والثقافة
    # ------------------------------------------------------

    if النص == "📖 القرآن والثقافة":

        await update.message.reply_text(
            "📖 القرآن والثقافة\n\n"
            "سيتم ربط هذا القسم بالقوائم لاحقًا."
        )

        return


    # ------------------------------------------------------
    # الملازم
    # ------------------------------------------------------

    if النص == "📚 الملازم":

        await update.message.reply_text(
            "📚 الملازم\n\n"
            "سيتم ربط هذا القسم بالقوائم لاحقًا."
        )

        return


    # ------------------------------------------------------
    # المحاضرات
    # ------------------------------------------------------

    if النص == "🎧 المحاضرات":

        await update.message.reply_text(
            "🎧 المحاضرات\n\n"
            "سيتم ربط هذا القسم بالقوائم لاحقًا."
        )

        return


    # ------------------------------------------------------
    # عن البوت
    # ------------------------------------------------------

    if النص == "ℹ️ عن البوت":

        await update.message.reply_text(
            "🌿 هدى للناس\n\n"
            "منصة Telegram لتنظيم وعرض المحتوى."
        )

        return


    # ------------------------------------------------------
    # إضافة محتوى
    # ------------------------------------------------------

    if النص == "➕ إضافة محتوى":

        if not is_admin(user_id):
            return

        await update.message.reply_text(
            "➕ إضافة محتوى\n\n"
            "سيتم تفعيلها في الخطوة القادمة."
        )

        return


    # ------------------------------------------------------
    # تعديل المحتوى
    # ------------------------------------------------------

    if النص == "✏️ تعديل المحتوى":

        if not is_admin(user_id):
            return

        await update.message.reply_text(
            "✏️ تعديل المحتوى\n\n"
            "سيتم تفعيلها لاحقًا."
        )

        return


    # ------------------------------------------------------
    # حذف المحتوى
    # ------------------------------------------------------

    if النص == "🗑️ حذف المحتوى":

        if not is_admin(user_id):
            return

        await update.message.reply_text(
            "🗑️ حذف المحتوى\n\n"
            "سيتم تفعيلها لاحقًا."
        )

        return


    # ------------------------------------------------------
    # ترتيب العناصر
    # ------------------------------------------------------

    if النص == "↕️ ترتيب العناصر":

        if not is_admin(user_id):
            return

        await update.message.reply_text(
            "↕️ ترتيب العناصر\n\n"
            "سيتم تفعيلها لاحقًا."
        )

        return


    # ------------------------------------------------------
    # المشرفون
    # ------------------------------------------------------

    if النص == "👥 المشرفون":

        if not is_admin(user_id):
            return

        await update.message.reply_text(
            "👥 المشرفون\n\n"
            "سيتم تفعيلها لاحقًا."
        )

        return


    # ------------------------------------------------------
    # الإحصائيات
    # ------------------------------------------------------

    if النص == "📊 الإحصائيات":

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
            filters.TEXT & ~filters.COMMAND,
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
