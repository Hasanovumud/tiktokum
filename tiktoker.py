import os
import logging
import yt_dlp
import asyncio
import requests
import random
import json
import time
from flask import Flask
from threading import Thread

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# --- AYARLAR ---
TOKEN = "8706775383:AAH1666R0aetr06kiur612nxXgfiklj-H8E"
AUDD_API_KEY = "1beceba87cfc9c253cee5787c2513e65"
BOT_USERNAME = "@SonicDownloaderBot"
ADMIN_ID = 844671093  # Öz Telegram ID-ni bura dəqiq yaz

STICKER_LIST = [
    "CAACAgIAAxkBAAIefGngpL4tARSbMMqODfBvfOgBYhShAAIGlwACuWuhS33nS5UJOVG-OwQv",
    "CAACAgIAAxkBAAIeeGngpLrfYaVojr2xEiEmJa9ZXD8TAAJsQAACSUzRSqhPVcf-QsDwOwQ",
    "CAACAgIAAxkBAAIedmngpLhHWO9eSkwJvvVtB-xJswJ7AAJzhAAC78ZhS0pK43RtnEElOwQ",
    "CAACAgIAAxkBAAIedGngpLf1pwHEOSIO0cWfO-aRZxycAAI9iAAC_DFhS4xagEOuONg9OwQ"
]

# --- RENDER-DƏ OYAQ QALMAQ ---
server = Flask('')
@server.route('/')
def home(): return "Bot aktivdir!"
def run(): server.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- STATİSTİKA SİSTEMİ ---
STATS_FILE = "stats.json"

def load_stats():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r") as f: return json.load(f)
    return {"users": [], "total_downloads": 0}

def save_stats(stats):
    with open(STATS_FILE, "w") as f: json.dump(stats, f)

def log_user(user_id):
    stats = load_stats()
    if user_id not in stats["users"]:
        stats["users"].append(user_id)
        save_stats(stats)

def log_download():
    stats = load_stats()
    stats["total_downloads"] += 1
    save_stats(stats)

# --- PROGRESS BAR FUNKSİYASI ---
def get_pb(current, total):
    if not total: return "..."
    percent = current / total
    filled = int(10 * percent)
    bar = '█' * filled + '░' * (10 - filled)
    return f"[{bar}] {int(percent * 100)}%"

last_edit_time = 0

async def progress_callback(current, total, message, text_prefix):
    global last_edit_time
    now = time.time()
    if now - last_edit_time < 2: return # Telegram-ı yormamaq üçün 2 saniyədən bir yenilə
    
    pb = get_pb(current, total)
    try:
        await message.edit_text(f"{text_prefix}\n{pb}")
        last_edit_time = now
    except: pass

# --- DİLLƏR ---
LANGUAGES = {
    'az': {'name': '🇦🇿 Azərbaycan', 'start': 'Dil seçildi!', 'shazam': '🎵 Mahnı Tap', 'dl': '📥 Video/Mahnı Yüklə', 'wait': 'Yüklənir... ⏳', 'error': 'Xəta baş verdi! ❌', 'thanks': 'Kömək etdiyimə şadam! ❤️', 'ask_audio': '🎬 Video hazırdır! Mahnısını da (MP3) istəyirsən?', 'get_audio': '🎵 Bəli, MP3 yüklə', 'up': 'Göndərilir...'},
    'tr': {'name': '🇹🇷 Türkçe', 'start': 'Dil seçildi!', 'shazam': '🎵 Şarkı Bul', 'dl': '📥 Video/Müzik İndir', 'wait': 'İndiriliyor... ⏳', 'error': 'Bir hata oluştu! ❌', 'thanks': 'Yardımcı olduğuma sevindim! ❤️', 'ask_audio': '🎬 Video hazır! Müziğini de (MP3) ister misin?', 'get_audio': '🎵 Evet, MP3 indir', 'up': 'Gönderiliyor...'},
    'en': {'name': '🇺🇸 English', 'start': 'Language set!', 'shazam': '🎵 Find Song', 'dl': '📥 Download Media', 'wait': 'Downloading... ⏳', 'error': 'Error occurred! ❌', 'thanks': 'Happy to help! ❤️', 'ask_audio': '🎬 Video is ready! MP3 too?', 'get_audio': '🎵 Yes, download MP3', 'up': 'Uploading...'}
    # Digər dilləri eyni qayda ilə genişləndirə bilərsən
}

user_prefs = {}

# --- YÜKLƏMƏ FUNKSİYALARI ---
async def download_video(query):
    v_file = "video.mp4"
    if os.path.exists(v_file): os.remove(v_file)
    opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': 'video.%(ext)s', 'quiet': True, 'noplaylist': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'extractor_args': {'tiktok': {'impersonate': True}},
    }
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(opts).download([query if query.startswith("http") else f"ytsearch1:{query}"]))
        return v_file if os.path.exists(v_file) else None
    except: return None

async def download_audio(query):
    a_file = "audio.mp3"
    if os.path.exists(a_file): os.remove(a_file)
    opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
        'outtmpl': 'audio', 'quiet': True, 'noplaylist': True,
    }
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(opts).download([query if query.startswith("http") else f"ytsearch1:{query}"]))
        return a_file if os.path.exists(a_file) else None
    except: return None

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log_user(update.effective_user.id)
    await update.message.reply_text("Dil seçin / Choose language:", reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton(v['name'], callback_data=f"l_{k}")] for k, v in LANGUAGES.items()
    ]))

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    s = load_stats()
    text = f"📊 **Bot Statistikası**\n\n👤 İstifadəçilər: {len(s['users'])}\n📥 Cəmi yükləmə: {s['total_downloads']}"
    await update.message.reply_text(text, parse_mode="Markdown")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    lang = user_prefs.get(user_id, 'az')
    l = LANGUAGES.get(lang, LANGUAGES['az'])

    if query.data.startswith('l_'):
        lang = query.data.split('_')[1]
        user_prefs[user_id] = lang
        await query.edit_message_text(text=LANGUAGES[lang]['start'], reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(LANGUAGES[lang]['shazam'], callback_data='act_shazam')],
            [InlineKeyboardButton(LANGUAGES[lang]['dl'], callback_data='act_dl')]
        ]))
        
    elif query.data == 'getmp3_now':
        original_query = context.user_data.get('last_query')
        if not original_query: return
        
        sticker_msg = await context.bot.send_sticker(chat_id=query.message.chat_id, sticker=random.choice(STICKER_LIST))
        progress_msg = await query.message.reply_text(f"{l['wait']}")
        
        audio = await download_audio(original_query)
        if audio:
            await progress_msg.edit_text(l['up'])
            with open(audio, 'rb') as f:
                await context.bot.send_audio(
                    chat_id=query.message.chat_id, 
                    audio=f, 
                    caption=f"🎵 {BOT_USERNAME}",
                    progress_callback=lambda c, t: progress_callback(c, t, progress_msg, l['up'])
                )
            os.remove(audio)
            log_download()
            await context.bot.delete_message(chat_id=query.message.chat_id, message_id=sticker_msg.message_id)
            await progress_msg.delete()
        else:
            await progress_msg.edit_text(l['error'])

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    log_user(user_id)
    lang = user_prefs.get(user_id, 'az')
    l = LANGUAGES.get(lang, LANGUAGES['az'])
    text = update.message.text
    context.user_data['last_query'] = text

    try: await update.message.set_reaction(reaction="👀")
    except: pass
    
    status_msg = await update.message.reply_text(l['wait'])
    video = await download_video(text)

    if video:
        await status_msg.edit_text(l['up'])
        with open(video, 'rb') as vf:
            await context.bot.send_video(
                chat_id=update.message.chat_id, 
                video=vf, 
                caption=f"✅ {l['thanks']}\n\n🤖 {BOT_USERNAME}",
                progress_callback=lambda c, t: progress_callback(c, t, status_msg, l['up'])
            )
        os.remove(video)
        log_download()
        await status_msg.delete()
        
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(l['get_audio'], callback_data='getmp3_now')]])
        await update.message.reply_text(l['ask_audio'], reply_markup=keyboard)
        try: await update.message.set_reaction(reaction="✅")
        except: pass
    else:
        await status_msg.edit_text(l['error'])

# --- MAIN ---
def main():
    keep_alive()
    app = Application.builder().token(TOKEN).connect_timeout(40).read_timeout(40).write_timeout(40).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot başlatıldı...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
