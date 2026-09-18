async def backup_text_to_channel(
    application,
    title,
    text_content,
):
    if not CHANNEL_ID:
        print("⚠️ CHANNEL_ID غير موجود.")
        return

    try:
        backup_message = (
            "🗄️ نسخ احتياطي — هدى للناس\n\n"
            f"📝 العنوان: {title}\n\n"
            f"{text_content}"
        )

        await application.bot.send_message(
            chat_id=int(CHANNEL_ID),
            text=backup_message,
        )

        print(
            f"✅ تم حفظ النص في قناة النسخ الاحتياطي: {title}"
        )

    except Exception as error:
        print(
            "❌ فشل حفظ النص في قناة النسخ الاحتياطي:"
        )
        print(error)
