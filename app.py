import os
import asyncio
from gtts import gTTS
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- ربط التوكن الخاص بك مباشرة ---
TOKEN = "7857085752:AAE6XUInKJ-SpFkVxHhYDiI2RUKcs0DiwRo"

# دالة الترحيب عند تشغيل البوت /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "أهلاً بك! أنا بوت تحويل النص إلى كلام. 🎙️\n"
        "أرسل لي أي نص وسأقوم بتحويله إلى مقطع صوتي فوراً."
    )

# دالة معالجة النصوص وتحويلها لصوت
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    chat_id = update.message.chat_id

    # إظهار حالة "يرسل ملفاً صوتياً" للمستخدم
    await context.bot.send_chat_action(chat_id=chat_id, action="record_voice")

    try:
        # 1. تحويل النص إلى كلام باستخدام gTTS (يدعم العربية)
        tts = gTTS(text=user_text, lang='ar', slow=False)
        
        # 2. حفظ الملف مؤقتاً بصيغة mp3
        file_name = f"voice_{chat_id}.mp3"
        tts.save(file_name)

        # 3. إرسال الملف الصوتي للمستخدم
        with open(file_name, 'rb') as audio:
            await update.message.reply_voice(voice=audio)

        # 4. حذف الملف من السيرفر بعد الإرسال لتوفير المساحة
        if os.path.exists(file_name):
            os.remove(file_name)

    except Exception as e:
        await update.message.reply_text(f"عذراً، حدث خطأ أثناء المعالجة: {e}")

# التشغيل الأساسي للبوت
def main():
    # إنشاء التطبيق وربطه بالتوكن
    application = Application.builder().token(TOKEN).build()

    # إضافة الأوامر والمستقبلات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("البوت يعمل الآن... اذهب إلى تلغرام وجربه!")
    application.run_polling()

if __name__ == '__main__':
    main()
