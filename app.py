import telebot
from telebot import types
import requests
import os
from moviepy.editor import ImageClip, TextClip, CompositeVideoClip, AudioFileClip
from arabic_reshaper import reshape
from bidi.algorithm import get_display
from moviepy.config import change_settings

# إعداد محرك النصوص للسيرفر
change_settings({"IMAGEMAGICK_BINARY": "/usr/bin/convert"})

TOKEN = "7857085752:AAE6XUInKJ-SpFkVxHhYDiI2RUKcs0DiwRo"
bot = telebot.TeleBot(TOKEN)

def fix_arabic(text):
    return get_display(reshape(text))

user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "📸 أهلاً بك في @NameRefuserBot\nمن فضلك **أرسل الصورة** التي تريدها كخلفية أولاً.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    user_image = f"bg_{chat_id}.jpg"
    with open(user_image, 'wb') as new_file:
        new_file.write(downloaded_file)
    
    user_data[chat_id] = {'image': user_image}
    
    markup = types.InlineKeyboardMarkup()
    qaris = {"المنشاوي": "ar.minshawi", "العفاسي": "ar.alafasy", "عبدالباسط": "ar.abdulsamad"}
    for name, code in qaris.items():
        markup.add(types.InlineKeyboardButton(name, callback_data=f"qari_{code}"))
    
    bot.send_message(chat_id, "✅ وصلت الصورة! الآن اختر القارئ:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('qari_'))
def select_qari(call):
    user_data[call.message.chat.id]['qari'] = call.data.split('_')[1]
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "📖 أرسل الآن رقم السورة والآية (مثال 1:1 أو 1.1)")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    chat_id = message.chat.id
    if chat_id not in user_data or 'image' not in user_data[chat_id]:
        bot.send_message(chat_id, "⚠️ يرجى إرسال الصورة أولاً قبل كتابة الأرقام!")
        return

    try:
        # إصلاح ذكي: تحويل النقطة إلى نقطتين عموديتين إذا وجدت
        text_input = message.text.replace('.', ':')
        surah, ayah = text_input.split(':')
        
        data = user_data[chat_id]
        bot.send_message(chat_id, "⏳ جاري دمج الآية مع صورتك... انتظر قليلاً")

        # جلب البيانات
        res = requests.get(f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah}/{data['qari']}").json()
        ayah_text = res['data']['text']
        audio_url = res['data']['audio']

        audio_content = requests.get(audio_url).content
        with open(f"s_{chat_id}.mp3", "wb") as f: f.write(audio_content)
        audio = AudioFileClip(f"s_{chat_id}.mp3")

        img = ImageClip(data['image']).set_duration(audio.duration).resize(width=1080)
        txt = TextClip(fix_arabic(ayah_text), fontsize=70, color='white', font='Arial', method='caption', size=(img.w*0.8, None))
        txt = txt.set_duration(audio.duration).set_position('center')

        final = CompositeVideoClip([img, txt]).set_audio(audio)
        output = f"vid_{chat_id}.mp4"
        final.write_videofile(output, fps=10, codec="libx264")

        with open(output, 'rb') as v:
            bot.send_video(chat_id, v, caption="تم التصميم بواسطة @NameRefuserBot ✨")
        
        os.remove(f"s_{chat_id}.mp3")
        os.remove(output)

    except Exception:
        bot.send_message(chat_id, "❌ تأكد من اختيار القارئ وكتابة الأرقام بشكل صحيح (مثال 1:1)")

bot.infinity_polling()
