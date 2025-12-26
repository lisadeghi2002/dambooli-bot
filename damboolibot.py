import asyncio
import random
import threading
import os

from telethon import TelegramClient, events
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from fastapi import FastAPI
import uvicorn

# -------- CONFIG --------
API_ID = 34384738
API_HASH = "5ec5a6a4d89e2f50f76a9ce62300e19a"
BOT_TOKEN = "7840299522:AAGM85M-jPfOdWJmfWVeVmr6VMKclnwHSKU"

CHANNEL = "dambouli_kosak"
CHANNEL_USERNAME = "@dambouli_kosak"
INDEX_FILE = "audio_ids.txt"
# ------------------------

audio_ids = set()

# ---------- TELETHON ----------
tg_client = TelegramClient("indexer", API_ID, API_HASH)

async def index_channel():
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
            f.write(f"{i}\n")

def load_ids():
    try:
        with open(INDEX_FILE) as f:
            for line in f:
                audio_ids.add(int(line.strip()))
    except FileNotFoundError:
        pass

async def telethon_runner():
    await tg_client.start()
    await index_channel()
    await tg_client.run_until_disconnected()

# ---------- BOT ----------
async def random_song(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    await update.message.reply_text(
        "سلام 👋\nبا /random یه آهنگ رندوم بگیر 🎶"
    )

def start_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("random", random_song))
    app.add_handler(CommandHandler("start", start))
    app.run_polling()

# ---------- WEB ----------
web_app = FastAPI()

@web_app.get("/")
def root():
    return {
        "status": "ok",
        "audios": len(audio_ids)
    }

# ---------- MAIN ----------
def main():
    load_ids()

    # Telethon در loop جدا
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(telethon_runner())

    threading.Thread(target=loop.run_forever, daemon=True).start()

    # Bot در thread جدا
    threading.Thread(target=start_bot, daemon=True).start()

    # Web server (برای Render)
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(web_app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
