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

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler, InlineQueryHandler

# --- RENDER-DƏ OYAQ QALMAQ ---
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
ADMIN_ID = 6378413470 # Buranı öz ID-nlə yoxla

# STİKER SİYAHISI
STICKER_LIST = [
    "CAACAgIAAxkBAAIefGngpL4tARSbMMqODfBvfOgBYhShAAIGlwACuWuhS33nS5UJOVG-OwQv",
    "CAACAgIAAxkBAAIeeGngpLrfYaVojr2xEiEmJa9ZXD8TAAJsQAACSUzRSqhPVcf-QsDwOwQ",
    "CAACAgIAAxkBAAIedmngpLhHWO9eSkwJvvVtB-xJswJ7AAJzhAAC78ZhS0pK43RtnEElOwQ",
    "CAACAgIAAxkBAAIedGngpLf1pwHEOSIO0cWfO-aRZxycAAI9iAAC_DFhS4xagEOuONg9OwQ"
]

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- STATİSTİKA SİSTEMİ ---
STATS_FILE = "stats.json"

def load_stats():
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r") as f: return json.load(f)
        except: pass
    return {"users": [], "total_downloads": 0}

def save_stats(stats):
    with open(STATS_FILE, "w") as f: json.dump(stats, f)

def log_user(user_id):
    stats = load_stats()
    if str(user_id) not in stats["users"]:
        stats["users"].append(str(user_id))
        save_stats(stats)

def log_download():
    stats = load_stats()
    stats["total_downloads"] += 1
    save_stats(stats)

# --- PROGRESS BAR FUNKSİYASI ---
def get_pb(current, total):
    if not total or total == 0: return "[░░░░░░░░░░] 0%"
    percent = (current / total) * 100
    filled = int(percent / 10)
    bar = '█' * filled + '░' * (10 - filled)
    return f"[{bar}] {int(percent)}%"

last_edit_time = {}

async def progress_callback(current, total, context, chat_id, message_id, prefix):
    now = time.time()
    # Hər 3 saniyədən bir editlə ki, Telegram banlamasın
    if chat_id not in last_edit_time or now - last_edit_time[chat_id] > 3:
        pb = get_pb(current, total)
        try:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=f"{prefix}\n{pb}")
            last_edit_time[chat_id] = now
        except: pass

# --- BÜTÜN DİLLƏR (Dəyişilmədi) ---
LANGUAGES = {
    'az': {'name': '🇦🇿 Azərbaycan', 'start': 'Dil seçildi!', 'shazam': '🎵 Mahnı Tap', 'dl': '📥 Video/Mahnı Yüklə', 'help': '🆘 Kömək', 'wait': 'Yüklənir... ⏳', 'find': 'Axtarılır... 🔎', 'not_found': 'Təəssüf ki, tapılmadı 😕', 'error': 'Xəta baş verdi! ❌', 'voice_req': '🎤 Mahnını tapmaq üçün səs yazısı göndərin.', 'link_req': '📥 Yükləmək üçün link və ya mahnı adı göndərin.', 'thanks': 'Kömək etdiyimə şadam! ❤️', 'ask_audio': '🎬 Video hazırdır! Mahnısını da (MP3) istəyirsən?', 'get_audio': '🎵 Bəli, MP3 yüklə', 'up': 'Telegram-a göndərilir...'},
    'tr': {'name': '🇹🇷 Türkçe', 'start': 'Dil seçildi!', 'shazam': '🎵 Şarkı Bul', 'dl': '📥 Video/Müzik İndir', 'help': '🆘 Yardım', 'wait': 'İndiriliyor... ⏳', 'find': 'Aranıyor... 🔎', 'not_found': 'Maalesef bulunamadı 😕', 'error': 'Bir hata oluştu! ❌', 'voice_req': '🎤 Şarkıyı bulmak için ses kaydı gönderin.', 'link_req': '📥 İndirmek için bağlantı veya şarkı ismi gönderin.', 'thanks': 'Yardımcı olduğuma sevindim! ❤️', 'ask_audio': '🎬 Video hazır! Müziğini de (MP3) ister misin?', 'get_audio': '🎵 Evet, MP3 indir', 'up': 'Gönderiliyor...'},
    'en': {'name': '🇺🇸 English', 'start': 'Language set!', 'shazam': '🎵 Find Song', 'dl': '📥 Download Media', 'help': '🆘 Help', 'wait': 'Downloading... ⏳', 'find': 'Searching... 🔎', 'not_found': 'Not found 😕', 'error': 'Error occurred! ❌', 'voice_req': '🎤 Send a voice note.', 'link_req': '📥 Send a link or song name.', 'thanks': 'Happy to help! ❤️', 'ask_audio': '🎬 Video is ready! Do you want the audio (MP3) too?', 'get_audio': '🎵 Yes, download MP3', 'up': 'Uploading...'},
    'ru': {'name': '🇷🇺 Русский', 'start': 'Язык выбран!', 'shazam': '🎵 Найти песню', 'dl': '📥 Скачать', 'help': '🆘 Помощь', 'wait': 'Загрузка... ⏳', 'find': 'Поиск... 🔎', 'not_found': 'Не найдено 😕', 'error': 'Ошибка! ❌', 'voice_req': '🎤 Отправьте голос.', 'link_req': '📥 Отправьте ссылку.', 'thanks': 'Рад помочь! ❤️', 'ask_audio': '🎬 Видео готово! Хотите аудио (MP3)?', 'get_audio': '🎵 Да, скачать MP3', 'up': 'Загрузка...'},
    'de': {'name': '🇩🇪 Deutsch', 'start': 'Sprache gewählt!', 'shazam': '🎵 Lied finden', 'dl': '📥 Video/Musik laden', 'help': '🆘 Hilfe', 'wait': 'Lädt... ⏳', 'find': 'Suche... 🔎', 'not_found': 'Nicht gefunden 😕', 'error': 'Fehler! ❌', 'voice_req': '🎤 Sende eine Sprachnachricht.', 'link_req': '📥 Sende einen Link.', 'thanks': 'Gerne geschehen! ❤️', 'ask_audio': '🎬 Video fertig! MP3 auch?', 'get_audio': '🎵 Ja, MP3', 'up': 'Senden...'},
    'fr': {'name': '🇫🇷 Français', 'start': 'Langue choisie!', 'shazam': '🎵 Trouver chanson', 'dl': '📥 Télécharger', 'help': '🆘 Aide', 'wait': 'Chargement... ⏳', 'find': 'Recherche... 🔎', 'not_found': 'Pas trouvé 😕', 'error': 'Erreur! ❌', 'voice_req': '🎤 Envoyez un message vocal.', 'link_req': '📥 Envoyez un lien.', 'thanks': 'Content d\'aider! ❤️', 'ask_audio': '🎬 Vidéo prête! MP3 aussi?', 'get_audio': '🎵 Oui, MP3', 'up': 'Envoi...'},
    'es': {'name': '🇪🇸 Español', 'start': '¡Idioma elegido!', 'shazam': '🎵 Buscar canción', 'dl': '📥 Descargar', 'help': '🆘 Ayuda', 'wait': 'Descargando... ⏳', 'find': 'Buscando... 🔎', 'not_found': 'No encontrado 😕', 'error': '¡Error! ❌', 'voice_req': '🎤 Envía una nota de voz.', 'link_req': '📥 Envía un enlace.', 'thanks': '¡Feliz de ayudar! ❤️', 'ask_audio': '🎬 ¡Vídeo listo! ¿MP3 también?', 'get_audio': '🎵 Sí, MP3', 'up': 'Enviando...'},
    'it': {'name': '🇮🇹 Italiano', 'start': 'Lingua scelta!', 'shazam': '🎵 Trova canzone', 'dl': '📥 Scarica', 'help': '🆘 Ayuto', 'wait': 'Caricamento... ⏳', 'find': 'Ricerca... 🔎', 'not_found': 'Non trovato 😕', 'error': 'Errore! ❌', 'voice_req': '🎤 Invia un messaggio vocale.', 'link_req': '🇮🇹 Invia un link.', 'thanks': 'Felice di aiutarti! ❤️', 'ask_audio': '🎬 Video pronto! MP3?', 'get_audio': '🎵 Sì, MP3', 'up': 'Inviando...'},
    'ar': {'name': '🇸🇦 العربية', 'start': 'تم اختيار اللغة!', 'shazam': '🎵 البحث عن أغنية', 'dl': '📥 تحميل فيديو/موسيقى', 'help': '🆘 مساعدة', 'wait': 'جاري التحميل... ⏳', 'find': 'جari البحث... 🔎', 'not_found': 'لم يتم العثور عليه 😕', 'error': 'خطأ! ❌', 'voice_req': '🎤 أرسل رسالة صوتية للبحث.', 'link_req': '📥 أرسل الرابط.', 'thanks': 'سعيد بمساعدتك! ❤️', 'ask_audio': '🎬 الفيديو جاهز! هل تريد MP3؟', 'get_audio': '🎵 نعم، تحميل', 'up': 'جاري الارسال...'},
    'ua': {'name': '🇺🇦 Українська', 'start': 'Мову обрано!', 'shazam': '🎵 Знайти пісню', 'dl': '📥 Завантажити', 'help': '🆘 Допомога', 'wait': 'Завантаження... ⏳', 'find': 'Поиск... 🔎', 'not_found': 'Не знайдено 😕', 'error': 'Помилка! ❌', 'voice_req': '🎤 Надішліть голосове повідомлення.', 'link_req': '📥 Надішліть посилання.', 'thanks': 'Радий допомогти! ❤️', 'ask_audio': '🎬 Відео готове! MP3?', 'get_audio': '🎵 Так, MP3', 'up': 'Надсилається...'}
}

user_prefs = {}

# --- FUNKSİYALAR ---
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

async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.strip()
    if not query.startswith("http"): return
    
    results = [
        InlineQueryResultArticle(
            id="1",
            title="📥 Videonu Yüklə",
            description=f"Link: {query}",
            input_message_content=InputTextMessageContent(query)
        )
    ]
    await update.inline_query.answer(results, cache_time=300)

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
        
    elif query.data == 'act_shazam': await query.message.reply_text(l['voice_req'])
    elif query.data == 'act_dl': await query.message.reply_text(l['link_req'])
    
    elif query.data == 'getmp3_now':
        original_query = context.user_data.get('last_query')
        if not original_query: return

        sticker_msg = await context.bot.send_sticker(chat_id=query.message.chat_id, sticker=random.choice(STICKER_LIST))
        status_msg = await query.message.reply_text(l['wait'])
        
        audio = await download_audio(original_query)
        if audio:
            await status_msg.edit_text(l['up'])
            with open(audio, 'rb') as f:
                await context.bot.send_audio(
                    chat_id=query.message.chat_id, 
                    audio=f, 
                    caption=f"🎵 {BOT_USERNAME}",
                    progress_callback=lambda c, t: progress_callback(c, t, context, query.message.chat_id, status_msg.message_id, l['up'])
                )
            os.remove(audio)
            log_download()
            await context.bot.delete_message(chat_id=query.message.chat_id, message_id=sticker_msg.message_id)
            await status_msg.delete()
        else:
            await status_msg.edit_text(l['error'])

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
                progress_callback=lambda c, t: progress_callback(c, t, context, update.message.chat_id, status_msg.message_id, l['up'])
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
    app.add_handler(InlineQueryHandler(inline_query_handler))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot işə düşdü...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__": main()
