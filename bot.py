import discord
from discord.ext import commands
from discord import app_commands
import os
from flask import Flask
from threading import Thread

# --- نظام الاستيقاظ ---
app = Flask('')
@app.route('/')
def home(): return "Pro Club Bot Online"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# --- إعدادات البوت ---
TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
SUGGESTIONS_CHANNEL_ID = 1511935406739034273  # روم الاقتراحات
ADMIN_CHANNEL_ID = 1512689809150312468       # روم الإدارة

# --- قاموس الرتب (تأكد أن أسماء الرتب في ديسكورد مطابقة تماماً للمكتوب هنا) ---
ROLES_MAP = {
    "هجوم": "هجوم",
    "وسط": "وسط",
    "دفاع": "دفاع",
    "حارس": "حارس"
}

class ClubApplyModal(discord.ui.Modal, title='استمارة الانضمام للنادي'):
    ign = discord.ui.TextInput(label='الأيدي (PSN / EA ID)', placeholder='اكتب الأيدي هنا...', required=True)
    position = discord.ui.TextInput(label='مركزك (هجوم، وسط، دفاع، حارس)', placeholder='اكتب مركزك هنا من الخيارات المذكورة...', required=True)
    overall = discord.ui.TextInput(label='الأوفر (Overall)', placeholder='مثال: 89', required=True)
    experience = discord.ui.TextInput(label='الخبرة (اختياري)', style=discord.TextStyle.paragraph, placeholder='أنديتك السابقة...', required=False)

    async def on_submit(self, interaction: discord.Interaction):
        admin_channel = interaction.guild.get_channel(ADMIN_CHANNEL_ID)
        pos_input = self.position.value.strip() # قراءة المركز المكتوب
        
        role_status = "لم يتم تحديد رتبة تلقائية"
        if pos_input in ROLES_MAP:
            role_name = ROLES_MAP[pos_input]
            role = discord.utils.get(interaction.guild.roles, name=role_name)
            if role:
                try:
                    await interaction.user.add_roles(role)
                    role_status = f"✅ تم منحك رتبة **{role_name}** تلقائياً"
                except:
                    role_status = "⚠️ مشكلة في الصلاحيات (رتبة البوت نازلة)"

        embed = discord.Embed(title="⚽ طلب انضمام جديد", color=discord.Color.blue())
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.add_field(name="اللاعب", value=interaction.user.mention, inline=True)
        embed.add_field(name="الأيدي", value=self.ign.value, inline=True)
        embed.add_field(name="المركز المختار", value=pos_input, inline=True)
        embed.add_field(name="الأوفر", value=self.overall.value, inline=True)
        embed.set_footer(text=f"الحالة: {role_status}")

        await admin_channel.send(embed=embed)
        await interaction.response.send_message(f"شكراً {interaction.user.mention}! تم إرسال طلبك. {role_status}", ephemeral=True)

class ClubApplyView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="تقديم طلب انضمام", style=discord.ButtonStyle.primary, custom_id="apply_club_btn")
    async def apply_button(self, interaction, button):
        await interaction.response.send_modal(ClubApplyModal())

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)
    async def setup_hook(self): self.add_view(ClubApplyView())
    async def on_ready(self):
        print(f'Logged in as {self.user}')
        await self.tree.sync()

bot = MyBot()

@bot.event
async def on_message(message):
    if message.author == bot.user: return
    if message.channel.id == SUGGESTIONS_CHANNEL_ID:
        admin_channel = bot.get_channel(ADMIN_CHANNEL_ID)
        embed = discord.Embed(title="💡 اقتراح جديد", description=message.content, color=discord.Color.gold())
        await admin_channel.send(embed=embed)
        await message.delete()

@bot.tree.command(name="setup_club", description="إرسال لوحة التقديم")
@app_commands.checks.has_permissions(administrator=True)
async def setup_club(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📝 التقديم على نادي البرو كلوب",
        description=(
            "اضغط على الزر أدناه لتعبئة بيانات الانضمام.\n\n"
            "⚠️ **نظام الرتب التلقائي:**\n"
            "بمجرد كتابة مركزك بشكل صحيح (هجوم، وسط، دفاع، حارس) "
            "سيقوم البوت بإعطائك الرتبة المناسبة مباشرة!"
        ),
        color=discord.Color.blue()
    )
    await interaction.channel.send(embed=embed, view=ClubApplyView())
    await interaction.response.send_message("تم إرسال اللوحة بنجاح!", ephemeral=True)

keep_alive()
bot.run(TOKEN)
