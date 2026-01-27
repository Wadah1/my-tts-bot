import telebot
from telebot import types
import requests
import os
from moviepy.editor import ImageClip, TextClip, CompositeVideoClip, AudioFileClip
from arabic_reshaper import reshape
from bidi.algorithm import get_display

# التوكن الجديد الذي أرسلته
TOKEN = "7857085752:AAE6XUInKJ-SpFkVxHhYDiI2RUKcs0DiwRo"
bot = telebot.TeleBot(TOKEN)

# قائمة القراء المتاحة
qaris = {
    "الشيخ المنشاوي": "ar.minshawi",
    "مشاري العفاسي": "ar.alafasy",
    "الشيخ عبدالباسط": "ar.abdulsamad"
}

# عينة من السور للبدء بها
surahs = {
    "الفاتحة": 1,
    "الإخلاص": 112,
    "الفلق": 113,
    "الناس": 114
}

user_data = {}

def fix_arabic(text):
    """إصلاح عرض النصوص العربية في الفيديو"""
    return get_display(reshape(text))

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    for name in qaris.keys():
        markup.add(types.InlineKeyboardButton(name, callback_data=f"qari_{qaris[name]}"))
    bot.send_message(message.chat.id, "✨ مرحباً بك في بوت @NameRefuserBot ✨\n\nيرجى اختيار القارئ أولاً:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('qari_'))
def select_qari(call):
    user_data[call.message.chat.id] = {'qari': call.data.split('_')[1]}
    bot.answer_callback_query(call.id)
    
    markup = types.InlineKeyboardMarkup()
    for name, s_id in surahs.items():
        markup.add(types.InlineKeyboardButton(name, callback_data=f"surah_{s_id}"))
    bot.edit_message_text("📖 اختر السورة الآن:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('surah_'))
def select_surah(call):
    user_data[call.message.chat.id]['surah'] = call.data.split('_')[1]
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "🔢 أرسل رقم الآية التي تريدها (مثال: 1)")

@bot.message_handler(func=lambda message: True)
def create_video(message):
    chat_id = message.chat.id
    if chat_id not in user_data or 'surah' not in user_data[chat_id]:
        bot.reply_to(message, "يرجى اختيار القارئ والسورة عبر أمر /start أولاً.")
        return

    try:
        ayah = message.text
        surah = user_data[chat_id]['surah']
        qari = user_data[chat_id]['qari']
        
        bot.send_message(chat_id, "⏳ جاري جلب البيانات وإنتاج الفيديو... انتظر قليلاً")

        # جلب البيانات من API القرآن
        res = requests.get(f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah}/{qari}").json()
        ayah_text = res['data']['text']
        audio_url = res['data']['audio']

        # تحميل الملف الصوتي
        audio_content = requests.get(audio_url).content
        with open("temp.mp3", "wb") as f: f.write(audio_content)
        audio = AudioFileClip("temp.mp3")

        # التحقق من وجود صورة الخلفية
        if not os.path.exists("background.jpg"):
            bot.send_message(chat_id, "❌ خطأ: لم يتم العثور على ملف 'background.jpg' في الاستضافة.")
            return

        # معالجة المونتاج على صورة ثابتة لسرعة الإنجاز
        img = ImageClip("background.jpg").set_duration(audio.duration).resize(width=1080)
        txt = TextClip(fix_arabic(ayah_text), fontsize=65, color='white', font='Arial', method='caption', size=(img.w*0.8, None))
        txt = txt.set_duration(audio.duration).set_position('center')

        final = CompositeVideoClip([img, txt]).set_audio(audio)
        output = f"reel_{chat_id}.mp4"
        final.write_videofile(output, fps=10, codec="libx264")

        # إرسال الفيديو النهائي
        with open(output, 'rb') as v:
            bot.send_video(chat_id, v, caption=f"تم إنتاج الفيديو بنجاح بواسطة @NameRefuserBot ✨")
        
        # حذف الملفات المؤقتة لتوفير مساحة الاستضافة
        os.remove("temp.mp3")
        os.remove(output)

    except Exception:
        bot.reply_to(message, "❌ تأكد من إدخال رقم الآية بشكل صحيح.")

bot.infinity_polling()
