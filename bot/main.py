import os
import sqlite3

from dotenv import load_dotenv
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
    get_stats,
    get_connection,
)

from bot.keyboards import (
    make_keyboard,
    user_keyboard,
    public_menu_keyboard,
    admin_keyboard,
    menus_keyboard,
    admin_menu_keyboard,
    content_type_icon,
    media_group_icon,
    media_group_finish_keyboard,
    cancel_keyboard,
)


load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")


# =========================================================
# أدوات قاعدة البيانات
# =========================================================

ROOT_MENU_ID = 0


def get_menu(menu_id):
    if menu_id == ROOT_MENU_ID:
        return {
            "id": ROOT_MENU_ID,
            "name": "القائمة الرئيسية",
            "parent_id": None,
        }

    connection = get_connection()

    row = connection.execute(
        """
        SELECT *
        FROM menus
        WHERE id = ?
        """,
        (menu_id,),
    ).fetchone()

    connection.close()

    return row


def get_children(menu_id):
    connection = get_connection()

    if menu_id == ROOT_MENU_ID:
        rows = connection.execute(
            """
            SELECT *
            FROM menus
            WHERE parent_id IS NULL
            ORDER BY display_order, id
            """
        ).fetchall()
    else:
        rows = connection.execute(
            """
            SELECT *
            FROM menus
            WHERE parent_id = ?
            ORDER BY display_order, id
            """,
            (menu_id,),
        ).fetchall()

    connection.close()

    return rows


def get_contents(menu_id):
    connection = get_connection()

    rows = connection.execute(
        """
        SELECT *
        FROM contents
        WHERE menu_id = ?
        ORDER BY display_order, id
        """,
        (menu_id,),
    ).fetchall()

    connection.close()

    return rows


def get_media_groups(menu_id):
    connection = get_connection()

    rows = connection.execute(
        """
        SELECT *
        FROM media_groups
        WHERE menu_id = ?
        ORDER BY sort_order, id
        """,
        (menu_id,),
    ).fetchall()

    connection.close()

    return rows


def get_next_display_order(table_name, parent_field, parent_id):
    connection = get_connection()

    if parent_id == ROOT_MENU_ID:
        row = connection.execute(
            f"""
            SELECT COALESCE(MAX(display_order), 0) + 1 AS next_order
            FROM {table_name}
            WHERE {parent_field} IS NULL
            """
        ).fetchone()
    else:
        row = connection.execute(
            f"""
            SELECT COALESCE(MAX(display_order), 0) + 1 AS next_order
            FROM {table_name}
            WHERE {parent_field} = ?
            """,
            (parent_id,),
        ).fetchone()

    connection.close()

    return row["next_order"]


def get_next_menu_order(parent_id):
    connection = get_connection()

    if parent_id == ROOT_MENU_ID:
        row = connection.execute(
            """
            SELECT COALESCE(MAX(display_order), 0) + 1 AS next_order
            FROM menus
            WHERE parent_id IS NULL
            """
        ).fetchone()
    else:
        row = connection.execute(
            """
            SELECT COALESCE(MAX(display_order), 0) + 1 AS next_order
            FROM menus
            WHERE parent_id = ?
            """,
            (parent_id,),
        ).fetchone()

    connection.close()

    return row["next_order"]


def get_next_group_order(menu_id):
    connection = get_connection()

    row = connection.execute(
        """
        SELECT COALESCE(MAX(sort_order), 0) + 1 AS next_order
        FROM media_groups
        WHERE menu_id = ?
        """,
        (menu_id,),
    ).fetchone()

    connection.close()

    return row["next_order"]


# =========================================================
# أدوات النصوص والأزرار
# =========================================================

SYSTEM_BUTTONS = {
    "⚙️ الإدارة",
    "📂 إدارة القوائم",
    "👥 المشرفون",
    "📊 الإحصائيات",
    "👤 واجهة المستخدم",
    "➕ إنشاء قائمة رئيسية",
    "➕ إضافة فرع",
    "📝 إضافة نص",
    "🖼️ إضافة صور متعددة",
    "🎬 إضافة فيديوهات متعددة",
    "🎵 إضافة أصوات متعددة",
    "📄 إضافة ملف",
    "🔗 إضافة رابط",
    "📝 نص",
    "📄 ملف / PDF",
    "🔗 رابط",
    "✅ إنهاء",
    "❌ إلغاء",
    "◀️ رجوع",
}


def is_system_button(text):
    if not text:
        return False

    if text in SYSTEM_BUTTONS:
        return True

    if text.startswith("📂 "):
        return True

    if text.startswith("📝 "):
        return True

    if text.startswith("📄 "):
        return True

    if text.startswith("🖼️ "):
        return True

    if text.startswith("🎬 "):
        return True

    if text.startswith("🎵 "):
        return True

    if text.startswith("🎤 "):
        return True

    if text.startswith("🔗 "):
        return True

    return False


async def send_long_text(message, text):
    if not text:
        return

    max_length = 4000

    for start in range(0, len(text), max_length):
        await message.reply_text(
            text[start:start + max_length]
        )


# =========================================================
# واجهة القائمة الرئيسية
# =========================================================

def build_root_keyboard(is_admin_user=False):
    children = get_children(ROOT_MENU_ID)
    contents = get_contents(ROOT_MENU_ID)
    groups = get_media_groups(ROOT_MENU_ID)

    rows = []

    for menu in children:
        rows.append([
            f"📂 {menu['name']}"
        ])

    for content in contents:
        icon = content_type_icon(content["content_type"])

        rows.append([
            f"{icon} {content['title']}"
        ])

    for group in groups:
        icon = media_group_icon(group["media_type"])

        rows.append([
            f"{icon} {group['title']}"
        ])

    if is_admin_user:
        rows.append(["⚙️ الإدارة"])

    return make_keyboard(rows)


async def show_root(update, context):
    user = update.effective_user

    context.user_data.clear()

    register_user(user)

    admin_user = is_admin(user.id)

    await update.message.reply_text(
        "📂 القائمة الرئيسية",
        reply_markup=build_root_keyboard(admin_user),
    )


# =========================================================
# عرض قائمة للمستخدم
# =========================================================

async def show_public_menu(update, context, menu_id):
    menu = get_menu(menu_id)

    if not menu:
        await update.message.reply_text(
            "❌ القائمة غير موجودة."
        )
        return

    context.user_data["current_menu_id"] = menu_id
    context.user_data["mode"] = "public"

    children = get_children(menu_id)
    contents = get_contents(menu_id)
    groups = get_media_groups(menu_id)

    keyboard = public_menu_keyboard(
        children=children,
        contents=contents,
        media_groups=groups,
    )

    await update.message.reply_text(
        f"📂 {menu['name']}",
        reply_markup=keyboard,
    )


# =========================================================
# عرض قائمة الإدارة
# =========================================================

async def show_admin_menu(update, context, menu_id):
    menu = get_menu(menu_id)

    if not menu:
        await update.message.reply_text(
            "❌ القائمة غير موجودة."
        )
        return

    context.user_data["current_menu_id"] = menu_id
    context.user_data["mode"] = "admin"

    children = get_children(menu_id)
    contents = get_contents(menu_id)
    groups = get_media_groups(menu_id)

    keyboard = admin_menu_keyboard(
        children=children,
        contents=contents,
        media_groups=groups,
    )

    await update.message.reply_text(
        f"⚙️ إدارة: {menu['name']}",
        reply_markup=keyboard,
    )


# =========================================================
# البداية
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_root(update, context)


# =========================================================
# لوحة الإدارة
# =========================================================

async def show_admin_panel(update, context):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            "❌ هذا القسم خاص بالمشرفين."
        )
        return

    context.user_data.clear()
    context.user_data["mode"] = "admin_panel"

    await update.message.reply_text(
        "⚙️ لوحة الإدارة",
        reply_markup=admin_keyboard(),
    )


# =========================================================
# إدارة القوائم
# =========================================================

async def show_menu_management(update, context):
    if not is_admin(update.effective_user.id):
        return

    context.user_data.clear()
    context.user_data["mode"] = "menu_management"

    menus = get_children(ROOT_MENU_ID)

    await update.message.reply_text(
        "📂 إدارة القوائم الرئيسية",
        reply_markup=menus_keyboard(menus),
    )


# =========================================================
# إنشاء قائمة رئيسية
# =========================================================

async def start_create_main_menu(update, context):
    if not is_admin(update.effective_user.id):
        return

    context.user_data["state"] = "waiting_main_menu_name"

    await update.message.reply_text(
        "✏️ أرسل اسم القائمة الرئيسية:",
        reply_markup=cancel_keyboard(),
    )


async def save_main_menu(update, context):
    name = update.message.text.strip()

    if not name:
        await update.message.reply_text(
            "❌ اسم القائمة لا يمكن أن يكون فارغًا."
        )
        return

    if is_system_button(name):
        await update.message.reply_text(
            "❌ هذا الاسم محجوز لأحد أزرار البوت.\n"
            "اختر اسمًا آخر."
        )
        return

    connection = get_connection()

    order = get_next_menu_order(ROOT_MENU_ID)

    connection.execute(
        """
        INSERT INTO menus (
            name,
            parent_id,
            display_order
        )
        VALUES (?, NULL, ?)
        """,
        (name, order),
    )

    connection.commit()
    connection.close()

    context.user_data.pop("state", None)

    await update.message.reply_text(
        f"✅ تم إنشاء القائمة الرئيسية:\n\n📂 {name}"
    )

    await show_menu_management(update, context)


# =========================================================
# إنشاء فرع داخل أي قائمة
# =========================================================

async def start_create_branch(update, context):
    if not is_admin(update.effective_user.id):
        return

    menu_id = context.user_data.get(
        "current_menu_id",
        ROOT_MENU_ID,
    )

    context.user_data["state"] = "waiting_branch_name"
    context.user_data["branch_parent_id"] = menu_id

    await update.message.reply_text(
        "📂 أرسل اسم الفرع الجديد:",
        reply_markup=cancel_keyboard(),
    )


async def save_branch(update, context):
    name = update.message.text.strip()

    if not name:
        await update.message.reply_text(
            "❌ اسم الفرع لا يمكن أن يكون فارغًا."
        )
        return

    if is_system_button(name):
        await update.message.reply_text(
            "❌ هذا الاسم محجوز لأحد أزرار البوت.\n"
            "اختر اسمًا آخر."
        )
        return

    parent_id = context.user_data.get(
        "branch_parent_id",
        ROOT_MENU_ID,
    )

    connection = get_connection()

    order = get_next_menu_order(parent_id)

    if parent_id == ROOT_MENU_ID:
        db_parent = None
    else:
        db_parent = parent_id

    connection.execute(
        """
        INSERT INTO menus (
            name,
            parent_id,
            display_order
        )
        VALUES (?, ?, ?)
        """,
        (name, db_parent, order),
    )

    connection.commit()
    connection.close()

    context.user_data.pop("state", None)
    context.user_data.pop("branch_parent_id", None)

    await update.message.reply_text(
        f"✅ تم إنشاء الفرع:\n\n📂 {name}"
    )

    if context.user_data.get("mode") == "admin":
        await show_admin_menu(update, context, parent_id)
    else:
        await show_root(update, context)


# =========================================================
# إضافة نص
# =========================================================

async def start_add_text(update, context):
    if not is_admin(update.effective_user.id):
        return

    menu_id = context.user_data.get(
        "current_menu_id",
        ROOT_MENU_ID,
    )

    context.user_data["state"] = "waiting_text_title"
    context.user_data["content_menu_id"] = menu_id

    await update.message.reply_text(
        "📝 أرسل عنوان النص:",
        reply_markup=cancel_keyboard(),
    )


async def save_text_title(update, context):
    title = update.message.text.strip()

    if not title:
        await update.message.reply_text(
            "❌ العنوان لا يمكن أن يكون فارغًا."
        )
        return

    if is_system_button(title):
        await update.message.reply_text(
            "❌ هذا العنوان محجوز لأحد أزرار البوت.\n"
            "اختر عنوانًا آخر."
        )
        return

    context.user_data["text_title"] = title
    context.user_data["state"] = "waiting_text_content"

    await update.message.reply_text(
        "📝 أرسل النص الآن:\n\n"
        "يمكن أن يكون النص طويلًا.",
        reply_markup=cancel_keyboard(),
    )


async def save_text_content(update, context):
    text_content = update.message.text

    if not text_content:
        await update.message.reply_text(
            "❌ لم يتم استلام نص."
        )
        return

    menu_id = context.user_data.get(
        "content_menu_id",
        ROOT_MENU_ID,
    )

    title = context.user_data.get(
        "text_title",
        "نص",
    )

    connection = get_connection()

    order = get_next_display_order(
        "contents",
        "menu_id",
        menu_id,
    )

    connection.execute(
        """
        INSERT INTO contents (
            menu_id,
            title,
            content_type,
            text_content,
            display_order
        )
        VALUES (?, ?, 'text', ?, ?)
        """,
        (
            menu_id,
            title,
            text_content,
            order,
        ),
    )

    connection.commit()
    connection.close()

    context.user_data.pop("state", None)
    context.user_data.pop("content_menu_id", None)
    context.user_data.pop("text_title", None)

    await update.message.reply_text(
        f"✅ تم حفظ النص:\n\n📝 {title}"
    )

    await show_admin_menu(update, context, menu_id)


# =========================================================
# إضافة رابط
# =========================================================

async def start_add_url(update, context):
    if not is_admin(update.effective_user.id):
        return

    menu_id = context.user_data.get(
        "current_menu_id",
        ROOT_MENU_ID,
    )

    context.user_data["state"] = "waiting_url_title"
    context.user_data["content_menu_id"] = menu_id

    await update.message.reply_text(
        "🔗 أرسل عنوان الرابط:",
        reply_markup=cancel_keyboard(),
    )


async def save_url_title(update, context):
    title = update.message.text.strip()

    if not title:
        await update.message.reply_text(
            "❌ العنوان لا يمكن أن يكون فارغًا."
        )
        return

    context.user_data["url_title"] = title
    context.user_data["state"] = "waiting_url"

    await update.message.reply_text(
        "🔗 أرسل الرابط الآن:",
        reply_markup=cancel_keyboard(),
    )


async def save_url(update, context):
    url = update.message.text.strip()

    if not url:
        await update.message.reply_text(
            "❌ الرابط لا يمكن أن يكون فارغًا."
        )
        return

    menu_id = context.user_data.get(
        "content_menu_id",
        ROOT_MENU_ID,
    )

    title = context.user_data.get(
        "url_title",
        "رابط",
    )

    connection = get_connection()

    order = get_next_display_order(
        "contents",
        "menu_id",
        menu_id,
    )

    connection.execute(
        """
        INSERT INTO contents (
            menu_id,
            title,
            content_type,
            url,
            display_order
        )
        VALUES (?, ?, 'url', ?, ?)
        """,
        (
            menu_id,
            title,
            url,
            order,
        ),
    )

    connection.commit()
    connection.close()

    context.user_data.pop("state", None)
    context.user_data.pop("content_menu_id", None)
    context.user_data.pop("url_title", None)

    await update.message.reply_text(
        f"✅ تم حفظ الرابط:\n\n🔗 {title}"
    )

    await show_admin_menu(update, context, menu_id)


# =========================================================
# إضافة ملف / PDF
# =========================================================

async def start_add_document(update, context):
    if not is_admin(update.effective_user.id):
        return

    menu_id = context.user_data.get(
        "current_menu_id",
        ROOT_MENU_ID,
    )

    context.user_data["state"] = "waiting_document_title"
    context.user_data["content_menu_id"] = menu_id

    await update.message.reply_text(
        "📄 أرسل عنوان الملف:",
        reply_markup=cancel_keyboard(),
    )


async def save_document_title(update, context):
    title = update.message.text.strip()

    if not title:
        await update.message.reply_text(
            "❌ العنوان لا يمكن أن يكون فارغًا."
        )
        return

    context.user_data["document_title"] = title
    context.user_data["state"] = "waiting_document"

    await update.message.reply_text(
        "📄 أرسل الملف أو PDF الآن.",
        reply_markup=cancel_keyboard(),
    )


async def save_document(update, context):
    if not update.message.document:
        await update.message.reply_text(
            "❌ أرسل ملفًا أو PDF."
        )
        return

    document = update.message.document

    menu_id = context.user_data.get(
        "content_menu_id",
        ROOT_MENU_ID,
    )

    title = context.user_data.get(
        "document_title",
        document.file_name or "ملف",
    )

    connection = get_connection()

    order = get_next_display_order(
        "contents",
        "menu_id",
        menu_id,
    )

    connection.execute(
        """
        INSERT INTO contents (
            menu_id,
            title,
            content_type,
            file_id,
            display_order
        )
        VALUES (?, ?, 'document', ?, ?)
        """,
        (
            menu_id,
            title,
            document.file_id,
            order,
        ),
    )

    connection.commit()
    connection.close()

    context.user_data.pop("state", None)
    context.user_data.pop("content_menu_id", None)
    context.user_data.pop("document_title", None)

    await update.message.reply_text(
        f"✅ تم حفظ الملف:\n\n📄 {title}"
    )

    await show_admin_menu(update, context, menu_id)


# =========================================================
# مجموعات الصور والفيديوهات والأصوات
# =========================================================

async def start_media_group(update, context, media_type):
    if not is_admin(update.effective_user.id):
        return

    menu_id = context.user_data.get(
        "current_menu_id",
        ROOT_MENU_ID,
    )

    context.user_data["state"] = "waiting_group_title"
    context.user_data["group_menu_id"] = menu_id
    context.user_data["new_group_type"] = media_type

    await update.message.reply_text(
        "✏️ أرسل اسم المجموعة:",
        reply_markup=cancel_keyboard(),
    )


async def save_group_title(update, context):
    title = update.message.text.strip()

    if not title:
        await update.message.reply_text(
            "❌ اسم المجموعة لا يمكن أن يكون فارغًا."
        )
        return

    if is_system_button(title):
        await update.message.reply_text(
            "❌ هذا الاسم محجوز لأحد أزرار البوت.\n"
            "اختر اسمًا آخر."
        )
        return

    context.user_data["group_title"] = title
    context.user_data["state"] = "waiting_group_description"

    await update.message.reply_text(
        "📝 أرسل وصف المجموعة.\n\n"
        "إذا لم ترد وصفًا، أرسل:\n"
        "بدون شرح",
        reply_markup=cancel_keyboard(),
    )


async def create_group(update, context):
    description = update.message.text.strip()

    if description == "بدون شرح":
        description = ""

    title = context.user_data.get(
        "group_title",
        "مجموعة",
    )

    media_type = context.user_data.get(
        "new_group_type"
    )

    menu_id = context.user_data.get(
        "group_menu_id",
        ROOT_MENU_ID,
    )

    if media_type not in {
        "photo",
        "video",
        "audio",
    }:
        await update.message.reply_text(
            "❌ نوع المجموعة غير صحيح."
        )
        return

    connection = get_connection()

    order = get_next_group_order(menu_id)

    cursor = connection.execute(
        """
        INSERT INTO media_groups (
            menu_id,
            title,
            description,
            media_type,
            sort_order
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            menu_id,
            title,
            description,
            media_type,
            order,
        ),
    )

    group_id = cursor.lastrowid

    connection.commit()
    connection.close()

    context.user_data["media_group_id"] = group_id
    context.user_data["creating_media_group"] = True
    context.user_data["state"] = "receiving_media"

    icon = media_group_icon(media_type)

    await update.message.reply_text(
        f"{icon} تم إنشاء المجموعة:\n\n"
        f"{title}\n\n"
        "الآن أرسل الملفات واحدًا تلو الآخر.\n"
        "وعندما تنتهي اضغط:\n"
        "✅ إنهاء",
        reply_markup=media_group_finish_keyboard(),
    )


# =========================================================
# استقبال الصور / الفيديو / الصوت
# =========================================================

async def handle_media(update, context):
    if not context.user_data.get("creating_media_group"):
        return

    media_group_id = context.user_data.get(
        "media_group_id"
    )

    media_type = context.user_data.get(
        "new_group_type"
    )

    file_id = None
    caption = None

    if media_type == "photo":

        if not update.message.photo:
            await update.message.reply_text(
                "❌ هذه المجموعة مخصصة للصور فقط."
            )
            return

        file_id = update.message.photo[-1].file_id
        caption = update.message.caption

    elif media_type == "video":

        if not update.message.video:
            await update.message.reply_text(
                "❌ هذه المجموعة مخصصة للفيديوهات فقط."
            )
            return

        file_id = update.message.video.file_id
        caption = update.message.caption

    elif media_type == "audio":

        if not update.message.audio:
            await update.message.reply_text(
                "❌ هذه المجموعة مخصصة للأصوات فقط."
            )
            return

        file_id = update.message.audio.file_id
        caption = update.message.caption

    else:
        return

    connection = get_connection()

    row = connection.execute(
        """
        SELECT COALESCE(MAX(sort_order), 0) + 1 AS next_order
        FROM media_group_items
        WHERE group_id = ?
        """,
        (media_group_id,),
    ).fetchone()

    order = row["next_order"]

    connection.execute(
        """
        INSERT INTO media_group_items (
            group_id,
            file_id,
            caption,
            sort_order
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            media_group_id,
            file_id,
            caption,
            order,
        ),
    )

    connection.commit()

    count = connection.execute(
        """
        SELECT COUNT(*) AS n
        FROM media_group_items
        WHERE group_id = ?
        """,
        (media_group_id,),
    ).fetchone()["n"]

    connection.close()

    await update.message.reply_text(
        f"✅ تم حفظ العنصر رقم {count}\n\n"
        "يمكنك إرسال عنصر آخر أو الضغط على:\n"
        "✅ إنهاء",
        reply_markup=media_group_finish_keyboard(),
    )


# =========================================================
# إنهاء مجموعة الوسائط
# =========================================================

async def finish_media_group(update, context):
    group_id = context.user_data.get(
        "media_group_id"
    )

    menu_id = context.user_data.get(
        "group_menu_id",
        ROOT_MENU_ID,
    )

    if not group_id:
        await show_admin_menu(update, context, menu_id)
        return

    connection = get_connection()

    row = connection.execute(
        """
        SELECT COUNT(*) AS n
        FROM media_group_items
        WHERE group_id = ?
        """,
        (group_id,),
    ).fetchone()

    count = row["n"]

    connection.close()

    if count == 0:
        await update.message.reply_text(
            "⚠️ لم تضف أي ملف إلى المجموعة.\n"
            "أرسل ملفًا واحدًا على الأقل أو ألغِ العملية."
        )
        return

    context.user_data.pop("creating_media_group", None)
    context.user_data.pop("media_group_id", None)
    context.user_data.pop("new_group_type", None)
    context.user_data.pop("group_title", None)
    context.user_data.pop("group_menu_id", None)
    context.user_data.pop("state", None)

    await update.message.reply_text(
        f"✅ تم إنهاء المجموعة بنجاح.\n"
        f"عدد العناصر: {count}"
    )

    await show_admin_menu(update, context, menu_id)


# =========================================================
# إلغاء العملية الحالية
# =========================================================

async def cancel_action(update, context):
    group_id = context.user_data.get(
        "media_group_id"
    )

    if context.user_data.get("creating_media_group") and group_id:

        connection = get_connection()

        connection.execute(
            """
            DELETE FROM media_group_items
            WHERE group_id = ?
            """,
            (group_id,),
        )

        connection.execute(
            """
            DELETE FROM media_groups
            WHERE id = ?
            """,
            (group_id,),
        )

        connection.commit()
        connection.close()

    context.user_data.clear()

    await update.message.reply_text(
        "❌ تم إلغاء العملية."
    )

    if is_admin(update.effective_user.id):
        await show_admin_panel(update, context)
    else:
        await show_root(update, context)


# =========================================================
# إرسال محتوى فردي
# =========================================================

async def send_single_content(update, content):
    message = update.message

    content_type = content["content_type"]

    if content_type == "text":

        await send_long_text(
            message,
            content["text_content"] or "",
        )

    elif content_type == "document":

        await message.reply_document(
            document=content["file_id"]
        )

    elif content_type == "photo":

        await message.reply_photo(
            photo=content["file_id"]
        )

    elif content_type == "video":

        await message.reply_video(
            video=content["file_id"]
        )

    elif content_type == "audio":

        await message.reply_audio(
            audio=content["file_id"]
        )

    elif content_type == "voice":

        await message.reply_voice(
            voice=content["file_id"]
        )

    elif content_type == "url":

        await message.reply_text(
            content["url"] or ""
        )

    else:

        await message.reply_text(
            "❌ نوع المحتوى غير مدعوم."
        )


# =========================================================
# إرسال مجموعة وسائط
# =========================================================

async def send_media_group(update, group):
    message = update.message

    connection = get_connection()

    items = connection.execute(
        """
        SELECT *
        FROM media_group_items
        WHERE group_id = ?
        ORDER BY sort_order, id
        """,
        (group["id"],),
    ).fetchall()

    connection.close()

    if not items:
        await message.reply_text(
            "❌ هذه المجموعة لا تحتوي على ملفات."
        )
        return

    description = group["description"] or ""

    if description:
        await message.reply_text(
            f"📂 {group['title']}\n\n"
            f"{description}"
        )

    media_type = group["media_type"]

    for item in items:

        caption = item["caption"]

        if media_type == "photo":

            await message.reply_photo(
                photo=item["file_id"],
                caption=caption,
            )

        elif media_type == "video":

            await message.reply_video(
                video=item["file_id"],
                caption=caption,
            )

        elif media_type == "audio":

            await message.reply_audio(
                audio=item["file_id"],
                caption=caption,
            )


# =========================================================
# فتح فرع
# =========================================================

def find_child_by_button(menu_id, text):
    if not text.startswith("📂 "):
        return None

    name = text.removeprefix("📂 ").strip()

    children = get_children(menu_id)

    for child in children:
        if child["name"] == name:
            return child

    return None


def find_content_by_button(menu_id, text):
    contents = get_contents(menu_id)

    for content in contents:

        icon = content_type_icon(
            content["content_type"]
        )

        button_text = f"{icon} {content['title']}"

        if button_text == text:
            return content

    return None


def find_group_by_button(menu_id, text):
    groups = get_media_groups(menu_id)

    for group in groups:

        icon = media_group_icon(
            group["media_type"]
        )

        button_text = f"{icon} {group['title']}"

        if button_text == text:
            return group

    return None


# =========================================================
# الرجوع درجة واحدة
# =========================================================

async def go_back(update, context):
    mode = context.user_data.get("mode")

    current_menu_id = context.user_data.get(
        "current_menu_id",
        ROOT_MENU_ID,
    )

    if mode == "admin":

        if current_menu_id == ROOT_MENU_ID:
            await show_menu_management(update, context)
            return

        menu = get_menu(current_menu_id)

        if not menu:
            await show_menu_management(update, context)
            return

        parent_id = menu["parent_id"]

        if parent_id is None:
            await show_admin_menu(
                update,
                context,
                ROOT_MENU_ID,
            )
        else:
            await show_admin_menu(
                update,
                context,
                parent_id,
            )

        return

    if mode == "public":

        if current_menu_id == ROOT_MENU_ID:
            await show_root(update, context)
            return

        menu = get_menu(current_menu_id)

        if not menu:
            await show_root(update, context)
            return

        parent_id = menu["parent_id"]

        if parent_id is None:
            await show_root(update, context)
        else:
            await show_public_menu(
                update,
                context,
                parent_id,
            )

        return

    await show_root(update, context)


# =========================================================
# التعامل مع الأزرار والرسائل النصية
# =========================================================

async def handle_text(update, context):
    text = update.message.text.strip()

    if not text:
        return

    user_id = update.effective_user.id

    # -----------------------------------------------------
    # الأزرار العامة أولاً
    # -----------------------------------------------------

    if text == "❌ إلغاء":
        await cancel_action(update, context)
        return

    if text == "◀️ رجوع":
        await go_back(update, context)
        return

    # -----------------------------------------------------
    # إنهاء مجموعة الوسائط
    # -----------------------------------------------------

    if text == "✅ إنهاء":

        if context.user_data.get("creating_media_group"):
            await finish_media_group(update, context)

        return

    # -----------------------------------------------------
    # الإدارة
    # -----------------------------------------------------

    if text == "⚙️ الإدارة":

        if is_admin(user_id):
            await show_admin_panel(update, context)

        return

    if text == "📂 إدارة القوائم":

        if is_admin(user_id):
            await show_menu_management(update, context)

        return

    if text == "👤 واجهة المستخدم":

        await show_root(update, context)
        return

    if text == "📊 الإحصائيات":

        if not is_admin(user_id):
            return

        stats = get_stats()

        users = stats[0]
        menus = stats[1]
        contents = stats[2]
        admins = stats[3]
        media_groups = stats[4]
        media_items = stats[5]

        await update.message.reply_text(
            "📊 إحصائيات البوت\n\n"
            f"👥 المستخدمون: {users}\n"
            f"📂 القوائم: {menus}\n"
            f"📝 المحتويات: {contents}\n"
            f"🎞️ مجموعات الوسائط: {media_groups}\n"
            f"📦 عناصر الوسائط: {media_items}\n"
            f"👤 المشرفون: {admins}"
        )

        return

    if text == "👥 المشرفون":

        if not is_admin(user_id):
            return

        await update.message.reply_text(
            "👥 إدارة المشرفين ستكون في المرحلة التالية."
        )
        return

    # -----------------------------------------------------
    # إنشاء قائمة رئيسية
    # -----------------------------------------------------

    if text == "➕ إنشاء قائمة رئيسية":

        if is_admin(user_id):
            await start_create_main_menu(
                update,
                context,
            )

        return

    # -----------------------------------------------------
    # أدوات الإدارة داخل القائمة
    # -----------------------------------------------------

    if text == "➕ إضافة فرع":

        if is_admin(user_id):
            await start_create_branch(
                update,
                context,
            )

        return

    if text == "📝 إضافة نص":

        if is_admin(user_id):
            await start_add_text(
                update,
                context,
            )

        return

    if text == "📄 إضافة ملف":

        if is_admin(user_id):
            await start_add_document(
                update,
                context,
            )

        return

    if text == "🔗 إضافة رابط":

        if is_admin(user_id):
            await start_add_url(
                update,
                context,
            )

        return

    if text == "🖼️ إضافة صور متعددة":

        if is_admin(user_id):
            await start_media_group(
                update,
                context,
                "photo",
            )

        return

    if text == "🎬 إضافة فيديوهات متعددة":

        if is_admin(user_id):
            await start_media_group(
                update,
                context,
                "video",
            )

        return

    if text == "🎵 إضافة أصوات متعددة":

        if is_admin(user_id):
            await start_media_group(
                update,
                context,
                "audio",
            )

        return

    # -----------------------------------------------------
    # حالات الإدخال
    # -----------------------------------------------------

    state = context.user_data.get("state")

    if state == "waiting_main_menu_name":

        await save_main_menu(
            update,
            context,
        )
        return

    if state == "waiting_branch_name":

        await save_branch(
            update,
            context,
        )
        return

    if state == "waiting_text_title":

        await save_text_title(
            update,
            context,
        )
        return

    if state == "waiting_text_content":

        await save_text_content(
            update,
            context,
        )
        return

    if state == "waiting_url_title":

        await save_url_title(
            update,
            context,
        )
        return

    if state == "waiting_url":

        await save_url(
            update,
            context,
        )
        return

    if state == "waiting_document_title":

        await save_document_title(
            update,
            context,
        )
        return

    if state == "waiting_group_title":

        await save_group_title(
            update,
            context,
        )
        return

    if state == "waiting_group_description":

        await create_group(
            update,
            context,
        )
        return

    if state == "waiting_document":

        await update.message.reply_text(
            "📄 أنت الآن في انتظار ملف أو PDF."
        )
        return

    if state == "receiving_media":

        await update.message.reply_text(
            "📦 أنت الآن تضيف ملفات إلى مجموعة الوسائط.\n"
            "أرسل الملف المناسب أو اضغط ✅ إنهاء."
        )
        return

    # -----------------------------------------------------
    # القائمة الحالية
    # -----------------------------------------------------

    mode = context.user_data.get("mode")

    current_menu_id = context.user_data.get(
        "current_menu_id",
        ROOT_MENU_ID,
    )

    # -----------------------------------------------------
    # فتح فرع
    # -----------------------------------------------------

    child = find_child_by_button(
        current_menu_id,
        text,
    )

    if child:

        if mode == "admin":

            await show_admin_menu(
                update,
                context,
                child["id"],
            )

        else:

            await show_public_menu(
                update,
                context,
                child["id"],
            )

        return

    # -----------------------------------------------------
    # فتح محتوى فردي
    # -----------------------------------------------------

    content = find_content_by_button(
        current_menu_id,
        text,
    )

    if content:

        await send_single_content(
            update,
            content,
        )

        return

    # -----------------------------------------------------
    # فتح مجموعة وسائط
    # -----------------------------------------------------

    group = find_group_by_button(
        current_menu_id,
        text,
    )

    if group:

        await send_media_group(
            update,
            group,
        )

        return

    # -----------------------------------------------------
    # أزرار القائمة الرئيسية القديمة
    # -----------------------------------------------------

    # دعم الأزرار القديمة إذا كانت موجودة عند المستخدم.
    old_main_names = {
        "📖 القرآن والثقافة": "القرآن والثقافة",
        "📚 الملازم": "الملازم",
        "🎧 المحاضرات": "المحاضرات",
        "ℹ️ عن البوت": "عن البوت",
    }

    if text in old_main_names:

        target_name = old_main_names[text]

        children = get_children(ROOT_MENU_ID)

        for menu in children:

            if menu["name"] == target_name:

                await show_public_menu(
                    update,
                    context,
                    menu["id"],
                )

                return

    # -----------------------------------------------------
    # أي نص غير معروف
    # -----------------------------------------------------

    await update.message.reply_text(
        "❓ لم أفهم هذا الخيار.\n"
        "اختر أحد الأزرار الظاهرة أمامك."
    )


# =========================================================
# التطبيق الرئيسي
# =========================================================

def main():

    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN غير موجود في متغيرات البيئة."
        )

    initialize_database()

    if ADMIN_ID:
        try:
            ensure_admin(int(ADMIN_ID))
        except ValueError:
            raise RuntimeError(
                "ADMIN_ID يجب أن يكون رقم Telegram User ID صحيح."
            )

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    # الرسائل النصية
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_text,
        )
    )

    # الصور
    application.add_handler(
        MessageHandler(
            filters.PHOTO,
            handle_media,
        )
    )

    # الفيديوهات
    application.add_handler(
        MessageHandler(
            filters.VIDEO,
            handle_media,
        )
    )

    # الأصوات
    application.add_handler(
        MessageHandler(
            filters.AUDIO,
            handle_media,
        )
    )

    # الملفات
    application.add_handler(
        MessageHandler(
            filters.Document.ALL,
            save_document,
        )
    )

    print("Huda People Bot is running...")

    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()
