import os
import logging
from flask import Flask
from threading import Thread
from telethon import TelegramClient, events

# إعداد السجلات
logging.basicConfig(level=logging.INFO)

# قراءة المتغيرات من ريندر (استخدام توكن البوت فقط)
API_ID = int(os.environ.get("API_ID", "24400989"))
API_HASH = os.environ.get("API_HASH", "8a682c7664872355902f07d127b494d9")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8605129862:AAGcXah1pArBp3ibUb1gaiZCk5tU3J7OC8A")

# إنشاء تطبيق ويب وهمي لضمان بقاء الخدمة تعمل 24/7 على ريندر
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running 24/7 successfully!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# إنشاء عميل تيليجرام باستخدام توكن البوت حصرياً (بدون جلسة معقدة)
client = TelegramClient('bot_session', API_ID, API_HASH)

@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    await event.respond("أهلاً بك! البوت يعمل بنجاح تام 🚀 24/7\nأرسل لي الآن معرف القناة أو المجموعه (مثل @username) لنقوم بفحصها.")

# استقبال أي رسالة تحتوي على معرف أو رابط قناة لفحصها
@client.on(events.NewMessage(incoming=True, func=lambda e: e.text and (e.text.startswith('@') or 't.me/' in e.text)))
async def scan_handler(event):
    target = event.text.strip()
    await event.respond(f"⏳ جاري فحص الكيان: `{target}` ... يرجى الانتظار.")
    try:
        # جلب معلومات القناة/المستخدم العامة
        entity = await client.get_entity(target)
        result_text = (
            f"✅ **تم العثور على الكيان بنجاح!**\n\n"
            f"📌 **الاسم:** {getattr(entity, 'title', getattr(entity, 'first_name', 'غير متوفر'))}\n"
            f"🆔 **المعرف/الإيدي:** `{entity.id}`\n"
            f"🔗 **المعرف:** @{getattr(entity, 'username', 'لا يوجد')}"
        )
        await event.respond(result_text)
    except Exception as e:
        await event.respond(f"❌ حدث خطأ أثناء الفحص أو لم يتم العثور على الهدف:\n`{str(e)}`")

def main():
    # تشغيل سيرفر الويب في خلفية مستقلة
    server_thread = Thread(target=run_web)
    server_thread.daemon = True
    server_thread.start()
    
    print("Starting Telegram Bot...")
    # بدء تشغيل البوت باستخدام التوكن مباشرة
    client.start(bot_token=BOT_TOKEN)
    client.run_until_disconnected()

if __name__ == '__main__':
    main()
    
