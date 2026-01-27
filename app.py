import telebot
from telebot import types
import requests
import os
from moviepy.editor import ImageClip, TextClip, CompositeVideoClip, AudioFileClip
from arabic_reshaper import reshape
from bidi.algorithm import get_display
from moviepy.config import change_settings

# إعداد محرك النصوص للسيرفر
try:
    change_settings({"IMAGEMAGICK_BINARY": "/usr/bin/convert"})
except:
    pass

TOKEN = "7857085752:AAE6XUInKJ-SpFkVxHhYDiI2RUKcs0DiwRo"
bot = telebot.TeleBot(TOKEN)

def fix_arabic(text):
    return get_display(reshape(text))

user_data = {}

# قائمة القراء
qaris = {"المنشاوي": "ar.minshawi", "العفاسي": "ar.alafasy", "عبدالباسط": "ar.abdulsamad"}

# قائمة السور المختارة (يمكنك زيادتها لاحقاً)
surahs_list = {
    "الفاتحة": "1",
    "الإخلاص": "112",
    "الفلق": "113",
    "الناس": "114",
    "الكرسي (آية)": "2:255"
}

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "📸 أهلاً بك في بوت @NameRefuserBot\n\nمن فضلك **أرسل الصورة** التي تريدها كخلفية أولاً.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    img_path = f"bg_{chat_id}.jpg"
    with open(img_path, 'wb') as f:
        f.write(downloaded_file)
    
    user_data[chat_id] = {'image': img_path}
    
    # إنشاء أزرار القراء
    markup = types.InlineKeyboardMarkup()
    for name, code in qaris.items():
        markup.add(types.InlineKeyboardButton(name, callback_data=f"q_{code}"))
    
    bot.send_message(chat_id, "✅ تم حفظ الصورة! اختر الآن القارئ:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('q_'))
def select_qari(call):
    chat_id = call.message.chat.id
    user_data[chat_id]['qari'] = call.data.split('_')[1]
    bot.answer_callback_query(call.id)
    
    # إنشاء أزرار السور
    markup = types.InlineKeyboardMarkup()
    for name, code in surahs_list.items():
        markup.add(types.InlineKeyboardButton(name, callback_data=f"s_{code}"))
    
    bot.edit_message_text("📖 الآن اختر السورة أو الآية من القائمة:", chat_id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('s_'))
def process_video_step(call):
    chat_id = call.message.chat.id
    selection = call.data.split('_')[1]
    bot.answer_callback_query(call.id)
    
    # تحديد السورة والآية
    if ":" in selection:
        surah, ayah = selection.split(':')
    else:
        surah, ayah = selection, "1" # الافتراضي الآية الأولى

    data = user_data[chat_id]
    bot.send_message(chat_id, "⏳ جاري إنتاج الفيديو الخاص بك... انتظر قليلاً")

    try:
        # جلب البيانات
        res = requests.get(f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah}/{data['qari']}").json()
        ayah_text = res['data']['text']
        audio_url = res['data']['audio']

        # تحميل الصوت
        audio_path = f"audio_{chat_id}.mp3"
        with open(audio_path, "wb") as f:
            f.write(requests.get(audio_url).content)
        
        audio = AudioFileClip(audio_path)
        img = ImageClip(data['image']).set_duration(audio.duration).resize(width=1080)
        
        txt = TextClip(fix_arabic(ayah_text), fontsize=60, color='white', font='Arial', 
                       method='caption', size=(img.w*0.8, None))
        txt = txt.set_duration(audio.duration).set_position('center')

        final = CompositeVideoClip([img, txt]).set_audio(audio)
        out_file = f"video_{chat_id}.mp4"
        final.write_videofile(out_file, fps=10, codec="libx264")

        with open(out_file, 'rb') as v:
            bot.send_video(chat_id, v, caption="تم التصميم بواسطة @NameRefuserBot ✨")
        
        os.remove(audio_path)
        os.remove(out_file)
    except Exception as e:
        bot.send_message(chat_id, "❌ حدث خطأ أثناء المعالجة، حاول مرة أخرى.")

bot.infinity_polling()
