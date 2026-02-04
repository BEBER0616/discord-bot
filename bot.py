import discord
from discord import app_commands
from discord.ext import commands
import os
from datetime import timedelta
from flask import Flask
from threading import Thread

# ================= Flask (Render 유지용) =================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive"

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    Thread(target=run).start()

keep_alive()
# =======================================================


# ===== 디스코드 토큰 =====
TOKEN = os.getenv("TOKEN")  # Render 환경변수


# ===== Intents =====
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents)

# ✅ 허용할 역할 ID
ALLOWED_ROLE_ID = 1385985951272009879

# 역할 체크 함수
def has_role_id(member):
    return any(role.id == ALLOWED_ROLE_ID for role in member.roles)


# ================= 봇 시작 =================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"봇 온라인! {bot.user}")


# ================= Slash 타임아웃 =================
@bot.tree.command(name="timeout", description="유저 타임아웃")
async def timeout(interaction: discord.Interaction, member: discord.Member, minutes: int):

    if not has_role_id(interaction.user):
        await interaction.response.send_message("❌ 권한 없음", ephemeral=True)
        return

    duration = timedelta(minutes=minutes)
    await member.timeout(duration)
    await interaction.response.send_message(f"⏳ {member.mention} {minutes}분 타임아웃!")


# ================= Slash 밴 =================
@bot.tree.command(name="ban", description="유저 밴")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "사유 없음"):

    if not has_role_id(interaction.user):
        await interaction.response.send_message("❌ 권한 없음", ephemeral=True)
        return

    await member.ban(reason=reason)
    await interaction.response.send_message(f"🔨 {member} 밴됨 | 이유: {reason}")


# ================= 테스트 명령어 =================
@bot.tree.command(name="ping", description="봇 상태 확인")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong! 봇 정상 작동 중")


bot.run(TOKEN)
