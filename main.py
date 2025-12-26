import random
import asyncio
import os
from telethon import TelegramClient, events
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler
)
from aiohttp import web

# -------- CONFIG --------
API_ID = int(os.environ.get("API_ID", 34384738))
API_HASH = os.environ.get("API_HASH", "5ec5a6a4d89e2f50f76a9ce62300e19a")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7840299522:AAGM85M-jPfOdWJmfWVeVmr6VMKclnwHSKU")

CHANNEL = "dambouli_kosak"        # بدون @
CHANNEL_USERNAME = "@dambouli_kosak"

INDEX_FILE = "audio_ids.txt"
# ------------------------

audio_ids = set()

# ---------- TELETHON PART ----------
tg_client = TelegramClient("indexer", API_ID, API_HASH)

async def index_channel():
    print("Indexing channel history...")
    async for msg in tg_client.iter_messages(CHANNEL):
        if msg.audio:
            audio_ids.add(msg.id)
    save_ids()
    print(f"Indexed {len(audio_ids)} audios")

@tg_client.on(events.NewMessage(chats=CHANNEL))
async def new_audio_handler(event):
    if event.message.audio:
        audio_ids.add(event.message.id)
        save_ids()
        print("New audio added")

def save_ids():
    with open(INDEX_FILE, "w") as f:
        for i in audio_ids:
            f.write(str(i) + "\n")

def load_ids():
    try:
        with open(INDEX_FILE) as f:
            for line in f:
                audio_ids.add(int(line.strip()))
    except FileNotFoundError:
        pass

# ---------- BOT PART ----------
async def random_song(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("one person requested a song")
    if not audio_ids:
        await update.message.reply_text("هنوز آهنگی پیدا نشد 🎵")
        return

    msg_id = random.choice(list(audio_ids))

    await context.bot.forward_message(
        chat_id=update.effective_chat.id,
        from_chat_id=CHANNEL_USERNAME,
        message_id=msg_id
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("one person started the bot")
    welcome_text = """
سلام سلام! 👋
به دنیای دامبولی و کصکلک خوش اومدی 🎶
من از این به بعد همکار هوشمند علی هستم 😎

اگه دلت یه آهنگ رندوم از کانال فوق‌العاده‌ی 
دامبولی کصک می‌خواد، فقط کافیه بزنی:
/random

هرموقع حس کردی غم داری کافیه این دکمه رو بزنی تا قر رو بیارم به خونه‌ت! 😏
راستی، تا ابد میتونم برات آهنگ بفرستم پس من رو دور ننداز 💿✨
اگه با چنل فوق‌العاده‌ی دامبولی کصک آشنایی نداره هم میتونی با لینک زیر جوین بدی:
@dambouli_kosak
"""
    await update.message.reply_text(welcome_text)

# ---------- HEALTH SERVER ----------
async def health_server():
    async def handle(request):
        return web.Response(text="OK")

    app = web.Application()
    app.router.add_get("/", handle)

    port = int(os.environ.get("PORT", 8000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Health server running on port {port}")

# ---------- TELETHON RUNNER ----------
async def telethon_runner():
    await tg_client.start()
    await index_channel()
    await tg_client.run_until_disconnected()

# ---------- MAIN ----------
def main():
    load_ids()
    loop = asyncio.get_event_loop()

    # Telethon
    loop.create_task(telethon_runner())

    # Health server
    loop.create_task(health_server())

    # Telegram Bot
    bot_app = ApplicationBuilder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("random", random_song))
    bot_app.add_handler(CommandHandler("start", start))

    print("Bot is running...")
    bot_app.run_polling()

if __name__ == "__main__":
    main()
