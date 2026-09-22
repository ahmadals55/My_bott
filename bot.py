from telethon import TelegramClient, events

API_ID = 24400989
API_HASH = '8a682c7664872355902f07d127b494d9'
BOT_TOKEN = '8605129862:AAGcXah1pArBp3ibUb1gaiZCk5tU3J7OC8A'

client = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond('مرحباً بك! البوت يعمل الآن بنجاح على مدار الساعة 24/7.')

print("Bot is running...")
client.run_until_disconnected()
