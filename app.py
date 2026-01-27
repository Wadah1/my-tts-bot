import telebot
from telebot import types
import requests
import os

TOKEN = "7857085752:AAE6XUInKJ-SpFkVxHhYDiI2RUKcs0DiwRo"
bot = telebot.TeleBot(TOKEN)

user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "📸 أهلاً بك في @NameRefuserBot\nأرسل **الصورة** التي تريدها أولاً.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    img_path = f"img_{chat_id}.jpg"
    with open(img_path, 'wb') as f: f.write(downloaded_file)
    user_data[chat_id] = {'image': img_path}
    
    markup = types.InlineKeyboardMarkup()
    qaris = {"المنشاوي": "ar.minshawi", "العفاسي": "ar.alafasy", "عبدالباسط": "ar.abdulsamad"}
    for name, code in qaris.items():
        markup.add(types.InlineKeyboardButton(name, callback_data=f"q_{code}"))
    bot.send_message(chat_id, "✅ تم استلام الصورة! اختر القارئ:", reply_markup=markup)

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
def send_audio_with_image(call):
    chat_id = call.message.chat.id
    selection = call.data.split('_')[1]
    bot.answer_callback_query(call.id)
    surah, ayah = selection.split(':')
    data = user_data[chat_id]
    
    bot.send_message(chat_id, "⏳ جاري جلب الآية والصوت...")

    try:
        # جلب البيانات من API القرآن
        res = requests.get(f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah}/{data['qari']}").json()
        ayah_text = res['data']['text']
        audio_url = res['data']['audio']

        # 1. إرسال الصورة أولاً
        with open(data['image'], 'rb') as photo:
            bot.send_photo(chat_id, photo, caption=f"📖 {ayah_text}")

        # 2. إرسال ملف الصوت
        audio_content = requests.get(audio_url).content
        bot.send_voice(chat_id, audio_content, caption="بصوت القارئ المختار ✨")

    except:
        bot.send_message(chat_id, "❌ حدث خطأ في الاتصال، حاول مرة أخرى.")

bot.infinity_polling()
