import telebot
from telebot import types
import requests
import os
import time
from moviepy.editor import ImageClip, AudioFileClip

TOKEN = "7857085752:AAE6XUInKJ-SpFkVxHhYDiI2RUKcs0DiwRo"
bot = telebot.TeleBot(TOKEN)

user_files = {}

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "📸 أرسل الصورة أولاً (خلفية الفيديو).")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    img_path = f"img_{chat_id}.jpg"
    # مسح أي ملف قديم بنفس الاسم لتوفير المساحة
    if os.path.exists(img_path): os.remove(img_path)
    
    with open(img_path, 'wb') as f:
        f.write(downloaded_file)
    
    user_files[chat_id] = {'img': img_path}
    
    markup = types.InlineKeyboardMarkup()
    qaris = {"المنشاوي": "ar.minshawi", "العفاسي": "ar.alafasy", "عبدالباسط": "ar.abdulsamad"}
    for name, code in qaris.items():
        markup.add(types.InlineKeyboardButton(name, callback_data=f"q_{code}"))
    bot.send_message(chat_id, "✅ تم حفظ الصورة! اختر القارئ:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('q_'))
def select_qari(call):
    chat_id = call.message.chat.id
    if chat_id not in user_files:
        bot.send_message(chat_id, "⚠️ أرسل الصورة مرة أخرى.")
        return
    user_files[chat_id]['qari'] = call.data.split('_')[1]
    bot.answer_callback_query(call.id)
    surahs = {"الفاتحة": "1:1", "الإخلاص": "112:1", "الفلق": "113:1", "الناس": "114:1", "الكرسي": "2:255"}
    markup = types.InlineKeyboardMarkup()
    for name, code in surahs.items():
        markup.add(types.InlineKeyboardButton(name, callback_data=f"s_{code}"))
    bot.edit_message_text("📖 اختر الآية الآن:", chat_id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('s_'))
def make_video(call):
    chat_id = call.message.chat.id
    if chat_id not in user_files: return

    selection = call.data.split('_')[1]
    surah, ayah = selection.split(':')
    data = user_files[chat_id]
    
    status_msg = bot.send_message(chat_id, "⏳ جاري بدء المونتاج (صورة + صوت)...")

    try:
        # جلب البيانات
        res = requests.get(f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah}/{data['qari']}").json()
        audio_url = res['data']['audio']
        ayah_text = res['data']['text']
        
        audio_path = f"aud_{chat_id}.mp3"
        output_v = f"vid_{chat_id}.mp4"

        # تنظيف قبل البدء
        for f in [audio_path, output_v]:
            if os.path.exists(f): os.remove(f)

        # تحميل الصوت
        audio_data = requests.get(audio_url).content
        with open(audio_path, "wb") as f: f.write(audio_data)

        # معالجة الفيديو
        audio_clip = AudioFileClip(audio_path)
        video_clip = ImageClip(data['img']).set_duration(audio_clip.duration)
        video_clip = video_clip.set_audio(audio_clip)
        
        # استخدام إعدادات خفيفة جداً لضمان النجاح
        video_clip.write_videofile(output_v, fps=5, codec="libx264", audio_codec="libmp3lame", preset="ultrafast")

        with open(output_v, 'rb') as v:
            bot.send_video(chat_id, v, caption=f"📖 {ayah_text}\n\nتم بواسطة @NameRefuserBot")

        # تنظيف نهائي
        audio_clip.close()
        video_clip.close()
        os.remove(audio_path)
        os.remove(output_v)
        
    except Exception as e:
        bot.send_message(chat_id, f"❌ فشل المونتاج. السبب التقني: {str(e)[:100]}")

bot.infinity_polling()
