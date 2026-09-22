import os
import asyncio
import logging
from flask import Flask
from threading import Thread
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# إعداد السجلات
logging.basicConfig(level=logging.INFO)

# قراءة المتغيرات من ريندر
API_ID = int(os.environ.get("API_ID", "24400989"))
API_HASH = os.environ.get("API_HASH", "8a682c7664872355902f07d127b494d9")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8605129862:AAGcXah1pArBp3ibUb1gaiZCk5tU3J7OC8A")
SESSION_STRING = os.environ.get("SESSION_STRING", "")

# إنشاء تطبيق ويب وهمي لضمان بقاء الخدمة تعمل 24/7 على ريندر
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot and Scanner are running 24/7 successfully!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# إعداد عميل تيليجرام باستخدام الجلسة النصية و توكن البوت
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    await event.respond("أهلاً بك! البوت يعمل بنجاح على مدار الساعة 🚀 24/7\nأرسل لي الآن معرف القناة أو المجموعه (مثل @username) لنقوم بفحصها.")

# استقبال أي رسالة تحتوي على معرف أو رابط قناة لفحصها
@client.on(events.NewMessage(incoming=True, func=lambda e: e.text and (e.text.startswith('@') or 't.me/' in e.text)))
async def scan_handler(event):
    target = event.text.strip()
    await event.respond(f"⏳ جاري فحص القناة أو المستخدم: `{target}` ... انتظار النتائج.")
    try:
        # محاولة جلب معلومات القناة/المستخدم كعملية فحص
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
    
    print("Starting Telegram Client...")
    # بدء تشغيل العميل (سواء كـ Bot أو UserBot حسب الجلسة)
    client.start(bot_token=BOT_TOKEN if not SESSION_STRING else None)
    client.run_until_disconnected()

if __name__ == '__main__':
    main()
    
