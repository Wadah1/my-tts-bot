import telebot
from telebot import types
import requests
import os
from moviepy.editor import ImageClip, TextClip, CompositeVideoClip, AudioFileClip
from moviepy.config import change_settings
from arabic_reshaper import reshape
from bidi.algorithm import get_display

# أمر حيوي لحل مشكلة السيرفر
change_settings({"IMAGEMAGICK_BINARY": "/usr/bin/convert"})

TOKEN = "7857085752:AAE6XUInKJ-SpFkVxHhYDiI2RUKcs0DiwRo"
bot = telebot.TeleBot(TOKEN)

def fix_arabic(text):
    return get_display(reshape(text))

user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "📸 أهلاً بك! أرسل **الصورة** أولاً لتكون خلفية للفيديو.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    img_path = f"bg_{chat_id}.jpg"
    with open(img_path, 'wb') as f: f.write(downloaded_file)
    user_data[chat_id] = {'image': img_path}
    
    markup = types.InlineKeyboardMarkup()
    qaris = {"المنشاوي": "ar.minshawi", "العفاسي": "ar.alafasy", "عبدالباسط": "ar.abdulsamad"}
    for name, code in qaris.items():
        markup.add(types.InlineKeyboardButton(name, callback_data=f"q_{code}"))
    bot.send_message(chat_id, "✅ الصورة جاهزة! اختر القارئ:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('q_'))
def select_qari(call):
    user_data[call.message.chat.id]['qari'] = call.data.split('_')[1]
    bot.answer_callback_query(call.id)
    surahs_list = {"الفاتحة": "1:1", "الإخلاص": "112:1", "الفلق": "113:1", "الناس": "114:1", "الكرسي": "2:255"}
    markup = types.InlineKeyboardMarkup()
    for name, code in surahs_list.items():
        markup.add(types.InlineKeyboardButton(name, callback_data=f"s_{code}"))
    bot.edit_message_text("📖 اختر الآية الآن:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('s_'))
def make_video(call):
    chat_id = call.message.chat.id
    selection = call.data.split('_')[1]
    bot.answer_callback_query(call.id)
    surah, ayah = selection.split(':')
    data = user_data[chat_id]
    bot.send_message(chat_id, "⏳ جاري دمج الآية والصوت والصورة... انتظر دقيقة")

    try:
        # جلب البيانات
        res = requests.get(f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah}/{data['qari']}").json()
        ayah_text = res['data']['text']
        audio_url = res['data']['audio']

        audio_path = f"a_{chat_id}.mp3"
        with open(audio_path, "wb") as f: f.write(requests.get(audio_url).content)
        
        # إعدادات المونتاج
        audio = AudioFileClip(audio_path)
        img = ImageClip(data['image']).set_duration(audio.duration).resize(width=1080)
        
        # كتابة النص (استخدام طريقة تحمي الكود من التوقف)
        txt = TextClip(fix_arabic(ayah_text), fontsize=60, color='white', 
                       size=(img.w*0.8, None), method='caption', align='Center')
        txt = txt.set_duration(audio.duration).set_position('center')

        final = CompositeVideoClip([img, txt]).set_audio(audio)
        out = f"final_{chat_id}.mp4"
        final.write_videofile(out, fps=12, codec="libx264", audio_codec="aac")

        with open(out, 'rb') as v:
            bot.send_video(chat_id, v, caption=f"تم التصميم بواسطة @NameRefuserBot ✨")
        
        os.remove(audio_path)
        os.remove(out)
    except Exception as e:
        bot.send_message(chat_id, f"❌ خطأ: تأكد من ملف packages.txt وكتابة كلمة imagemagick فيه.")

bot.infinity_polling()
