from telethon import TelegramClient, events
from flask import Flask
import threading
os = __import__('os')

API_ID = 24400989
API_HASH = '8a682c7664872355902f07d127b494d9'
BOT_TOKEN = '8605129862:AAGcXah1pArBp3ibUb1gaiZCk5tU3J7OC8A'

# إعداد خادم الويب الوهمي ليبقى البوت شغالاً على Render
app = Flask('')

@app.route('/')
def home():
    return "Bot is running 24/7!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# تشغيل الويب في خلفية الكود
t = threading.Thread(target=run_web)
t.start()

# تشغيل بوت تيليجرام
client = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond('أهلاً بك! البوت يعمل بنجاح على مدار الساعة 24/7 🚀')

print("Bot is running...")
client.run_until_disconnected()
