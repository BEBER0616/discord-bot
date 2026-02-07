import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import datetime
import asyncio

TOKEN = "여기에_봇_토큰"

ROLE_ID = 1385985951272009879  # 명령어 사용 가능한 역할 ID

# 인텐트
intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)

# DB
conn = sqlite3.connect("warns.db")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS warnings (
    user_id INTEGER PRIMARY KEY,
    count INTEGER,
    last_warn TEXT
)
""")
conn.commit()

# ===================== 유틸 =====================

def has_permission(member: discord.Member):
    return any(role.id == ROLE_ID for role in member.roles)

def get_warns(user_id):
    c.execute("SELECT count FROM warnings WHERE user_id=?", (user_id,))
    row = c.fetchone()
    return row[0] if row else 0

def add_warn(user_id):
    now = datetime.datetime.utcnow().isoformat()
    warns = get_warns(user_id) + 1

    c.execute("REPLACE INTO warnings (user_id, count, last_warn) VALUES (?,?,?)",
              (user_id, warns, now))
    conn.commit()
    return warns

# ===================== 자동 경고 감소 =====================

async def auto_warn_decay():
    await bot.wait_until_ready()
    while not bot.is_closed():
        now = datetime.datetime.utcnow()
        c.execute("SELECT user_id, count, last_warn FROM warnings")
        rows = c.fetchall()

        for user_id, count, last_warn in rows:
            if not last_warn:
                continue

            last_time = datetime.datetime.fromisoformat(last_warn)
            if (now - last_time).days >= 60:  # 2개월
                new_count = max(count - 1, 0)

                if new_count == 0:
                    c.execute("DELETE FROM warnings WHERE user_id=?", (user_id,))
                else:
                    c.execute("UPDATE warnings SET count=?, last_warn=? WHERE user_id=?",
                              (new_count, now.isoformat(), user_id))

                conn.commit()

        await asyncio.sleep(86400)  # 하루마다 체크

# ===================== 봇 준비 =====================

@bot.event
async def on_ready():
    await bot.tree.sync()
    bot.loop.create_task(auto_warn_decay())
    print(f"봇 온라인: {bot.user}")

# ===================== 기본 명령어 =====================

@bot.tree.command(name="ping")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")

@bot.tree.command(name="안녕")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message("안녕 😎")

# ===================== 타임아웃 =====================

@bot.tree.command(name="timeout")
@app_commands.describe(user="타임아웃할 유저", minutes="분")
async def timeout(interaction: discord.Interaction, user: discord.Member, minutes: int):
    if not has_permission(interaction.user):
        return await interaction.response.send_message("권한 없음", ephemeral=True)

    until = datetime.timedelta(minutes=minutes)
    await user.timeout(until)
    await interaction.response.send_message(f"{user.mention} 타임아웃 {minutes}분")

# ===================== 밴 =====================

@bot.tree.command(name="ban")
@app_commands.describe(user="밴할 유저", reason="사유")
async def ban(interaction: discord.Interaction, user: discord.Member, reason: str = "없음"):
    if not has_permission(interaction.user):
        return await interaction.response.send_message("권한 없음", ephemeral=True)

    await user.ban(reason=reason)
    await interaction.response.send_message(f"{user.mention} 영구밴됨 | 사유: {reason}")

# ===================== 경고 시스템 =====================

@bot.tree.command(name="warn")
@app_commands.describe(user="경고할 유저", reason="사유")
async def warn(interaction: discord.Interaction, user: discord.Member, reason: str = "없음"):
    if not has_permission(interaction.user):
        return await interaction.response.send_message("권한 없음", ephemeral=True)

    warns = add_warn(user.id)

    await interaction.response.send_message(f"{user.mention} 경고 {warns}/5 | {reason}")

    # 자동 처벌
    if warns == 1:
        await user.timeout(datetime.timedelta(minutes=30))
    elif warns == 2:
        await user.timeout(datetime.timedelta(hours=1))
    elif warns == 3:
        await user.timeout(datetime.timedelta(weeks=1))
    elif warns == 4:
        await user.kick(reason="경고 4회")
    elif warns >= 5:
        await user.ban(reason="경고 5회")

# ===================== 경고 확인 =====================

@bot.tree.command(name="warncheck")
async def warncheck(interaction: discord.Interaction, user: discord.Member):
    warns = get_warns(user.id)
    c.execute("SELECT last_warn FROM warnings WHERE user_id=?", (user.id,))
    row = c.fetchone()
    last_warn = row[0] if row else "없음"

    await interaction.response.send_message(
        f"{user.mention}\n경고 수: {warns}\n마지막 경고: {last_warn}"
    )

# ===================== 실행 =====================

bot.run(TOKEN)
