import telebot
from telebot import types
import requests
import os
from moviepy.editor import ImageClip, AudioFileClip

# ضع التوكن الجديد هنا إذا قمت بتغييره
TOKEN = "7857085752:AAE6XUInKJ-SpFkVxHhYDiI2RUKcs0DiwRo"
bot = telebot.TeleBot(TOKEN)

# ذاكرة مؤقتة لحفظ مسار الصورة لكل مستخدم
user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "📸 أهلاً بك في @NameRefuserBot\nمن فضلك أرسل **الصورة** أولاً.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    img_path = f"bg_{chat_id}.jpg"
    with open(img_path, 'wb') as f:
        f.write(downloaded_file)
    
    # حفظ مسار الصورة في الذاكرة
    user_data[chat_id] = {'image': img_path}
    
    markup = types.InlineKeyboardMarkup()
    qaris = {"المنشاوي": "ar.minshawi", "العفاسي": "ar.alafasy", "عبدالباسط": "ar.abdulsamad"}
    for name, code in qaris.items():
        markup.add(types.InlineKeyboardButton(name, callback_data=f"q_{code}"))
    
    bot.send_message(chat_id, "✅ تم حفظ الصورة! اختر القارئ:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('q_'))
def select_qari(call):
    chat_id = call.message.chat.id
    if chat_id not in user_data:
        bot.send_message(chat_id, "⚠️ أعد إرسال الصورة أولاً.")
        return
        
    user_data[chat_id]['qari'] = call.data.split('_')[1]
    bot.answer_callback_query(call.id)
    
    surahs_list = {"الفاتحة": "1:1", "الإخلاص": "112:1", "الفلق": "113:1", "الناس": "114:1", "الكرسي": "2:255"}
    markup = types.InlineKeyboardMarkup()
    for name, code in surahs_list.items():
        markup.add(types.InlineKeyboardButton(name, callback_data=f"s_{code}"))
    
    bot.edit_message_text("📖 اختر الآية الآن:", chat_id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('s_'))
def make_video(call):
    chat_id = call.message.chat.id
    
    # حل مشكلة KeyError: التأكد من وجود البيانات
    if chat_id not in user_data or 'image' not in user_data[chat_id]:
        bot.send_message(chat_id, "⚠️ انتهت الجلسة، يرجى إرسال الصورة مرة أخرى.")
        return

    selection = call.data.split('_')[1]
    bot.answer_callback_query(call.id)
    surah, ayah = selection.split(':')
    data = user_data[chat_id]
    
    msg = bot.send_message(chat_id, "⏳ جاري دمج الصوت مع صورتك... انتظر قليلاً")

    try:
        res = requests.get(f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah}/{data['qari']}").json()
        ayah_text = res['data']['text']
        audio_url = res['data']['audio']

        audio_path = f"a_{chat_id}.mp3"
        with open(audio_path, "wb") as f:
            f.write(requests.get(audio_url).content)
        
        # إنشاء الفيديو (دمج بسيط للصورة والصوت لضمان عدم حدوث خطأ السيرفر)
        audio = AudioFileClip(audio_path)
        img = ImageClip(data['image']).set_duration(audio.duration).resize(width=1080)
        
        out_file = f"v_{chat_id}.mp4"
        img.set_audio(audio).write_videofile(out_file, fps=10, codec="libx264", audio_codec="aac")

        with open(out_file, 'rb') as v:
            bot.send_video(chat_id, v, caption=f"📖 {ayah_text}\n\nتم بواسطة @NameRefuserBot")
        
        # تنظيف الملفات
        os.remove(audio_path)
        os.remove(out_file)
    except Exception as e:
        bot.send_message(chat_id, "❌ حدث خطأ في النظام، يرجى المحاولة لاحقاً.")

bot.infinity_polling()
