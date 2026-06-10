import discord
from discord.ext import commands
from discord import app_commands
import os
import requests
from flask import Flask
from threading import Thread

# --- نظام الاستيقاظ (للحفاظ على البوت أونلاين) ---
app = Flask('')
@app.route('/')
def home(): return "Pro Club Bot is Online!"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# --- إعدادات البوت الآيديات ---
TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
SUGGESTIONS_CHANNEL_ID = 1511935406739034273  # روم الاقتراحات
ADMIN_CHANNEL_ID = 1512689809150312468       # روم الإدارة والعقود
TIKTOK_SUPPORT_CHANNEL_ID = 1512953662635380847        # <--- حط آيدي روم دعم التيك توك هنا

# --- قاموس الرتب التلقائية ---
ROLES_MAP = {
    "هجوم": "هجوم",
    "وسط": "وسط",
    "دفاع": "دفاع",
    "حارس": "حارس"
}

# --- نظام تسجيل العقود (Modal) ---
class PlayerContractModal(discord.ui.Modal, title='تسجيل عقد لاعب جديد'):
    ign = discord.ui.TextInput(label='الأيدي (PSN / EA ID)', placeholder='اكتب الأيدي هنا...', required=True)
    position = discord.ui.TextInput(label='المركز (هجوم، وسط، دفاع، حارس)', placeholder='اكتب مركزك هنا...', required=True)
    overall = discord.ui.TextInput(label='الأوفر (Overall)', placeholder='مثال: 90', required=True)
    terms = discord.ui.TextInput(label='ملاحظات أو خبرات سابقة', style=discord.TextStyle.paragraph, required=False)

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
                    role_status = f"✅ تم تفعيل رتبة **{role_name}**"
                except:
                    role_status = "⚠️ مشكلة في الصلاحيات (رتبة البوت نازلة)"

        embed = discord.Embed(title="📜 عقد لاعب جديد", color=discord.Color.dark_gold())
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.add_field(name="النادي", value=interaction.guild.name, inline=True)
        embed.add_field(name="اللاعب", value=interaction.user.mention, inline=True)
        embed.add_field(name="المركز", value=pos_input, inline=True)
        embed.add_field(name="الحالة", value=role_status, inline=False)
        
        await admin_channel.send(embed=embed)
        await interaction.response.send_message(f"تهانينا {interaction.user.mention}! تم تسجيل عقدك. {role_status}", ephemeral=True)

class ContractView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="✍️ تسجيل عقد لاعب", style=discord.ButtonStyle.success, custom_id="reg_contract_btn")
    async def contract_btn(self, interaction, button):
        await interaction.response.send_modal(PlayerContractModal())

# --- إعداد البوت الرئيسي ---
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.add_view(ContractView())

    async def on_ready(self):
        print(f'Logged in as {self.user}')
        await self.tree.sync()

bot = MyBot()

# --- نظام الاقتراحات ---
@bot.event
async def on_message(message):
    if message.author == bot.user: return
    
    # معالجة الأوامر العادية (علامة التعجب) أولاً لمنع تعطل أمر الفحص
    await bot.process_commands(message)
    
    if message.channel.id == SUGGESTIONS_CHANNEL_ID:
        admin_channel = bot.get_channel(ADMIN_CHANNEL_ID)
        embed = discord.Embed(title="💡 اقتراح جديد", description=message.content, color=discord.Color.gold())
        embed.set_footer(text=f"بواسطة: {message.author}")
        await admin_channel.send(embed=embed)
        await message.delete()

# --- أمر فحص اليوزرات ---
@bot.command(name="فحص")
async def check_user(ctx, username: str):
    username = username.lower()
    url = f"https://www.instagram.com/{username}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 404:
            await ctx.send(f"🎯 **{username}** | غالباً متاح وكشخة! الحق عليه وسجله بسرعة.🏃‍♂️")
        elif response.status_code == 200:
            await ctx.send(f"❌ **{username}** | اليوزر هذا مستخدم ومأخوذ من قبل.")
        else:
            await ctx.send("⚠️ تعذر الفحص حالياً، جرب مرة ثانية بعد شوي.")
    except requests.exceptions.RequestException:
        await ctx.send("❌ حدث خطأ أثناء الاتصال بالشبكة.")

# --- أمر تفعيل لوحة العقود ---
@bot.tree.command(name="setup_contract", description="إرسال لوحة تسجيل العقود")
@app_commands.checks.has_permissions(administrator=True)
async def setup_contract(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📝 مركز تسجيل عقود اللاعبين",
        description="اضغط على الزر لتوقيع عقدك. ستحصل على رتبة مركزك تلقائياً!",
        color=discord.Color.dark_gold()
    )
    await interaction.channel.send(embed=embed, view=ContractView())
    await interaction.response.send_message("تم التفعيل!", ephemeral=True)

# --- أمر دعم التيك توك ---
@bot.tree.command(name="post_tiktok", description="نشر فيديو جديد لدعم التيك توك")
@app_commands.checks.has_permissions(administrator=True)
async def post_tiktok(interaction: discord.Interaction, video_url: str):
    channel = bot.get_channel(TIKTOK_SUPPORT_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="🎬 مقطع جديد للنادي على تيك توك!",
            description=f"يا وحوش نزل مقطع جديد، فجروه لايكات وكومنتات عشان يطلع إكسبلور! 🔥\n\n🔗 [اضغط هنا لمشاهدة المقطع]({video_url})",
            color=discord.Color.from_rgb(255, 0, 80)
        )
        msg = await channel.send(content="@everyone", embed=embed)
        # إضافة تفاعلات تلقائية للعيال
        await msg.add_reaction("❤️")
        await msg.add_reaction("💬")
        await msg.add_reaction("🚀")
        await interaction.response.send_message("تم النشر بنجاح!", ephemeral=True)
    else:
        await interaction.response.send_message("خطأ: تأكد من آيدي روم الدعم في الكود.", ephemeral=True)

keep_alive()
bot.run(TOKEN)
