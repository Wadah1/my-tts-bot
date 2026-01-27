import telebot
from telebot import types
import requests
import os
import random
from moviepy.editor import ImageClip, TextClip, CompositeVideoClip, AudioFileClip
from arabic_reshaper import reshape
from bidi.algorithm import get_display

# التوكن الخاص بك
TOKEN = "7857085752:AAE6XUInKJ-SpFkVxHhYDiI2RUKcs0DiwRo"
bot = telebot.TeleBot(TOKEN)

# قائمة القراء
qaris = {
    "الشيخ المنشاوي": "ar.minshawi",
    "مشاري العفاسي": "ar.alafasy",
    "الشيخ عبدالباسط": "ar.abdulsamad"
}

# قائمة السور
surahs = {"الفاتحة": 1, "الإخلاص": 112, "الفلق": 113, "الناس": 114}

user_data = {}

def fix_arabic(text):
    return get_display(reshape(text))

def get_random_nature_image():
    """هذه الدالة تجلب صورة منظر طبيعي عشوائية من الإنترنت"""
    try:
        # رابط يجلب صورة عشوائية لمناظر طبيعية بجودة عالية
        img_url = "https://source.unsplash.com/featured/1080x1920/?nature,mountains,sea"
        response = requests.get(img_url)
        if response.status_code == 200:
            with open("downloaded_bg.jpg", "wb") as f:
                f.write(response.content)
            return "downloaded_bg.jpg"
    except:
        return None

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    for name in qaris.keys():
        markup.add(types.InlineKeyboardButton(name, callback_data=f"qari_{qaris[name]}"))
    bot.send_message(message.chat.id, "✨ مرحباً بك في بوت @NameRefuserBot ✨\nالبوت سيجلب صورة ومقاطع صوتية تلقائياً.\n\nاختر القارئ:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('qari_'))
def select_qari(call):
    user_data[call.message.chat.id] = {'qari': call.data.split('_')[1]}
    markup = types.InlineKeyboardMarkup()
    for name, s_id in surahs.items():
        markup.add(types.InlineKeyboardButton(name, callback_data=f"surah_{s_id}"))
    bot.edit_message_text("📖 اختر السورة الآن:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('surah_'))
def select_surah(call):
    user_data[call.message.chat.id]['surah'] = call.data.split('_')[1]
    bot.send_message(call.message.chat.id, "🔢 أرسل رقم الآية (مثال: 1)")

@bot.message_handler(func=lambda message: True)
def create_video(message):
    chat_id = message.chat.id
    if chat_id not in user_data or 'surah' not in user_data[chat_id]:
        bot.reply_to(message, "يرجى البدء عبر /start")
        return

    try:
        ayah = message.text
        surah = user_data[chat_id]['surah']
        qari = user_data[chat_id]['qari']
        
        bot.send_message(chat_id, "⏳ جاري جلب صورة جديدة وصوت الآية... انتظر قليلاً")

        # 1. جلب الصورة تلقائياً
        bg_image = get_random_nature_image()
        
        # 2. جلب البيانات من API القرآن
        res = requests.get(f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah}/{qari}").json()
        ayah_text = res['data']['text']
        audio_url = res['data']['audio']

        # 3. تحميل الصوت
        audio_content = requests.get(audio_url).content
        with open("temp.mp3", "wb") as f: f.write(audio_content)
        audio = AudioFileClip("temp.mp3")

        # 4. المونتاج
        img = ImageClip(bg_image).set_duration(audio.duration).resize(width=1080)
        txt = TextClip(fix_arabic(ayah_text), fontsize=70, color='white', font='Arial', 
                       method='caption', size=(img.w*0.8, None), stroke_color='black', stroke_width=1)
        txt = txt.set_duration(audio.duration).set_position('center')

        final = CompositeVideoClip([img, txt]).set_audio(audio)
        output = f"reel_{chat_id}.mp4"
        final.write_videofile(output, fps=12, codec="libx264")

        # 5. إرسال الفيديو
        with open(output, 'rb') as v:
            bot.send_video(chat_id, v, caption=f"تم إنتاج الفيديو تلقائياً بواسطة @NameRefuserBot ✨")
        
        # تنظيف الملفات
        os.remove("temp.mp3")
        os.remove(output)
        os.remove(bg_image)

    except Exception:
        bot.reply_to(message, "❌ حدث خطأ، يرجى التأكد من رقم الآية.")

bot.infinity_polling()
