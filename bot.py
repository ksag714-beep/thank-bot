import discord
import os
from flask import Flask
from threading import Thread

# --- نظام الاستيقاظ ---
app = Flask('')
@app.route('/')
def home(): return "Online"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# --- إعدادات البوت ---
TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
CHANNEL_ID = 1511935406739034273

intents = discord.Intents.default()
intents.message_content = True 
client = discord.Client(intents=intents)

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.channel.id == CHANNEL_ID:
        # رسالتك الأصلية
        response = f"بندرس اقتراحك.. شكراً لك يا {message.author.mention} على تفاعلك معنا ❤️ بنحاول نرد عليك بأسرع وقت 🙏⌛"
        await message.reply(response)

# التشغيل
if __name__ == "__main__":
    keep_alive()
    if TOKEN:
        client.run(TOKEN)
