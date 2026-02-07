import discord
from discord.ext import commands
import os
import json
from datetime import datetime, timedelta

TOKEN = os.getenv("TOKEN")  # Render 환경변수

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

ROLE_ID = 1385985951272009879  # 관리자 역할 ID
WARN_FILE = "warnings.json"


# ===== 경고 저장 =====
def load_warnings():
    if not os.path.exists(WARN_FILE):
        return {}
    with open(WARN_FILE, "r") as f:
        return json.load(f)


def save_warnings(data):
    with open(WARN_FILE, "w") as f:
        json.dump(data, f, indent=4)


# ===== 역할 체크 =====
def has_role(member):
    return any(role.id == ROLE_ID for role in member.roles)


# ===== 봇 준비 =====
@bot.event
async def on_ready():
    print(f"봇 온라인! {bot.user}")
    await bot.tree.sync()
    print("슬래시 명령어 동기화 완료!")


# ===== 기본 명령어 =====
@bot.tree.command(name="ping")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong!")


@bot.tree.command(name="안녕")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message("안녕하세요! 🤖")


# ===== 경고 시스템 =====
@bot.tree.command(name="경고")
async def warn(interaction: discord.Interaction, user: discord.Member, reason: str = "이유 없음"):
    if not has_role(interaction.user):
        await interaction.response.send_message("❌ 권한 없음", ephemeral=True)
        return

    data = load_warnings()
    uid = str(user.id)

    if uid not in data:
        data[uid] = []

    data[uid].append({"time": datetime.utcnow().isoformat(), "reason": reason})
    save_warnings(data)

    warn_count = len(data[uid])

    await interaction.response.send_message(f"⚠️ {user.mention} 경고 {warn_count}회 (이유: {reason})")

    # ===== 자동 처벌 =====
    if warn_count == 1:
        await user.timeout(timedelta(minutes=30))
        await interaction.followup.send("⏳ 30분 타임아웃 적용")

    elif warn_count == 2:
        await user.timeout(timedelta(hours=1))
        await interaction.followup.send("⏳ 1시간 타임아웃 적용")

    elif warn_count == 3:
        await user.timeout(timedelta(weeks=1))
        await interaction.followup.send("⏳ 1주 타임아웃 적용")

    elif warn_count == 4:
        await user.kick(reason="경고 4회 누적")
        await interaction.followup.send("👢 서버 추방됨")

    elif warn_count >= 5:
        await user.ban(reason="경고 5회 누적")
        await interaction.followup.send("🔨 영구 밴됨")


# ===== 경고 확인 =====
@bot.tree.command(name="경고확인")
async def check_warn(interaction: discord.Interaction, user: discord.Member):
    data = load_warnings()
    uid = str(user.id)

    if uid not in data or len(data[uid]) == 0:
        await interaction.response.send_message("경고 없음")
        return

    msg = f"⚠️ {user} 경고 목록:\n"
    for i, w in enumerate(data[uid], 1):
        msg += f"{i}. {w['reason']} ({w['time']})\n"

    await interaction.response.send_message(msg)


# ===== 경고 삭제 =====
@bot.tree.command(name="경고삭제")
async def clear_warn(interaction: discord.Interaction, user: discord.Member):
    if not has_role(interaction.user):
        await interaction.response.send_message("❌ 권한 없음", ephemeral=True)
        return

    data = load_warnings()
    uid = str(user.id)

    if uid in data:
        del data[uid]
        save_warnings(data)

    await interaction.response.send_message(f"{user} 경고 초기화 완료")


# ===== 경고 자동 2개월 삭제 시스템 =====
@bot.event
async def on_member_join(member):
    data = load_warnings()
    uid = str(member.id)

    if uid not in data:
        return

    new_list = []
    for w in data[uid]:
        t = datetime.fromisoformat(w["time"])
        if datetime.utcnow() - t < timedelta(days=60):
            new_list.append(w)

    data[uid] = new_list
    save_warnings(data)


bot.run(TOKEN)
