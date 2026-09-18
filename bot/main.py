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
# الواجهة الرئيسية للمستخدم
# ==========================================================

async def show_public_home(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    register_user(
        update.effective_user
    )

    context.user_data.pop(
        "public_menu_id",
        None
    )

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

    context.user_data["state"] = "creating_main_menu"

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

    context.user_data["state"] = "creating_submenu"

    context.user_data["parent_id"] = parent_id

    await update.message.reply_text(
        "📂 إنشاء قائمة فرعية\n\n"
        f"📌 داخل: {context.user_data.get('current_menu_name', '')}\n\n"
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
    # التحقق من الاسم في نفس المستوى
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
    # تحديد الترتيب
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
    # بعد إنشاء القائمة الفرعية
    # ------------------------------------------------------

    if state == "creating_submenu":

        current_menu_id = parent_id

        context.user_data.clear()

        await update.message.reply_text(
            "✅ تم إنشاء القائمة الفرعية بنجاح.\n\n"
            f"📂 الاسم: {menu_name}\n"
            f"🆔 ID: {new_menu_id}",
        )

        await open_menu(
            update,
            context,
            current_menu_id
        )

        return

    # ------------------------------------------------------
    # بعد إنشاء القائمة الرئيسية
    # ------------------------------------------------------

    context.user_data.clear()

    await update.message.reply_text(
        "✅ تم إنشاء القائمة الرئيسية بنجاح.\n\n"
        f"📂 الاسم: {menu_name}\n"
        f"🆔 ID: {new_menu_id}",
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

        await update.message.reply_text(
            "❌ ليس لديك صلاحية."
        )

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

        await update.message.reply_text(
            "❌ ليس لديك صلاحية."
        )

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

    context.user_data["current_menu_id"] = menu["id"]

    context.user_data["current_menu_name"] = menu["name"]

    context.user_data["current_parent_id"] = menu["parent_id"]

    await update.message.reply_text(
        f"📂 {menu['name']}\n\n"
        "اختر أحد العناصر:",
        reply_markup=menu_management_keyboard(
            children
        )
    )


# ==========================================================
# الرجوع في إدارة القوائم
# ==========================================================

async def go_back(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    current_parent_id = context.user_data.get(
        "current_parent_id"
    )

    if current_parent_id:

        await open_menu(
            update,
            context,
            current_parent_id
        )

        return

    context.user_data.clear()

    await show_menus(
        update,
        context
    )


# ==========================================================
# البحث عن قائمة بالاسم
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
# فتح قائمة للمستخدم العادي
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
        """
        ,
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

    connection.close()

    context.user_data["public_menu_id"] = menu["id"]

    context.user_data["public_parent_id"] = menu["parent_id"]

    context.user_data["public_menu_name"] = menu["name"]

    if children:

        await update.message.reply_text(
            f"📂 {menu['name']}\n\n"
            "اختر من القائمة:",
            reply_markup=public_menu_keyboard(
                children
            )
        )

    else:

        await update.message.reply_text(
            f"📂 {menu['name']}\n\n"
            "لا توجد عناصر داخل هذا القسم حاليًا.",
            reply_markup=public_menu_keyboard([])
        )


# ==========================================================
# ربط الأزرار الرئيسية بالقوائم التي أنشأها المشرف
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
# الرجوع في واجهة المستخدم
# ==========================================================

async def go_back_public(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    current_menu_id = context.user_data.get(
        "public_menu_id"
    )

    if not current_menu_id:

        await show_public_home(
            update,
            context
        )

        return

    connection = get_connection()

    current_menu = connection.execute(
        """
        SELECT
            id,
            parent_id
        FROM menus
        WHERE id = ?
        """,
        (current_menu_id,)
    ).fetchone()

    connection.close()

    if not current_menu:

        await show_public_home(
            update,
            context
        )

        return

    parent_id = current_menu["parent_id"]

    if parent_id is None:

        context.user_data.pop(
            "public_menu_id",
            None
        )

        context.user_data.pop(
            "public_parent_id",
            None
        )

        context.user_data.pop(
            "public_menu_name",
            None
        )

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

    if not update.message.text:
        return

    النص = update.message.text.strip()

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
    # إذا كنا في وضع إنشاء قائمة
    # ------------------------------------------------------

    if context.user_data.get(
        "state"
    ) in [
        "creating_main_menu",
        "creating_submenu"
    ]:

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
    # إنشاء قائمة رئيسية
    # ------------------------------------------------------

    if النص == "➕ إنشاء قائمة رئيسية":

        await create_main_menu_start(
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
    # الرجوع
    # ------------------------------------------------------

    if النص == "◀️ رجوع":

        # ----------------------------------------------
        # إذا كان المستخدم داخل شجرة القوائم العامة
        # ----------------------------------------------

        if context.user_data.get(
            "public_menu_id"
        ):

            await go_back_public(
                update,
                context
            )

            return

        # ----------------------------------------------
        # إذا كان المشرف داخل إدارة القوائم
        # ----------------------------------------------

        if is_admin(user_id):

            if context.user_data.get(
                "current_menu_id"
            ):

                await go_back(
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

    # ------------------------------------------------------
    # فتح قائمة للمشرف
    # ------------------------------------------------------

    if النص.startswith("📂 "):

        if not is_admin(user_id):

            return

        menu_name = النص[len("📂 "):].strip()

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
                "❌ لم يتم العثور على هذه القائمة."
            )

        return

    # ======================================================
    # الواجهة العامة
    # ======================================================

    # ------------------------------------------------------
    # القرآن والثقافة
    # ------------------------------------------------------

    if النص == "📖 القرآن والثقافة":

        context.user_data.pop(
            "current_menu_id",
            None
        )

        await open_public_root_by_name(
            update,
            context,
            "القرآن والثقافة"
        )

        return

    # ------------------------------------------------------
    # الملازم
    # ------------------------------------------------------

    if النص == "📚 الملازم":

        context.user_data.pop(
            "current_menu_id",
            None
        )

        await open_public_root_by_name(
            update,
            context,
            "الملازم"
        )

        return

    # ------------------------------------------------------
    # المحاضرات
    # ------------------------------------------------------

    if النص == "🎧 المحاضرات":

        context.user_data.pop(
            "current_menu_id",
            None
        )

        await open_public_root_by_name(
            update,
            context,
            "المحاضرات"
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
    # فتح قائمة فرعية للمستخدم
    # ------------------------------------------------------

    if النص.startswith("📂 "):

        public_menu_id = context.user_data.get(
            "public_menu_id"
        )

        if public_menu_id:

            menu_name = النص[len("📂 "):].strip()

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

            else:

                await update.message.reply_text(
                    "❌ لم يتم العثور على هذا القسم."
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
            "سيتم تفعيلها لاحقًا."
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
