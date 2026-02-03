import discord
from discord.ext import commands
import os
from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive"

def run():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

def keep_alive():
    Thread(target=run).start()

keep_alive()

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=".", intents=intents)

@bot.event
async def on_ready():
    print(f"봇 온라인! {bot.user}")

@bot.command()
async def 안녕(ctx):
    await ctx.send("안녕하세요! 저는 명령어 봇입니다 🤖")

bot.run(TOKEN)
