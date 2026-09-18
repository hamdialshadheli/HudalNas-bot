# ==========================================================
# بوت هدى للناس
# الملف الرئيسي لتشغيل البوت
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
# التأكد من وجود الإعدادات
# ==========================================================

if not BOT_TOKEN:
    raise RuntimeError(
        "❌ BOT_TOKEN غير موجود في إعدادات GitHub"
    )

if not ADMIN_ID:
    raise RuntimeError(
        "❌ ADMIN_ID غير موجود في إعدادات GitHub"
    )


# ==========================================================
# الواجهة الرئيسية للمستخدم
# ==========================================================

async def show_public_home(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    # تسجيل المستخدم في قاعدة البيانات
    register_user(update.effective_user)

    # التحقق هل المستخدم مشرف أم لا
    admin_status = is_admin(user_id)

    # إرسال الواجهة الرئيسية
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

    # حذف أي حالة سابقة للمستخدم
    context.user_data.clear()

    # عرض الواجهة الرئيسية
    await show_public_home(
        update,
        context
    )


# ==========================================================
# واجهة الإدارة
# ==========================================================

async def show_admin_panel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    # التحقق من صلاحية المستخدم
    if not is_admin(user_id):

        await update.message.reply_text(
            "❌ ليس لديك صلاحية الدخول إلى لوحة الإدارة."
        )

        return

    # مسح الحالة السابقة
    context.user_data.clear()

    # عرض لوحة الإدارة
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
# التعامل مع أزرار المستخدم
# ==========================================================

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    النص = update.message.text

    user_id = update.effective_user.id


    # ------------------------------------------------------
    # تسجيل المستخدم
    # ------------------------------------------------------

    register_user(
        update.effective_user
    )


    # ------------------------------------------------------
    # زر الإدارة
    # ------------------------------------------------------

    if النص == "⚙️ الإدارة":

        await show_admin_panel(
            update,
            context
        )

        return


    # ------------------------------------------------------
    # زر واجهة المستخدم
    # ------------------------------------------------------

    if النص == "👤 واجهة المستخدم":

        context.user_data.clear()

        await show_public_home(
            update,
            context
        )

        return


    # ------------------------------------------------------
    # زر القرآن والثقافة
    # ------------------------------------------------------

    if النص == "📖 القرآن والثقافة":

        await update.message.reply_text(
            "📖 القرآن والثقافة\n\n"
            "سيتم بناء الأقسام والفروع هنا في الخطوات القادمة."
        )

        return


    # ------------------------------------------------------
    # زر الملازم
    # ------------------------------------------------------

    if النص == "📚 الملازم":

        await update.message.reply_text(
            "📚 الملازم\n\n"
            "سيتم بناء قسم الملازم هنا."
        )

        return


    # ------------------------------------------------------
    # زر المحاضرات
    # ------------------------------------------------------

    if النص == "🎧 المحاضرات":

        await update.message.reply_text(
            "🎧 المحاضرات\n\n"
            "سيتم بناء قسم المحاضرات هنا."
        )

        return


    # ------------------------------------------------------
    # زر عن البوت
    # ------------------------------------------------------

    if النص == "ℹ️ عن البوت":

        await update.message.reply_text(
            "🌿 هدى للناس\n\n"
            "منصة Telegram لتنظيم وعرض المحتوى."
        )

        return


    # ------------------------------------------------------
    # زر إنشاء قائمة
    # ------------------------------------------------------

    if النص == "➕ إنشاء قائمة":

        if not is_admin(user_id):

            await update.message.reply_text(
                "❌ ليس لديك صلاحية."
            )

            return

        await update.message.reply_text(
            "📂 إنشاء قائمة\n\n"
            "هذه الوظيفة سيتم ربطها بقاعدة البيانات "
            "في الخطوة القادمة."
        )

        return


    # ------------------------------------------------------
    # زر إدارة القوائم
    # ------------------------------------------------------

    if النص == "📂 إدارة القوائم":

        if not is_admin(user_id):

            await update.message.reply_text(
                "❌ ليس لديك صلاحية."
            )

            return

        await update.message.reply_text(
            "📂 إدارة القوائم\n\n"
            "سيتم عرض القوائم التي ينشئها المشرف هنا."
        )

        return


    # ------------------------------------------------------
    # زر إضافة محتوى
    # ------------------------------------------------------

    if النص == "➕ إضافة محتوى":

        if not is_admin(user_id):

            await update.message.reply_text(
                "❌ ليس لديك صلاحية."
            )

            return

        await update.message.reply_text(
            "➕ إضافة محتوى\n\n"
            "سيتم بناء نظام إضافة النصوص والصور "
            "والفيديو والصوت والملفات لاحقاً."
        )

        return


    # ------------------------------------------------------
    # زر تعديل المحتوى
    # ------------------------------------------------------

    if النص == "✏️ تعديل المحتوى":

        if not is_admin(user_id):
            return

        await update.message.reply_text(
            "✏️ تعديل المحتوى\n\n"
            "سيتم تفعيل هذه الوظيفة لاحقاً."
        )

        return


    # ------------------------------------------------------
    # زر حذف المحتوى
    # ------------------------------------------------------

    if النص == "🗑️ حذف المحتوى":

        if not is_admin(user_id):
            return

        await update.message.reply_text(
            "🗑️ حذف المحتوى\n\n"
            "سيتم تفعيل هذه الوظيفة لاحقاً."
        )

        return


    # ------------------------------------------------------
    # زر ترتيب العناصر
    # ------------------------------------------------------

    if النص == "↕️ ترتيب العناصر":

        if not is_admin(user_id):
            return

        await update.message.reply_text(
            "↕️ ترتيب العناصر\n\n"
            "سيتم تفعيل نظام الترتيب لاحقاً."
        )

        return


    # ------------------------------------------------------
    # زر المشرفين
    # ------------------------------------------------------

    if النص == "👥 المشرفون":

        if not is_admin(user_id):
            return

        await update.message.reply_text(
            "👥 المشرفون\n\n"
            "سيتم بناء إدارة المشرفين لاحقاً."
        )

        return


    # ------------------------------------------------------
    # زر الإحصائيات
    # ------------------------------------------------------

    if النص == "📊 الإحصائيات":

        if not is_admin(user_id):
            return

        await update.message.reply_text(
            "📊 الإحصائيات\n\n"
            "سيتم عرض إحصائيات البوت هنا."
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


    # إنشاء قاعدة البيانات والجداول
    initialize_database()


    # إنشاء تطبيق Telegram
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )


    # ------------------------------------------------------
    # أوامر البوت
    # ------------------------------------------------------

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


    # ------------------------------------------------------
    # استقبال الرسائل النصية والأزرار
    # ------------------------------------------------------

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )


    print(
        "✅ Huda People Bot is running...",
        flush=True
    )


    # تشغيل البوت
    application.run_polling(
        drop_pending_updates=False
    )


# ==========================================================
# نقطة بداية البرنامج
# ==========================================================

if __name__ == "__main__":
    main()
