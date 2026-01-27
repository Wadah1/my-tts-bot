import telebot
from telebot import types
import requests
import os
from moviepy.editor import ImageClip, TextClip, CompositeVideoClip, AudioFileClip
from arabic_reshaper import reshape
from bidi.algorithm import get_display

TOKEN = "7857085752:AAE6XUInKJ-SpFkVxHhYDiI2RUKcs0DiwRo"
bot = telebot.TeleBot(TOKEN)

# إعدادات معالجة النص العربي
def fix_arabic(text):
    return get_display(reshape(text))

user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "📸 أهلاً بك! أولاً أرسل لي **الصورة** التي تريدها كخلفية للفيديو.")

# 1. استقبال الصورة وحفظها
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    # حفظ الصورة باسم خاص لكل مستخدم
    user_image = f"bg_{chat_id}.jpg"
    with open(user_image, 'wb') as new_file:
        new_file.write(downloaded_file)
    
    user_data[chat_id] = {'image': user_image}
    
    # عرض قائمة القراء بعد استلام الصورة
    markup = types.InlineKeyboardMarkup()
    qaris = {"المنشاوي": "ar.minshawi", "العفاسي": "ar.alafasy", "عبدالباسط": "ar.abdulsamad"}
    for name, code in qaris.items():
        markup.add(types.InlineKeyboardButton(name, callback_data=f"qari_{code}"))
    
    bot.send_message(chat_id, "✅ تم حفظ الصورة! الآن اختر القارئ:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('qari_'))
def select_qari(call):
    user_data[call.message.chat.id]['qari'] = call.data.split('_')[1]
    bot.send_message(call.message.chat.id, "📖 أرسل رقم السورة والآية (مثال 1:1)")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    chat_id = message.chat.id
    if chat_id not in user_data or 'image' not in user_data[chat_id]:
        bot.send_message(chat_id, "⚠️ من فضلك أرسل الصورة أولاً!")
        return

    try:
        surah, ayah = message.text.split(':')
        data = user_data[chat_id]
        
        bot.send_message(chat_id, "⏳ جاري دمج الآية مع صورتك... انتظر قليلاً")

        # جلب البيانات
        res = requests.get(f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah}/{data['qari']}").json()
        text = res['data']['text']
        audio_url = res['data']['audio']

        # تحميل الصوت
        audio_content = requests.get(audio_url).content
        with open(f"sound_{chat_id}.mp3", "wb") as f: f.write(audio_content)
        audio = AudioFileClip(f"sound_{chat_id}.mp3")

        # المونتاج على صورة المستخدم
        img = ImageClip(data['image']).set_duration(audio.duration).resize(width=1080)
        txt = TextClip(fix_arabic(text), fontsize=70, color='white', font='Arial', method='caption', size=(img.w*0.8, None))
        txt = txt.set_duration(audio.duration).set_position('center')

        final = CompositeVideoClip([img, txt]).set_audio(audio)
        output = f"result_{chat_id}.mp4"
        final.write_videofile(output, fps=10, codec="libx264")

        # إرسال الفيديو
        with open(output, 'rb') as v:
            bot.send_video(chat_id, v, caption="تم التصميم بصورتك الخاصة عبر @NameRefuserBot ✨")
        
        # تنظيف الملفات
        os.remove(f"sound_{chat_id}.mp3")
        os.remove(output)

    except:
        bot.send_message(chat_id, "❌ خطأ في البيانات! تأكد من الصيغة سورة:آية")

bot.infinity_polling()
