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
        'voice_req': '🎤 Mahnını tapmaq üçün səs yazısı göndərin.', 'link_req': '📥 Yükləmək üçün link və ya mahnı adı göndərin.', 'thanks': 'Kömək etdiyimə şadam! ❤️'
    },
    'tr': {
        'name': '🇹🇷 Türkçe', 'start': 'Dil seçildi!', 'shazam': '🎵 Şarkı Bul', 'dl': '📥 Video/Müzik İndir', 'help': '🆘 Yardım',
        'wait': 'İndiriliyor... ⏳', 'find': 'Aranıyor... 🔎', 'not_found': 'Maalesef bulunamadı 😕', 'error': 'Bir hata oluştu! ❌',
        'voice_req': '🎤 Şarkıyı bulmak için ses kaydı gönderin.', 'link_req': '📥 İndirmek için bağlantı veya şarkı ismi gönderin.', 'thanks': 'Yardımcı olduğuma sevindim! ❤️'
    },
    'en': {
        'name': '🇺🇸 English', 'start': 'Language set!', 'shazam': '🎵 Find Song', 'dl': '📥 Download Media', 'help': '🆘 Help',
        'wait': 'Downloading... ⏳', 'find': 'Searching... 🔎', 'not_found': 'Not found 😕', 'error': 'Error occurred! ❌',
        'voice_req': '🎤 Send a voice note.', 'link_req': '📥 Send a link or song name.', 'thanks': 'Happy to help! ❤️'
    },
    'ru': { 'name': '🇷🇺 Русский', 'start': 'Язык выбран!', 'shazam': '🎵 Найти песню', 'dl': '📥 Скачать', 'help': '🆘 Помощь', 'wait': 'Загрузка... ⏳', 'find': 'Поиск... 🔎', 'not_found': 'Не найдено 😕', 'error': 'Ошибка! ❌', 'voice_req': '🎤 Отправьте голос.', 'link_req': '📥 Отправьте ссылку.', 'thanks': 'Рад помочь! ❤️' },
    'de': { 'name': '🇩🇪 Deutsch', 'start': 'Sprache gewählt!', 'shazam': '🎵 Lied finden', 'dl': '📥 Video/Musik laden', 'help': '🆘 Hilfe', 'wait': 'Lädt... ⏳', 'find': 'Suche... 🔎', 'not_found': 'Nicht gefunden 😕', 'error': 'Fehler! ❌', 'voice_req': '🎤 Sende eine Sprachnachricht.', 'link_req': '📥 Sende einen Link.', 'thanks': 'Gerne geschehen! ❤️' },
    'fr': { 'name': '🇫🇷 Français', 'start': 'Langue choisie!', 'shazam': '🎵 Trouver chanson', 'dl': '📥 Télécharger', 'help': '🆘 Aide', 'wait': 'Chargement... ⏳', 'find': 'Recherche... 🔎', 'not_found': 'Pas trouvé 😕', 'error': 'Erreur! ❌', 'voice_req': '🎤 Envoyez un message vocal.', 'link_req': '📥 Envoyez un lien.', 'thanks': 'Content d\'aider! ❤️' },
    'es': { 'name': '🇪🇸 Español', 'start': '¡Idioma elegido!', 'shazam': '🎵 Buscar canción', 'dl': '📥 Descargar', 'help': '🆘 Ayuda', 'wait': 'Descargando... ⏳', 'find': 'Buscando... 🔎', 'not_found': 'No encontrado 😕', 'error': '¡Error! ❌', 'voice_req': '🎤 Envía una nota de voz.', 'link_req': '📥 Envía un enlace.', 'thanks': '¡Feliz de ayudar! ❤️' },
    'it': { 'name': '🇮🇹 Italiano', 'start': 'Lingua scelta!', 'shazam': '🎵 Trova canzone', 'dl': '📥 Scarica', 'help': '🆘 Ayuto', 'wait': 'Caricamento... ⏳', 'find': 'Ricerca... 🔎', 'not_found': 'Non trovato 😕', 'error': 'Errore! ❌', 'voice_req': '🎤 Invia un messaggio vocale.', 'link_req': '🇮🇹 Invia un link.', 'thanks': 'Felice di aiutarti! ❤️' },
    'ar': { 'name': '🇸🇦 العربية', 'start': 'تم اختيار اللغة!', 'shazam': '🎵 البحث عن أغنية', 'dl': '📥 تحميل فيديو/موسيقى', 'help': '🆘 مساعدة', 'wait': 'جاري التحميل... ⏳', 'find': 'جari البحث... 🔎', 'not_found': 'لم يتم العثور عليه 😕', 'error': 'خطأ! ❌', 'voice_req': '🎤 أرسل رسالة صوتية للبحث.', 'link_req': '📥 أرسل الرابط.', 'thanks': 'سعيد بمساعدتك! ❤️' },
    'ua': { 'name': '🇺🇦 Українська', 'start': 'Мову обрано!', 'shazam': '🎵 Знайти пісню', 'dl': '📥 Завантажити', 'help': '🆘 Допомога', 'wait': 'Завантаження... ⏳', 'find': 'Поиск... 🔎', 'not_found': 'Не знайдено 😕', 'error': 'Помилка! ❌', 'voice_req': '🎤 Надішліть голосове повідомлення.', 'link_req': '📥 Надішліть посилання.', 'thanks': 'Радий допомогти! ❤️' }
}

user_prefs = {}

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

# --- PROSESLƏR ---
async def download_media(query):
    if not query.startswith("http"):
        query = f"ytsearch1:{query}"

    v_file, a_file = "video.mp4", "audio.mp3"
    for f in [v_file, a_file]:
        if os.path.exists(f): 
            try: os.remove(f)
            except: pass

    common_opts = {
        'quiet': True,
        'noplaylist': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'referer': 'https://www.google.com/',
        'nocheckcertificate': True,
    }

    opts_v = {
        **common_opts,
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': 'video.%(ext)s',
    }
    
    opts_a = {
        **common_opts,
        'format': 'bestaudio/best',
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
        'outtmpl': 'audio',
    }

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(opts_v).download([query]))
        await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(opts_a).download([query]))
        return v_file, a_file
    except Exception as e:
        logging.error(f"Download error: {e}")
        return None, None

async def find_song_audd(file_path, lang_code):
    l = LANGUAGES.get(lang_code, LANGUAGES['az'])
    try:
        with open(file_path, 'rb') as f:
            res = requests.post('https://api.audd.io/', data={'api_token': AUDD_API_KEY}, files={'file': f}).json()
        if res.get('status') == 'success' and res.get('result'):
            r = res['result']
            return f"🎧 {r['title']} - {r['artist']}"
        return l['not_found']
    except: return l['error']

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please choose a language / Dil seçin:", reply_markup=get_lang_keyboard())

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    if query.data.startswith('l_'):
        lang = query.data.split('_')[1]
        user_prefs[user_id] = lang
        l = LANGUAGES[lang]
        await query.edit_message_text(text=l['start'], reply_markup=get_main_buttons(lang))
    elif query.data == 'act_shazam':
        lang = user_prefs.get(user_id, 'az')
        await query.message.reply_text(LANGUAGES[lang]['voice_req'])
    elif query.data == 'act_dl':
        lang = user_prefs.get(user_id, 'az')
        await query.message.reply_text(LANGUAGES[lang]['link_req'])

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    lang = user_prefs.get(user_id, 'az')
    l = LANGUAGES[lang]
    text = update.message.text

    try: await update.message.set_reaction(reaction="👀")
    except: pass
    
    await context.bot.send_chat_action(chat_id=update.message.chat_id, action="upload_video")

    v, a = await download_media(text)

    if v and os.path.exists(v):
        caption_text = f"{l['thanks']}\n\n🤖 Bot: {BOT_USERNAME}"
        await context.bot.send_chat_action(chat_id=update.message.chat_id, action="upload_video")
        with open(v, 'rb') as vf:
            await context.bot.send_video(
                chat_id=update.message.chat_id, 
                video=vf, 
                caption=caption_text, 
                reply_markup=get_main_buttons(lang)
            )
        
        if os.path.exists(a):
            await context.bot.send_chat_action(chat_id=update.message.chat_id, action="upload_document")
            with open(a, 'rb') as af:
                await context.bot.send_audio(chat_id=update.message.chat_id, audio=af, caption=caption_text)

        if os.path.exists(v): os.remove(v)
        if os.path.exists(a): os.remove(a)
        
        try: await update.message.set_reaction(reaction="✅")
        except: pass
    else:
        try: await update.message.set_reaction(reaction=[])
        except: pass
        await update.message.reply_text(l['error'])

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    lang = user_prefs.get(user_id, 'az')
    l = LANGUAGES[lang]
    msg = await update.message.reply_text(l['find'])
    file = await (update.message.voice or update.message.audio).get_file()
    path = f"s_{user_id}.ogg"
    await file.download_to_drive(path)
    res = await find_song_audd(path, lang)
    await msg.edit_text(res, reply_markup=get_main_buttons(lang))
    if os.path.exists(path): os.remove(path)

# --- İŞƏ SALMA ---
def main():
    keep_alive() 
    
    # Builder-də tənzimləmələr
    app = (
        Application.builder()
        .token(TOKEN)
        .connect_timeout(40)
        .read_timeout(40)
        .write_timeout(40)
        .build()
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))

    print("Bot stabil rejimdə aktivdir...")
    
    # run_polling içində artıq arqument yoxdur
    app.run_polling(
        drop_pending_updates=True, 
        timeout=30, 
        bootstrap_retries=10 
    )

if __name__ == "__main__":
    main()
