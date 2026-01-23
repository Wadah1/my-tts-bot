import os
import asyncio
import edge_tts
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# التوكن الخاص بك
TOKEN = "7857085752:AAE6XUInKJ-SpFkVxHhYDiI2RUKcs0DiwRo"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("مرحباً! أرسل لي النص وسأقوم بتحويله لصوت هادئ وواضح.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    context.user_data['text_to_say'] = user_text
    
    keyboard = [
        [
            InlineKeyboardButton("🇸🇦 حمد (رجل)", callback_data='ar-SA-HamedNeural'),
            InlineKeyboardButton("🇸🇦 زارينا (امرأة)", callback_data='ar-SA-ZariinaNeural'),
        ],
        [
            InlineKeyboardButton("🇪🇬 سلمى (امرأة)", callback_data='ar-EG-SalmaNeural'),
            InlineKeyboardButton("🇮🇶 باسل (رجل)", callback_data='ar-IQ-BasselNeural'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("اختر الصوت (تم ضبط السرعة لتكون طبيعية):", reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    voice = query.data
    text = context.user_data.get('text_to_say', '')
    
    await query.edit_message_text("⏳ جاري إنشاء الصوت بنبرة طبيعية...")
    file_path = f"voice_{query.from_user.id}.mp3"
    
    # تم ضبط السرعة (rate) إلى -15% لجعل الصوت أوضح وأبطأ قليلًا
    communicate = edge_tts.Communicate(text, voice, rate="-15%")
    await communicate.save(file_path)

    with open(file_path, 'rb') as audio:
        await context.bot.send_voice(chat_id=query.message.chat_id, voice=audio)
    
    await query.delete_message()
    if os.path.exists(file_path): os.remove(file_path)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.run_polling()

if __name__ == '__main__': main()
