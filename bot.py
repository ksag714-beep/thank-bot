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
ADMIN_CHANNEL_ID = 1512689809150312468       # روم الإدارة والعقود

# --- قاموس الرتب (تأكد من مطابقة الأسماء في ديسكورد) ---
ROLES_MAP = {
    "هجوم": "هجوم",
    "وسط": "وسط",
    "دفاع": "دفاع",
    "حارس": "حارس"
}

class PlayerContractModal(discord.ui.Modal, title='تسجيل عقد لاعب جديد'):
    ign = discord.ui.TextInput(label='الأيدي (PSN / EA ID)', placeholder='اكتب الأيدي هنا...', required=True)
    position = discord.ui.TextInput(label='المركز الأساسي (هجوم، وسط، دفاع، حارس)', placeholder='اكتب مركزك هنا...', required=True)
    overall = discord.ui.TextInput(label='الأوفر (Overall)', placeholder='مثال: 90', required=True)
    contract_terms = discord.ui.TextInput(label='تفاصيل أو خبرات سابقة', style=discord.TextStyle.paragraph, placeholder='اذكر أنديتك السابقة أو ملاحظاتك...', required=False)

    async def on_submit(self, interaction: discord.Interaction):
        admin_channel = interaction.guild.get_channel(ADMIN_CHANNEL_ID)
        pos_input = self.position.value.strip()
        
        role_status = "لم يتم العثور على رتبة مطابقة"
        if pos_input in ROLES_MAP:
            role_name = ROLES_MAP[pos_input]
            role = discord.utils.get(interaction.guild.roles, name=role_name)
            if role:
                try:
                    await interaction.user.add_roles(role)
                    role_status = f"✅ تم تفعيل رتبة **{role_name}** في العقد"
                except:
                    role_status = "⚠️ مشكلة في الصلاحيات (رتبة البوت نازلة)"

        embed = discord.Embed(title="📜 عقد لاعب جديد", color=discord.Color.dark_gold())
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.add_field(name="الطرف الأول (النادي)", value=interaction.guild.name, inline=True)
        embed.add_field(name="الطرف الثاني (اللاعب)", value=interaction.user.mention, inline=True)
        embed.add_field(name="الأيدي", value=self.ign.value, inline=True)
        embed.add_field(name="المركز المتفق عليه", value=pos_input, inline=True)
        embed.add_field(name="التقييم الفني (OVR)", value=self.overall.value, inline=True)
        embed.add_field(name="بنود إضافية", value=self.contract_terms.value or "لا يوجد", inline=False)
        embed.set_footer(text=f"الحالة التقنية: {role_status}")

        await admin_channel.send(embed=embed)
        await interaction.response.send_message(f"تهانينا {interaction.user.mention}! تم تسجيل عقدك بنجاح. {role_status}", ephemeral=True)

class ContractView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="✍️ تسجيل عقد لاعب", style=discord.ButtonStyle.success, custom_id="register_contract_btn")
    async def contract_button(self, interaction, button):
        await interaction.response.send_modal(PlayerContractModal())

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)
    async def setup_hook(self): self.add_view(ContractView())
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

@bot.tree.command(name="setup_contract", description="إرسال لوحة تسجيل العقود")
@app_commands.checks.has_permissions(administrator=True)
async def setup_contract(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📝 مركز تسجيل عقود اللاعبين",
        description=(
            "أهلاً بك في منصة تسجيل العقود الرسمية.\n\n"
            "يرجى الضغط على الزر أدناه لتوقيع عقدك مع النادي.\n"
            "سيتم منحك رتبة مركزك (هجوم، وسط، دفاع، حارس) تلقائياً بمجرد التسجيل."
        ),
        color=discord.Color.dark_gold()
    )
    await interaction.channel.send(embed=embed, view=ContractView())
    await interaction.response.send_message("تم إرسال لوحة العقود!", ephemeral=True)

keep_alive()
bot.run(TOKEN)
