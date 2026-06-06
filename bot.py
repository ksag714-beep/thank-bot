import discord
from discord.ext import commands
from discord import app_commands
import os
from flask import Flask
from threading import Thread

# --- نظام الاستيقاظ ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Online"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# --- إعدادات البوت ---
TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
SUGGESTIONS_CHANNEL_ID = 1511935406739034273  # آيدي روم الاقتراحات اللي يرسل فيها الناس
ADMIN_CHANNEL_ID =  1512689809150312468      # آيدي روم الإدارة (للاقتراحات والتقديمات)

# --- نظام التقديم (Modal) ---
class ApplyModal(discord.ui.Modal, title='استمارة تقديم الجمارك'):
    name = discord.ui.TextInput(label='الاسم الثلاثي', placeholder='اكتب اسمك هنا...')
    age = discord.ui.TextInput(label='العمر', placeholder='مثال: 20')
    department = discord.ui.TextInput(label='القسم المطلوب', placeholder='تفتيش، دوريات...')
    experience = discord.ui.TextInput(label='الخبرات السابقة', style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        admin_channel = interaction.guild.get_channel(ADMIN_CHANNEL_ID)
        embed = discord.Embed(title="تقديم جديد: جمارك", color=discord.Color.green())
        embed.add_field(name="المتقدم", value=interaction.user.mention)
        embed.add_field(name="الاسم", value=self.name.value)
        embed.add_field(name="العمر", value=self.age.value)
        embed.add_field(name="القسم", value=self.department.value)
        embed.add_field(name="الخبرة", value=self.experience.value, inline=False)
        
        await admin_channel.send(embed=embed)
        await interaction.response.send_message("تم إرسال تقديمك بنجاح للإدارة!", ephemeral=True)

class ApplyView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="التقديم على الجمارك", style=discord.ButtonStyle.success, custom_id="apply_btn")
    async def apply_btn(self, interaction, button):
        await interaction.response.send_modal(ApplyModal())

# --- إعداد البوت الرئيسي ---
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.add_view(ApplyView()) # يخلي الزر شغال حتى لو طفى البوت واشتغل

    async def on_ready(self):
        print(f'Logged in as {self.user}')
        await self.tree.sync()

bot = MyBot()

# --- جزء الاقتراحات (القديم) ---
@bot.event
async def on_message(message):
    if message.author == bot.user: return
    if message.channel.id == SUGGESTIONS_CHANNEL_ID:
        admin_channel = bot.get_channel(ADMIN_CHANNEL_ID)
        embed = discord.Embed(title="اقتراح جديد", description=message.content, color=discord.Color.blue())
        embed.set_footer(text=f"بواسطة: {message.author}")
        await admin_channel.send(embed=embed)
        await message.delete()
        await message.channel.send(f"شكراً {message.author.mention}، تم استلام اقتراحك!", delete_after=5)

# --- أمر إنشاء لوحة التقديم ---
@bot.tree.command(name="setup_apply", description="إرسال لوحة التقديم للجمارك")
@app_commands.checks.has_permissions(administrator=True)
async def setup_apply(interaction: discord.Interaction):
    embed = discord.Embed(title="قسم التقديم على الجمارك", description="اضغط الزر لتعبئة البيانات", color=discord.Color.gold())
    await interaction.channel.send(embed=embed, view=ApplyView())
    await interaction.response.send_message("تم التفعيل", ephemeral=True)

keep_alive()
bot.run(TOKEN)
