import os
import requests
import subprocess
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("8467711253:AAGDIKhqHjcLn5zDAd_8JrPppDQysecYjZU")

# تحميل صورة طبيعة
def download_nature_image():
    url = "https://source.unsplash.com/1080x1920/?nature"
    img_path = "bg.jpg"
    with open(img_path, "wb") as f:
        f.write(requests.get(url).content)
    return img_path

# تحميل صوت التلاوة
def download_audio(audio_url):
    audio_path = "audio.mp3"
    with open(audio_path, "wb") as f:
        f.write(requests.get(audio_url).content)
    return audio_path

# إنشاء الفيديو
def create_video(image, audio, text):
    video_path = "output.mp4"

    cmd = [
        "ffmpeg",
        "-y",
        "-loop", "1",
        "-i", image,
        "-i", audio,
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        "-vf",
        f"scale=1080:1920,drawtext=text='{text}':fontcolor=white:fontsize=48:box=1:boxcolor=black@0.5:boxborderw=20:x=(w-text_w)/2:y=h-300",
        video_path
    ]

    subprocess.run(cmd, check=True)
    return video_path

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 بوت فيديوهات القرآن\n\n"
        "استخدم:\n"
        "/ayah رقم_السورة رقم_الآية\n\n"
        "مثال:\n"
        "/ayah 1 1"
    )

async def ayah(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        surah = context.args[0]
        ayah = context.args[1]

        api = f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah}/ar.alafasy"
        data = requests.get(api).json()["data"]

        text = data["text"].replace("'", "")
        audio_url = data["audio"]

        await update.message.reply_text("⏳ جاري إنشاء الفيديو...")

        image = download_nature_image()
        audio = download_audio(audio_url)
        video = create_video(image, audio, text)

        await update.message.reply_video(video=open(video, "rb"))

    except Exception as e:
        await update.message.reply_text("❌ حدث خطأ، تأكد من الأمر")
        print(e)

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ayah", ayah))
    app.run_polling()
