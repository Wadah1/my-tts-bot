import telebot
from telebot import types
import requests
import os
from moviepy.editor import ImageClip, TextClip, CompositeVideoClip, AudioFileClip
from arabic_reshaper import reshape
from bidi.algorithm import get_display
from moviepy.config import change_settings

# إعداد مسار ImageMagick للسيرفر
try:
    change_settings({"IMAGEMAGICK_BINARY": "/usr/bin/convert"})
except:
    pass

TOKEN = "7857085752:AAE6XUInKJ-SpFkVxHhYDiI2RUKcs0DiwRo"
bot = telebot.TeleBot(TOKEN)

def fix_arabic(text):
    return get_display(reshape(text))

user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "📸 مرحباً! أولاً: أرسل لي **الصورة** التي تريدها كخلفية.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    img_path = f"bg_{chat_id}.jpg"
    with open(img_path, 'wb') as f:
        f.write(downloaded_file)
    
    user_data[chat_id] = {'image': img_path}
    
    markup = types.InlineKeyboardMarkup()
    qaris = {"المنشاوي": "ar.minshawi", "العفاسي": "ar.alafasy", "عبدالباسط": "ar.abdulsamad"}
    for name, code in qaris.items():
        markup.add(types.InlineKeyboardButton(name, callback_data=f"qari_{code}"))
    
    bot.send_message(chat_id, "✅ تم حفظ الصورة! اختر الآن القارئ:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('qari_'))
def select_qari(call):
    user_data[call.message.chat.id]['qari'] = call.data.split('_')[1]
    bot.send_message(call.message.chat.id, "📖 أرسل رقم السورة والآية بصيغة (سورة:آية) مثال 1:1")

@bot.message_handler(func=lambda message: True)
def process_video(message):
    chat_id = message.chat.id
    if chat_id not in user_data or 'image' not in user_data[chat_id]:
        bot.send_message(chat_id, "⚠️ أرسل صورة أولاً!")
        return

    try:
        # تحويل أي شكل للأرقام إلى الصيغة المطلوبة
        raw_text = message.text.replace('.', ':').replace(' ', '')
        surah, ayah = raw_text.split(':')
        
        bot.send_message(chat_id, "⏳ جاري المعالجة... قد تستغرق دقيقة")
        
        # جلب البيانات
        res = requests.get(f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah}/{user_data[chat_id]['qari']}").json()
        ayah_text = res['data']['text']
        audio_url = res['data']['audio']

        # تحميل الصوت
        audio_content = requests.get(audio_url).content
        audio_path = f"s_{chat_id}.mp3"
        with open(audio_path, "wb") as f: f.write(audio_content)
        
        audio = AudioFileClip(audio_path)
        img = ImageClip(user_data[chat_id]['image']).set_duration(audio.duration).resize(width=1080)
        
        txt = TextClip(fix_arabic(ayah_text), fontsize=60, color='white', font='Arial', 
                       method='caption', size=(img.w*0.8, None))
        txt = txt.set_duration(audio.duration).set_position('center')

        final = CompositeVideoClip([img, txt]).set_audio(audio)
        out = f"res_{chat_id}.mp4"
        final.write_videofile(out, fps=10, codec="libx264")

        with open(out, 'rb') as v:
            bot.send_video(chat_id, v, caption="تم الإنتاج بواسطة @NameRefuserBot")
        
        os.remove(audio_path)
        os.remove(out)
    except Exception as e:
        bot.send_message(chat_id, "❌ خطأ! تأكد من إرسال الصورة أولاً ثم كتابة (رقم السورة:رقم الآية)")

bot.infinity_polling()
