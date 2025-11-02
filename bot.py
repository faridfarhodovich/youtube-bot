import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
import yt_dlp

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# TOKEN
TOKEN = '8347924509:AAFTywOTU61zKsxThjDF4NjLEyE6_qLLhJU'

# Papka
DOWNLOAD_DIR = '/tmp/downloads'  # Fly.io da /tmp tez va bepul
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# yt-dlp sozlamalari (CAPTCHA + TEZLIK)
ydl_opts = {
    'quiet': True,
    'no_warnings': True,
    'format': 'best',
    'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
    'merge_output_format': 'mp4',
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'sleep_interval': 1,
    'max_sleep_interval': 3,
    'retries': 3,
    'fragment_retries': 3,
    'http_headers': {
        'Accept-Language': 'en-US,en;q=0.9',
    },
}

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "YouTube Downloader\n\n"
        "Link yuboring → MP3 yoki Video yuklayman!\n"
        "Tez va xatosiz ishlaydi",
        disable_web_page_preview=True
    )

# Link qabul qilish
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not ('youtube.com' in url or 'youtu.be' in url):
        await update.message.reply_text("Faqat YouTube linki!")
        return

    context.user_data['url'] = url
    keyboard = [
        [InlineKeyboardButton("MP3", callback_data='mp3')],
        [InlineKeyboardButton("Video", callback_data='video')]
    ]
    await update.message.reply_text(
        "Format tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Tugmalar
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    url = context.user_data.get('url')
    if query.data == 'mp3':
        await query.edit_message_text("MP3 yuklanmoqda...")
        await download_mp3(query, url)
    elif query.data == 'video':
        await query.edit_message_text("Sifatlar tekshirilmoqda...")
        await show_qualities(query, url)

# MP3 yuklash
async def download_mp3(query, url):
    opts = ydl_opts.copy()
    opts.update({
        'format': 'bestaudio',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    })
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info['title'][:60]
        for f in os.listdir(DOWNLOAD_DIR):
            if f.endswith('.mp3'):
                path = os.path.join(DOWNLOAD_DIR, f)
                if os.path.getsize(path) < 50*1024*1024:
                    with open(path, 'rb') as audio:
                        await query.message.reply_audio(audio, caption=f"{title}")
                os.remove(path)
                break
        await query.edit_message_text("MP3 yuborildi!")
    except Exception as e:
        await query.edit_message_text(f"Xato: {str(e)[:80]}")

# Sifatlar
async def show_qualities(query, url):
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        heights = {f['height'] for f in info['formats'] if f.get('height')}
        buttons = [[InlineKeyboardButton(f"{h}p", callback_data=f"vid_{h}")] for h in sorted(heights, reverse=True)[:5]]
        await query.edit_message_text("Sifat tanlang:", reply_markup=InlineKeyboardMarkup(buttons))
    except:
        await query.edit_message_text("Sifat topilmadi. MP3 yuklab ko'ring.")

# Video yuklash
async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    res = query.data.split('_')[1]
    url = context.user_data.get('url')
    await query.edit_message_text(f"{res}p yuklanmoqda...")
    opts = ydl_opts.copy()
    opts['format'] = f'best[height<={res}][ext=mp4]/best'
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info['title']
        for f in os.listdir(DOWNLOAD_DIR):
            if f.endswith(('.mp4', '.webm')):
                path = os.path.join(DOWNLOAD_DIR, f)
                if os.path.getsize(path) < 2*1024*1024*1024:
                    with open(path, 'rb') as video:
                        await query.message.reply_video(video, caption=f"{title} - {res}p")
                os.remove(path)
                break
        await query.edit_message_text("Video yuborildi!")
    except Exception as e:
        await query.edit_message_text(f"Xato: {str(e)[:80]}")

# Asosiy
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button, pattern='^(mp3|video)$'))
    app.add_handler(CallbackQueryHandler(download_video, pattern='^vid_'))
    print("Bot ishga tushdi (Fly.io)")
    app.run_polling()

if __name__ == '__main__':
    main()
