import discord
from discord import app_commands
from discord.ext import commands, tasks
import os
import json
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread

# ===== Flask 서버 (Render 살아있게) =====
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive"

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    Thread(target=run).start()

keep_alive()
# =====================================

TOKEN = os.getenv("TOKEN")
ADMIN_ROLE_ID = 1385985951272009879  # 권한 역할 ID

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)

# ===== 경고 저장 파일 =====
WARN_FILE = "warnings.json"

def load_warns():
    if not os.path.exists(WARN_FILE):
        return {}
    with open(WARN_FILE, "r") as f:
        return json.load(f)

def save_warns(data):
    with open(WARN_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ===== 자동 경고 차감 (60일) =====
@tasks.loop(hours=12)
async def auto_warn_decay():
    warns = load_warns()
    now = datetime.utcnow()

    for guild_id in list(warns.keys()):
        for user_id in list(warns[guild_id].keys()):
            warns[guild_id][user_id] = [
                w for w in warns[guild_id][user_id]
                if now - datetime.fromisoformat(w) < timedelta(days=60)
            ]

            if not warns[guild_id][user_id]:
                del warns[guild_id][user_id]

    save_warns(warns)
    print("경고 자동 차감 완료")

# ===== 봇 준비 =====
@bot.event
async def on_ready():
    await bot.tree.sync()
    auto_warn_decay.start()
    print(f"봇 온라인! {bot.user}")

# ===== 권한 체크 =====
def has_admin_role(interaction):
    return any(role.id == ADMIN_ROLE_ID for role in interaction.user.roles)

# ===== /ping =====
@bot.tree.command(name="ping")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong!")

# ===== /안녕 =====
@bot.tree.command(name="안녕")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message("안녕하세요! 저는 관리 봇입니다 🤖")

# ===== /timeout =====
@bot.tree.command(name="timeout")
@app_commands.describe(user="타임아웃할 유저", minutes="분")
async def timeout(interaction: discord.Interaction, user: discord.Member, minutes: int):
    if not has_admin_role(interaction):
        return await interaction.response.send_message("권한 없음", ephemeral=True)

    until = datetime.utcnow() + timedelta(minutes=minutes)
    await user.timeout(until)
    await interaction.response.send_message(f"{user.mention} 타임아웃 {minutes}분")

# ===== /ban =====
@bot.tree.command(name="ban")
async def ban(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason"):
    if not has_admin_role(interaction):
        return await interaction.response.send_message("권한 없음", ephemeral=True)

    await user.ban(reason=reason)
    await interaction.response.send_message(f"{user} 영구밴 완료")

# ===== /warn =====
@bot.tree.command(name="warn")
async def warn(interaction: discord.Interaction, user: discord.Member):
    if not has_admin_role(interaction):
        return await interaction.response.send_message("권한 없음", ephemeral=True)

    warns = load_warns()
    gid = str(interaction.guild.id)
    uid = str(user.id)

    warns.setdefault(gid, {})
    warns[gid].setdefault(uid, [])
    warns[gid][uid].append(datetime.utcnow().isoformat())

    warn_count = len(warns[gid][uid])
    save_warns(warns)

    # ===== 자동 처벌 =====
    if warn_count == 1:
        await user.timeout(datetime.utcnow() + timedelta(minutes=30))
        msg = "경고 1 → 30분 타임아웃"
    elif warn_count == 2:
        await user.timeout(datetime.utcnow() + timedelta(hours=1))
        msg = "경고 2 → 1시간 타임아웃"
    elif warn_count == 3:
        await user.timeout(datetime.utcnow() + timedelta(days=7))
        msg = "경고 3 → 1주 타임아웃"
    elif warn_count == 4:
        await user.kick()
        msg = "경고 4 → 서버 추방"
    elif warn_count >= 5:
        await user.ban()
        msg = "경고 5 → 영구밴"
    else:
        msg = "경고 추가됨"

    await interaction.response.send_message(f"{user.mention} 경고 {warn_count}회 | {msg}")

# ===== /warnings =====
@bot.tree.command(name="warnings")
async def warnings(interaction: discord.Interaction, user: discord.Member):
    warns = load_warns()
    gid = str(interaction.guild.id)
    uid = str(user.id)

    count = len(warns.get(gid, {}).get(uid, []))
    await interaction.response.send_message(f"{user.mention} 경고 수: {count}")

# ===== 실행 =====
bot.run(TOKEN)
