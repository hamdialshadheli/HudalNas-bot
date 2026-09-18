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
    back_keyboard,
    cancel_keyboard,
)


# ==========================================================
# قراءة إعدادات البوت
# ==========================================================

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")


# ==========================================================
# التحقق من الإعدادات
# ==========================================================

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

    user_id = update.effective_user.id

    register_user(
        update.effective_user
    )

    admin_status = is_admin(
        user_id
    )

    await update.message.reply_text(
        "🌿 مرحباً بك في بوت هدى للناس\n\n"
        "اختر من القائمة الرئيسية:",
        reply_markup=user_keyboard(
            is_admin_user=admin_status
        )
    )


# ==========================================================
# أمر /start
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

    user_id = update.effective_user.id

    if not is_admin(user_id):

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
# أمر /admin
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
# إنشاء قائمة
# ==========================================================

async def create_menu_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    if not is_admin(user_id):

        await update.message.reply_text(
            "❌ ليس لديك صلاحية."
        )

        return

    context.user_data["state"] = "creating_menu"

    await update.message.reply_text(
        "📂 إنشاء قائمة جديدة\n\n"
        "✏️ اكتب اسم القائمة الجديدة:\n\n"
        "مثال:\n"
        "الملازم",
        reply_markup=cancel_keyboard()
    )


# ==========================================================
# حفظ القائمة الجديدة
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
            "اكتب اسم القائمة:"
        )

        return

    connection = get_connection()

    # التحقق من عدم وجود قائمة بنفس الاسم
    existing = connection.execute(
        """
        SELECT id
        FROM menus
        WHERE name = ?
        AND parent_id IS NULL
        """,
        (menu_name,)
    ).fetchone()

    if existing:

        connection.close()

        await update.message.reply_text(
            "⚠️ توجد قائمة رئيسية بهذا الاسم بالفعل.\n\n"
            "اكتب اسمًا آخر:"
        )

        return

    # معرفة ترتيب القائمة الجديدة
    order_row = connection.execute(
        """
        SELECT COALESCE(MAX(display_order), 0) + 1 AS next_order
        FROM menus
        WHERE parent_id IS NULL
        """
    ).fetchone()

    next_order = order_row["next_order"]

    # إنشاء القائمة
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
            menu_name,
            next_order
        )
    )

    connection.commit()
    connection.close()

    context.user_data.clear()

    await update.message.reply_text(
        "✅ تم إنشاء القائمة بنجاح.\n\n"
        f"📂 اسم القائمة: {menu_name}\n"
        f"🔢 الترتيب: {next_order}",
        reply_markup=admin_keyboard()
    )


# ==========================================================
# إلغاء العملية الحالية
# ==========================================================

async def cancel_action(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data.clear()

    if is_admin(
        update.effective_user.id
    ):

        await update.message.reply_text(
            "❌ تم إلغاء العملية.",
            reply_markup=admin_keyboard()
        )

    else:

        await show_public_home(
            update,
            context
        )


# ==========================================================
# استقبال رسائل وأزرار Telegram
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
    # إذا كان المشرف يقوم بإنشاء قائمة
    # ------------------------------------------------------

    if context.user_data.get("state") == "creating_menu":

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
    # إنشاء قائمة
    # ------------------------------------------------------

    if النص == "➕ إنشاء قائمة":

        await create_menu_start(
            update,
            context
        )

        return


    # ------------------------------------------------------
    # إدارة القوائم
    # ------------------------------------------------------

    if النص == "📂 إدارة القوائم":

        if not is_admin(user_id):

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
                "لا توجد قوائم منشأة حتى الآن.\n\n"
                "استخدم ➕ إنشاء قائمة لإضافة أول قائمة.",
                reply_markup=admin_keyboard()
            )

            return

        رسالة = "📂 القوائم الرئيسية:\n\n"

        for menu in menus:

            رسالة += (
                f"🔹 {menu['name']}\n"
                f"   ID: {menu['id']}\n"
                f"   الترتيب: {menu['display_order']}\n\n"
            )

        await update.message.reply_text(
            رسالة,
            reply_markup=admin_keyboard()
        )

        return


    # ------------------------------------------------------
    # القرآن والثقافة
    # ------------------------------------------------------

    if النص == "📖 القرآن والثقافة":

        await update.message.reply_text(
            "📖 القرآن والثقافة\n\n"
            "سيتم إنشاء الأقسام والفروع هنا."
        )

        return


    # ------------------------------------------------------
    # الملازم
    # ------------------------------------------------------

    if النص == "📚 الملازم":

        await update.message.reply_text(
            "📚 الملازم\n\n"
            "سيتم إنشاء قسم الملازم هنا."
        )

        return


    # ------------------------------------------------------
    # المحاضرات
    # ------------------------------------------------------

    if النص == "🎧 المحاضرات":

        await update.message.reply_text(
            "🎧 المحاضرات\n\n"
            "سيتم إنشاء قسم المحاضرات هنا."
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

            await update.message.reply_text(
                "❌ ليس لديك صلاحية."
            )

            return

        await update.message.reply_text(
            "➕ إضافة محتوى\n\n"
            "سيتم تفعيل إضافة النصوص والصور "
            "والفيديو والصوت والملفات."
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
            "سيتم تفعيل هذه الوظيفة لاحقًا."
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
            "سيتم تفعيل هذه الوظيفة لاحقًا."
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
            "سيتم تفعيل هذه الوظيفة لاحقًا."
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
            "سيتم تفعيل إدارة المشرفين لاحقًا."
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
            "سيتم تفعيل الإحصائيات لاحقًا."
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


    # إنشاء قاعدة البيانات
    initialize_database()


    # تسجيل صاحب ADMIN_ID كمشرف
    ensure_admin(
        int(ADMIN_ID)
    )


    # إنشاء تطبيق Telegram
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )


    # أمر /start
    application.add_handler(
        CommandHandler(
            "start",
            start
        )
    )


    # أمر /admin
    application.add_handler(
        CommandHandler(
            "admin",
            admin_command
        )
    )


    # استقبال الرسائل النصية
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


    # تشغيل البوت
    application.run_polling(
        drop_pending_updates=False
    )


# ==========================================================
# نقطة تشغيل البرنامج
# ==========================================================

if __name__ == "__main__":

    main()
