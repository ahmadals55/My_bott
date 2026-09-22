import sys
import subprocess
import asyncio
import os
import time
from flask import Flask
import threading

def auto_install(package_name):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])

try:
    from telethon import TelegramClient, events, Button
    from telethon.tl.functions.channels import GetParticipantsRequest
    from telethon.tl.types import ChannelParticipantsAdmins, ChannelParticipantsRecent
except ImportError:
    auto_install("telethon")
    from telethon import TelegramClient, events, Button
    from telethon.tl.functions.channels import GetParticipantsRequest
    from telethon.tl.types import ChannelParticipantsAdmins, ChannelParticipantsRecent

# 1. إعداد خادم الويب الوهمي ليبقى البوت شغالاً 24/7 على Render
app = Flask('')

@app.route('/')
def home():
    return "Bot and Scanner are running 24/7!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# تشغيل الويب في خلفية الكود
t = threading.Thread(target=run_web)
t.start()

# 2. بيانات Telegram
API_ID = 24400989
API_HASH = '8a682c7664872355902f07d127b494d9'
BOT_TOKEN = '8605129862:AAGcXah1pArBp3ibUb1gaiZCk5tU3J7OC8A'

user_attempts = {}
MAX_ATTEMPTS = 5
COOLDOWN_HOURS = 12
COOLDOWN_SECONDS = COOLDOWN_HOURS * 3600

user_target_channel = {}

user_client = TelegramClient('user_session', API_ID, API_HASH)
bot_client = TelegramClient('bot_session', API_ID, API_HASH)

PORN_KEYWORDS = ["سكس", "إباحي", "جنسي", "فيديو ساخن", "بنات سكس", "مقاطع اباحية", "صور عري", "شواذ", "نيك"]
VIOLENCE_KEYWORDS = ["اغتصاب", "اعتداء جنسي", "قتل متعمد", "ذبح بشري", "عنف دموي", "انتحار جماعي", "تهديد بالقتل"]
ABUSE_KEYWORDS = ["سب وشتم قذر", "شتم سافر", "ألفاظ نابية", "قحب", "عرص", "منيوك"]
SPAM_DOMAINS = [".xyz", ".top", ".club", ".online", ".site", "t.me/joinchat", "bit.ly", "exe.io", "t.me/+"]
SPAM_PHRASES = ["اشترك الآن لربح", "مسابقة ربح المال", "تمويل قناتك براتب", "زيادة أعضاء مضمونة"]

def analyze_message_content(text):
    text_lower = text.lower()
    for word in PORN_KEYWORDS:
        if word in text_lower:
            return "🔥 مخالف [محتوى إباحي صريح]"
    for word in VIOLENCE_KEYWORDS:
        if word in text_lower:
            return "⚠️ مخالف [عنف شديد أو اغتصاب]"
    for word in ABUSE_KEYWORDS:
        if word in text_lower:
            return "🛑 مخالف [إساءة وسب سافر]"
    for domain in SPAM_DOMAINS:
        if domain in text_lower:
            return "🔗 مخالف [رابط مشبوه أو دعوة مغلقة]"
    for phrase in SPAM_PHRASES:
        if phrase in text_lower:
            return "📢 مخالف [إعلان ترويجي / سبام]"
    return "سليم"

async def get_all_channel_admins_and_owner(channel_entity):
    admins_list = []
    owner_info = "👑 **المالك الأساسي:** مخفي أو محمي بواسطة إعدادات القناة"
    
    try:
        participants = await user_client(GetParticipantsRequest(
            channel=channel_entity,
            filter=ChannelParticipantsAdmins(),
            offset=0,
            limit=100,
            hash=0
        ))
        for user in participants.users:
            name = f"{user.first_name or ''} {user.last_name or ''}".strip()
            username = f"@{user.username}" if user.username else "بدون معرف"
            user_id = user.id
            role = "مشرف عادي"
            is_the_owner = False
            for p in participants.participants:
                if p.user_id == user_id:
                    if hasattr(p, 'rank') and p.rank:
                        role = f"مشرف (رتبة: {p.rank})"
                    if hasattr(p, 'is_creator') and p.is_creator:
                        role = "👑 [المالك الأساسي]"
                        is_the_owner = True
                    break
            formatted_admin = f"• الاسم: {name}\n  - المعرف: {username}\n  - الآيدي: `{user_id}`\n  - الصفة: {role}"
            if is_the_owner:
                owner_info = f"👑 **المالك الأساسي:**\n  - الاسم: {name}\n  - المعرف: {username}\n  - الآيدي: `{user_id}`"
            else:
                admins_list.append(formatted_admin)
        if admins_list:
            return owner_info, admins_list
    except Exception:
        pass

    try:
        async for message in user_client.iter_messages(channel_entity, limit=50):
            if message.sender_id:
                try:
                    sender = await user_client.get_entity(message.sender_id)
                    s_name = f"{sender.first_name or ''} {sender.last_name or ''}".strip()
                    s_username = f"@{sender.username}" if sender.username else "بدون معرف"
                    info_str = f"• الاسم: {s_name}\n  - المعرف: {s_username}\n  - الآيدي: `{sender.id}`\n  - الصفة: يرجرج/ينشر في القناة (مشرف محتمل)"
                    if info_str not in admins_list:
                        admins_list.append(info_str)
                except Exception:
                    pass
            if len(admins_list) >= 5:
                break
        if admins_list:
            owner_info = "👑 **المالك / الناشر الرئيسي:** تم استخراجه عبر تحليل بصمة المنشورات"
    except Exception as e:
        admins_list.append(f"⚠️ تعذر الاستخراج الكامل: القناة تفرض حماية إدارية تامة.")

    return owner_info, admins_list

@bot_client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    my_keyboard = [
        [Button.text("كشف", resize=True), Button.text("مخالفات", resize=True)]
    ]
    await event.respond(
        "👋 **أهلاً بك في بوت فحص القنوات وإدارة الحماية الخارق!**\n\n"
        "👨‍💻 **مطور البوت / المالك:** @italsory\n\n"
        "📌 **طريقة الاستخدام:**\n"
        "1️⃣ أرسل معرف القناة أولاً (مثال: `@telegram`)\n"
        "2️⃣ اضغط على زر **كشف** أو **مخالفات** من لوحة المفاتيح الثابتة بالأسفل.\n"
        "• مسموح بـ **5 محاولات لكل 12 ساعة**.",
        buttons=my_keyboard
    )

@bot_client.on(events.NewMessage)
async def handle_incoming_messages(event):
    text = event.text.strip() if event.text else ""
    
    if not text:
        return

    if text.startswith('/start'):
        return

    user_id = event.sender_id

    if text == "كشف":
        if user_id not in user_target_channel:
            await event.respond("⚠️ يرجى إرسال معرف القناة أولاً (مثل `@telegram`) ثم اضغط على زر **كشف**.")
            return
        await execute_scan_admins(event, user_id)
        return

    if text == "مخالفات":
        if user_id not in user_target_channel:
            await event.respond("⚠️ يرجى إرسال معرف القناة أولاً (مثل `@telegram`) ثم اضغط على زر **مخالفات**.")
            return
        await execute_scan_violations(event, user_id)
        return

    if text.startswith('@'):
        current_time = time.time()
        if user_id in user_attempts:
            data = user_attempts[user_id]
            if current_time < data['reset_time']:
                if data['count'] >= MAX_ATTEMPTS:
                    remaining_hours = int((data['reset_time'] - current_time) / 3600)
                    remaining_minutes = int(((data['reset_time'] - current_time) % 3600) / 60)
                    await event.respond(
                        f"⚠️ **عذراً، لقد استنفدت محاولات الفحص الـ 5 الخاصة بك.**\n"
                        f"⏳ يرجى الانتظار لمدة `{remaining_hours} ساعة و {remaining_minutes} دقيقة`."
                    )
                    return
            else:
                user_attempts[user_id] = {'count': 0, 'reset_time': current_time + COOLDOWN_SECONDS}
        else:
            user_attempts[user_id] = {'count': 0, 'reset_time': current_time + COOLDOWN_SECONDS}

        user_target_channel[user_id] = text
        
        my_keyboard = [
            [Button.text("كشف", resize=True), Button.text("مخالفات", resize=True)]
        ]
        
        await event.respond(
            f"🎯 **تم حفظ القناة بنجاح:** `{text}`\n"
            f"الآن اضغط على زر **كشف** أو **مخالفات** بالأسفل لتنفيذ الفحص مباشرة!",
            buttons=my_keyboard
        )

async def execute_scan_admins(event, user_id):
    channel_username = user_target_channel[user_id]
    user_attempts[user_id]['count'] += 1
    remaining_tries = MAX_ATTEMPTS - user_attempts[user_id]['count']

    await event.respond(f"⏳ **جاري الفحص الخارق وتحليل بصمة الإدارة للقناة `{channel_username}`...**")

    try:
        channel_entity = await user_client.get_entity(channel_username)
        owner_info, admins = await get_all_channel_admins_and_owner(channel_entity)
        admins_text = "\n\n".join(admins) if admins else "لا توجد تفاصيل متاحة بسبب حماية القناة المشددة."

        report = (
            f"👑 **تقرير الكشف الذكي للقناة `{channel_username}`:**\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"{owner_info}\n\n"
            f"👥 **النتائج المستخرجة:**\n"
            f"{admins_text}\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"📌 المحاولات المتبقية لك: `{remaining_tries}` من {MAX_ATTEMPTS}"
        )
        await event.respond(report, link_preview=False)
    except Exception as e:
        await event.respond(f"❌ عذراً، هذه القناة تحمي هويات المشرفين بشكل كامل ضد أي فحص خارجي.")

async def execute_scan_violations(event, user_id):
    channel_username = user_target_channel[user_id]
    clean_username = channel_username.replace('@', '').strip()

    user_attempts[user_id]['count'] += 1
    remaining_tries = MAX_ATTEMPTS - user_attempts[user_id]['count']

    await event.respond(f"⚡ **جاري الفحص العميق لأحدث 300 منشور في `{channel_username}` بحثاً عن المخالفات...**")

    try:
        channel_entity = await user_client.get_entity(channel_username)
        violations = []
        total_scanned = 0

        async for message in user_client.iter_messages(channel_entity, limit=300):
            total_scanned += 1
            msg_text = getattr(message, 'text', '') or getattr(message, 'message', '') or ''
            
            if msg_text:
                verdict = analyze_message_content(msg_text)
                if "مخالف" in verdict:
                    msg_link = f"https://t.me/{clean_username}/{message.id}"
                    violations.append({
                        'id': message.id,
                        'link': msg_link,
                        'verdict': verdict,
                        'text': msg_text[:70]
                    })

        if not violations:
            report = (
                f"✅ **تقرير المخالفات للقناة `{channel_username}`:**\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"📊 إجمالي ما تم فحصه: `{total_scanned}` منشوراً.\n"
                f"🟢 الحالة: القناة نظيفة وخالية من المخالفات.\n"
                f"📌 المحاولات المتبقية: `{remaining_tries}` من {MAX_ATTEMPTS}"
            )
        else:
            report = (
                f"🚨 **تقرير المخالفات الصارمة للقناة `{channel_username}`:**\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"📊 إجمالي الفحص: `{total_scanned}` منشوراً.\n"
                f"⚠️ عدد المخالفات المكتشفة: `{len(violations)}`\n"
                f"📌 المحاولات المتبقية: `{remaining_tries}` من {MAX_ATTEMPTS}\n\n"
                f"🔻 **الروابط المخالفة:**\n"
            )
            for v in violations[:10]:
                report += (
                    f"🔹 **منشور #{v['id']}**\n"
                    f"  📌 التصنيف: {v['verdict']}\n"
                    f"  🔗 [رابط الرسالة]({v['link']})\n"
                    f"  📝 النص: _\"{v['text']}...\"_\n"
                    f"───────────────────\n"
                )

        await event.respond(report, link_preview=False)
    except Exception as e:
        await event.respond(f"❌ حدث خطأ أثناء فحص المخالفات:\n{str(e)}")

async def main():
    await user_client.start()
    await bot_client.start(bot_token=BOT_TOKEN)
    print("🔥 تم تطبيق الكود الخارق مع دعم الاستضافة الدائمة 24/7 بنجاح!")
    
    await asyncio.gather(
        user_client.run_until_disconnected(),
        bot_client.run_until_disconnected()
    )

if __name__ == "__main__":
    asyncio.run(main())
    
