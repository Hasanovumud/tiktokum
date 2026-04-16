import os
import logging
import yt_dlp
import asyncio
import requests
from flask import Flask
from threading import Thread

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# --- RENDER-DƏ OYAQ QALMAQ ÜÇÜN ---
server = Flask('')

@server.route('/')
def home():
    return "Bot aktivdir!"

def run():
    server.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- AYARLAR ---
TOKEN = "8706775383:AAH1666R0aetr06kiur612nxXgfiklj-H8E"
AUDD_API_KEY = "1beceba87cfc9c253cee5787c2513e65"
BOT_USERNAME = "@SonicDownloaderBot"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- DİL SİSTEMİ ---
LANGUAGES = {
    'az': {
        'name': '🇦🇿 Azərbaycan', 'start': 'Dil seçildi!', 'shazam': '🎵 Mahnı Tap', 'dl': '📥 Video/Mahnı Yüklə', 'help': '🆘 Kömək',
        'wait': 'Yüklənir... ⏳', 'find': 'Axtarılır... 🔎', 'not_found': 'Təəssüf ki, tapılmadı 😕', 'error': 'Xəta baş verdi! ❌',
        'voice_req': '🎤 Mahnını tapmaq üçün səs yazısı göndərin.', 'link_req': '📥 Yükləmək üçün link və ya mahnı adı göndərin.', 
        'thanks': 'Kömək etdiyimə şadam! ❤️', 'ask_audio': '🎬 Video hazırdır! Mahnısını da (MP3) istəyirsən?', 'get_audio': '🎵 Bəli, MP3 yüklə'
    },
    'tr': {
        'name': '🇹🇷 Türkçe', 'start': 'Dil seçildi!', 'shazam': '🎵 Şarkı Bul', 'dl': '📥 Video/Müzik İndir', 'help': '🆘 Yardım',
        'wait': 'İndiriliyor... ⏳', 'find': 'Aranıyor... 🔎', 'not_found': 'Maalesef bulunamadı 😕', 'error': 'Bir hata oluştu! ❌',
        'voice_req': '🎤 Şarkıyı bulmak için ses kaydı gönderin.', 'link_req': '📥 İndirmek için bağlantı veya şarkı ismi gönderin.', 
        'thanks': 'Yardımcı olduğuma sevindim! ❤️', 'ask_audio': '🎬 Video hazır! Müziğini de (MP3) ister misin?', 'get_audio': '🎵 Evet, MP3 indir'
    },
    'en': {
        'name': '🇺🇸 English', 'start': 'Language set!', 'shazam': '🎵 Find Song', 'dl': '📥 Download Media', 'help': '🆘 Help',
        'wait': 'Downloading... ⏳', 'find': 'Searching... 🔎', 'not_found': 'Not found 😕', 'error': 'Error occurred! ❌',
        'voice_req': '🎤 Send a voice note.', 'link_req': '📥 Send a link or song name.', 
        'thanks': 'Happy to help! ❤️', 'ask_audio': '🎬 Video is ready! Do you want the audio (MP3) too?', 'get_audio': '🎵 Yes, download MP3'
    }
}

user_prefs = {}

# --- FUNKSİYALAR ---
def get_main_buttons(lang_code):
    l = LANGUAGES.get(lang_code, LANGUAGES['az'])
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(l['shazam'], callback_data='act_shazam')],
        [InlineKeyboardButton(l['dl'], callback_data='act_dl')],
        [InlineKeyboardButton(l['help'], url="tg://user?id=8446711093")]
    ])

def get_lang_keyboard():
    keyboard = []
    keys = list(LANGUAGES.keys())
    for i in range(0, len(keys), 2):
        row = [InlineKeyboardButton(LANGUAGES[keys[i]]['name'], callback_data=f"l_{keys[i]}")]
        if i+1 < len(keys):
            row.append(InlineKeyboardButton(LANGUAGES[keys[i+1]]['name'], callback_data=f"l_{keys[i+1]}"))
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

async def download_video(query):
    if not query.startswith("http"):
        query = f"ytsearch1:{query}"
    v_file = "video.mp4"
    if os.path.exists(v_file): os.remove(v_file)
    opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': 'video.%(ext)s',
        'quiet': True, 'noplaylist': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'extractor_args': {'tiktok': {'impersonate': True}},
    }
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(opts).download([query]))
        return v_file if os.path.exists(v_file) else None
    except: return None

async def download_audio(query):
    if not query.startswith("http"):
        query = f"ytsearch1:{query}"
    a_file = "audio.mp3"
    if os.path.exists("audio.mp3"): os.remove("audio.mp3")
    opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
        'outtmpl': 'audio',
        'quiet': True, 'noplaylist': True,
    }
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(opts).download([query]))
        return a_file if os.path.exists(a_file) else None
    except: return None

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please choose a language / Dil seçin:", reply_markup=get_lang_keyboard())

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    
    lang = user_prefs.get(user_id, 'az')
    l = LANGUAGES.get(lang, LANGUAGES['az'])

    if query.data.startswith('l_'):
        lang = query.data.split('_')[1]
        user_prefs[user_id] = lang
        await query.edit_message_text(text=LANGUAGES[lang]['start'], reply_markup=get_main_buttons(lang))
        
    elif query.data == 'act_shazam':
        await query.message.reply_text(l['voice_req'])
        
    elif query.data == 'act_dl':
        await query.message.reply_text(l['link_req'])
        
    elif query.data.startswith('getmp3_'):
        # Düyməyə basıldıqda yalnız audio yüklənir
        original_query = context.user_data.get('last_query')
        if not original_query:
            await query.message.reply_text("Məlumat tapılmadı. Zəhmət olmasa linki yenidən göndərin.")
            return

        await query.message.reply_text(l['wait'])
        audio = await download_audio(original_query)
        if audio:
            with open(audio, 'rb') as f:
                await context.bot.send_audio(chat_id=query.message.chat_id, audio=f, caption=f"🎵 {BOT_USERNAME}")
            os.remove(audio)
        else:
            await query.message.reply_text(l['error'])

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    lang = user_prefs.get(user_id, 'az')
    l = LANGUAGES.get(lang, LANGUAGES['az'])
    text = update.message.text

    # Son göndərilən linki yadda saxlayırıq ki, audio istəyəndə istifadə edək
    context.user_data['last_query'] = text

    try: await update.message.set_reaction(reaction="👀")
    except: pass
    
    await context.bot.send_chat_action(chat_id=update.message.chat_id, action="upload_video")

    video = await download_video(text)

    if video:
        # 1. Videonu göndər
        with open(video, 'rb') as vf:
            await context.bot.send_video(
                chat_id=update.message.chat_id, 
                video=vf, 
                caption=f"✅ {l['thanks']}\n\n🤖 {BOT_USERNAME}"
            )
        os.remove(video)
        
        # 2. Audio sualını göndər (DİQQƏT: Musiqini bura əlavə etmirik!)
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(l['get_audio'], callback_data=f"getmp3_now")]
        ])
        await update.message.reply_text(l['ask_audio'], reply_markup=keyboard)
        
        try: await update.message.set_reaction(reaction="✅")
        except: pass
    else:
        await update.message.reply_text(l['error'])

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    lang = user_prefs.get(user_id, 'az')
    l = LANGUAGES.get(lang, LANGUAGES['az'])
    msg = await update.message.reply_text(l['find'])
    file = await (update.message.voice or update.message.audio).get_file()
    path = f"s_{user_id}.ogg"
    await file.download_to_drive(path)
    
    try:
        res = requests.post('https://api.audd.io/', data={'api_token': AUDD_API_KEY}, files={'file': open(path, 'rb')}).json()
        if res.get('status') == 'success' and res.get('result'):
            r = res['result']
            await msg.edit_text(f"🎧 {r['title']} - {r['artist']}", reply_markup=get_main_buttons(lang))
        else:
            await msg.edit_text(l['not_found'], reply_markup=get_main_buttons(lang))
    except:
        await msg.edit_text(l['error'])
        
    if os.path.exists(path): os.remove(path)

# --- İŞƏ SALMA ---
def main():
    keep_alive() 
    app = Application.builder().token(TOKEN).connect_timeout(40).read_timeout(40).write_timeout(40).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))

    print("Bot stabil rejimdə aktivdir...")
    app.run_polling(drop_pending_updates=True, timeout=30, bootstrap_retries=10)

if __name__ == "__main__":
    main()
