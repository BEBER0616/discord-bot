import discord
from discord import app_commands
from discord.ext import commands

ROLE_ID = 1385985951272009879

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print("봇 준비 완료")

def has_role(interaction):
    return any(role.id == ROLE_ID for role in interaction.user.roles)

# ✅ 타임아웃
@bot.tree.command(name="timeout", description="유저 타임아웃")
async def timeout(interaction: discord.Interaction, member: discord.Member, minutes: int):
    await interaction.response.defer(ephemeral=True)

    if not has_role(interaction):
        return await interaction.followup.send("❌ 권한 없음", ephemeral=True)

    duration = discord.utils.utcnow() + discord.timedelta(minutes=minutes)
    await member.timeout(duration)

    await interaction.followup.send(f"✅ {member.mention} {minutes}분 타임아웃")

# ✅ 밴
@bot.tree.command(name="ban", description="유저 밴")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "사유 없음"):
    await interaction.response.defer(ephemeral=True)

    if not has_role(interaction):
        return await interaction.followup.send("❌ 권한 없음", ephemeral=True)

    await member.ban(reason=reason)
    await interaction.followup.send(f"🔨 {member} 밴됨 | 사유: {reason}")

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"봇 온라인! {bot.user}")

# /안녕
@bot.tree.command(name="안녕", description="봇 인사")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message("안녕하세요! 저는 명령어 봇입니다 🤖")


bot.run("토큰")
