import os
import logging
import yt_dlp
import asyncio
import requests
import random
import json
from flask import Flask
from threading import Thread

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# --- RENDER-DƏ OYAQ QALMAQ ÜÇÜN ---
server = Flask('')
@server.route('/')
def home(): return "Bot aktivdir!"
def run(): server.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# --- AYARLAR ---
TOKEN = "8706775383:AAH1666R0aetr06kiur612nxXgfiklj-H8E"
AUDD_API_KEY = "1beceba87cfc9c253cee5787c2513e65"
BOT_USERNAME = "@SonicDownloaderBot"
ADMIN_USERNAME = "UmudHasanovTM"
ADMIN_ID = 8446711093

STICKER_LIST = [
    "CAACAgIAAxkBAAIefGngpL4tARSbMMqODfBvfOgBYhShAAIGlwACuWuhS33nS5UJOVG-OwQv",
    "CAACAgIAAxkBAAIeeGngpLrfYaVojr2xEiEmJa9ZXD8TAAJsQAACSUzRSqhPVcf-QsDwOwQ",
    "CAACAgIAAxkBAAIedmngpLhHWO9eSkwJvvVtB-xJswJ7AAJzhAAC78ZhS0pK43RtnEElOwQ",
    "CAACAgIAAxkBAAIedGngpLf1pwHEOSIO0cWfO-aRZxycAAI9iAAC_DFhS4xagEOuONg9OwQ"
]

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- STATİSTİKA ---
DB_FILE = "users_db.json"
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f: return json.load(f)
    return {"users": [], "total_downloads": 0}

def save_db(db):
    with open(DB_FILE, "w") as f: json.dump(db, f)

def log_user(user_id):
    db = load_db()
    if user_id not in db["users"]:
        db["users"].append(user_id)
        save_db(db)

def log_download():
    db = load_db()
    db["total_downloads"] += 1
    save_db(db)

# --- DİLLƏR ---
LANGUAGES = {
    'az': {'name': '🇦🇿 Azərbaycan', 'start': 'Dil seçildi!', 'shazam': '🎵 Mahnı Tap', 'dl': '📥 Video/Mahnı Yüklə', 'help': '🆘 Kömək', 'wait': 'Yüklənir... ⏳', 'find': 'Axtarılır... 🔎', 'not_found': 'Təəssüf ki, tapılmadı 😕', 'error': 'Xəta baş verdi! ❌', 'voice_req': '🎤 Mahnını tapmaq üçün səs yazısı göndərin.', 'link_req': '📥 Yükləmək üçün link və ya mahnı adı göndərin.', 'thanks': 'Kömək etdiyimə şadam! ❤️', 'ask_audio': '🎬 Video hazırdır! Mahnısını da (MP3) istəyirsən?', 'get_audio': '🎵 Bəli, MP3 yüklə'},
    'tr': {'name': '🇹🇷 Türkçe', 'start': 'Dil seçildi!', 'shazam': '🎵 Şarkı Bul', 'dl': '📥 Video/Müzik İndir', 'help': '🆘 Yardım', 'wait': 'İndiriliyor... ⏳', 'find': 'Aranıyor... 🔎', 'not_found': 'Maalesef bulunamadı 😕', 'error': 'Bir hata oluştu! ❌', 'voice_req': '🎤 Şarkıyı bulmak için ses kaydı gönderin.', 'link_req': '📥 İndirmek için bağlantı veya şarkı ismi gönderin.', 'thanks': 'Yardımcı olduğuma sevindim! ❤️', 'ask_audio': '🎬 Video hazır! Müziğini de (MP3) ister misin?', 'get_audio': '🎵 Evet, MP3 indir'},
    'en': {'name': '🇺🇸 English', 'start': 'Language set!', 'shazam': '🎵 Find Song', 'dl': '📥 Download Media', 'help': '🆘 Help', 'wait': 'Downloading... ⏳', 'find': 'Searching... 🔎', 'not_found': 'Not found 😕', 'error': 'Error occurred! ❌', 'voice_req': '🎤 Send a voice note.', 'link_req': '📥 Send a link or song name.', 'thanks': 'Happy to help! ❤️', 'ask_audio': '🎬 Video is ready! Do you want the audio (MP3) too?', 'get_audio': '🎵 Yes, download MP3'}
}

user_prefs = {}

# --- YÜKLƏMƏ FUNKSİYALARI (BLOKLARI KEÇMƏK ÜÇÜN) ---
def get_ytdlp_opts(is_audio=False):
    opts = {
        'quiet': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'no_warnings': True,
        'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    }
    if is_audio:
        opts.update({
            'format': 'bestaudio/best',
            'outtmpl': 'audio.%(ext)s',
        })
    else:
        opts.update({
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': 'video.%(ext)s',
        })
    return opts

async def download_video(query):
    opts = get_ytdlp_opts(is_audio=False)
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(opts).download([query if query.startswith("http") else f"ytsearch1:{query}"]))
        for ext in ['mp4', 'webm', 'mkv']:
            if os.path.exists(f"video.{ext}"): return f"video.{ext}"
    except: return None

async def download_audio(query):
    opts = get_ytdlp_opts(is_audio=True)
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(opts).download([query if query.startswith("http") else f"ytsearch1:{query}"]))
        for ext in ['m4a', 'mp3', 'webm', 'opus']:
            if os.path.exists(f"audio.{ext}"): return f"audio.{ext}"
    except: return None

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log_user(update.effective_user.id)
    await update.message.reply_text("Dil seçin / Choose language:", reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton(v['name'], callback_data=f"l_{k}")] for k, v in LANGUAGES.items()
    ]))

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = user_prefs.get(user_id, 'az')
    l = LANGUAGES.get(lang, LANGUAGES['az'])
    
    wait_msg = await update.message.reply_text(l['find'])
    file = await context.bot.get_file(update.message.voice.file_id if update.message.voice else update.message.audio.file_id)
    path = "shazam_temp.ogg"
    await file.download_to_drive(path)
    
    try:
        with open(path, 'rb') as f:
            res = requests.post('https://api.audd.io/', data={'api_token': AUDD_API_KEY}, files={'file': f}).json()
        
        if res.get('result'):
            result = res['result']
            query = f"{result['artist']} - {result['title']}"
            context.user_data['last_query'] = query
            await wait_msg.edit_text(f"🎵 {query}\n\n{l['ask_audio']}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(l['get_audio'], callback_data='getmp3_now')]]))
        else:
            await wait_msg.edit_text(l['not_found'])
    except:
        await wait_msg.edit_text(l['error'])
    finally:
        if os.path.exists(path): os.remove(path)

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    lang = user_prefs.get(user_id, 'az')
    l = LANGUAGES.get(lang, LANGUAGES['az'])

    if query.data.startswith('l_'):
        lang = query.data.split('_')[1]
        user_prefs[user_id] = lang
        await query.edit_message_text(text=l['start'], reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(l['shazam'], callback_data='act_shazam')],
            [InlineKeyboardButton(l['dl'], callback_data='act_dl')]
        ]))
    elif query.data == 'act_shazam': await query.message.reply_text(l['voice_req'])
    elif query.data == 'act_dl': await query.message.reply_text(l['link_req'])
    elif query.data == 'getmp3_now':
        last_q = context.user_data.get('last_query')
        if not last_q: return
        sticker = await context.bot.send_sticker(chat_id=query.message.chat_id, sticker=random.choice(STICKER_LIST))
        audio = await download_audio(last_q)
        if audio:
            log_download()
            with open(audio, 'rb') as f: await context.bot.send_audio(chat_id=query.message.chat_id, audio=f, caption=f"🎵 {BOT_USERNAME}")
            os.remove(audio)
        await context.bot.delete_message(chat_id=query.message.chat_id, message_id=sticker.message_id)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = user_prefs.get(user_id, 'az')
    l = LANGUAGES.get(lang, LANGUAGES['az'])
    text = update.message.text
    context.user_data['last_query'] = text
    
    wait_msg = await update.message.reply_text(l['wait'])
    video = await download_video(text)
    
    if video:
        log_download()
        with open(video, 'rb') as f: await context.bot.send_video(chat_id=update.message.chat_id, video=f, caption=f"✅ {l['thanks']}")
        os.remove(video)
        await update.message.reply_text(l['ask_audio'], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(l['get_audio'], callback_data='getmp3_now')]]))
        await wait_msg.delete()
    else:
        await wait_msg.edit_text(l['error'])

# --- MAIN ---
def main():
    keep_alive()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__": main()
