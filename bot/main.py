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
)

from bot.keyboards import (
    user_keyboard,
    admin_keyboard,
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
    # إنشاء قائمة
    # ------------------------------------------------------

    if النص == "➕ إنشاء قائمة":

        if not is_admin(user_id):

            await update.message.reply_text(
                "❌ ليس لديك صلاحية."
            )

            return

        await update.message.reply_text(
            "📂 إنشاء قائمة\n\n"
            "سيتم تفعيل إنشاء القوائم في الخطوة القادمة."
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

        await update.message.reply_text(
            "📂 إدارة القوائم\n\n"
            "سيتم عرض القوائم هنا."
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
