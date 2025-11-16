import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import re

# ENV
load_dotenv()
TOKEN = os.getenv("TOKEN")

MAIN_ADMIN_ROLE_ID = int(os.getenv("MAIN_ADMIN_ROLE_ID", "0"))
EXTRA_ADMIN_ROLE_ID = None

LIST_CHANNEL_ID = None
LIST_MESSAGE_ID = None
LIST_ENTRIES = {}  # {1: "1) Tank – <@id>"}

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


# ---------------------------------------------------------------------
# ADMIN KONTROL
# ---------------------------------------------------------------------
def is_admin(user):
    role_ids = [r.id for r in getattr(user, "roles", [])]
    return (
        MAIN_ADMIN_ROLE_ID in role_ids or
        (EXTRA_ADMIN_ROLE_ID and EXTRA_ADMIN_ROLE_ID in role_ids)
    )


# ---------------------------------------------------------------------
# EMBED OLUŞTUR
# ---------------------------------------------------------------------
def build_embed():
    embed = discord.Embed(
        title="📋 Liste",
        color=0x3498db
    )

    # Liste satırlarını field olarak ekle
    for num in sorted(LIST_ENTRIES.keys()):
        embed.add_field(
            name=f"{num})",
            value=LIST_ENTRIES[num],
            inline=False
        )

    # Açıklama bloğu en alta
    embed.description = (
        "──────────────────────────────\n"
        "🔢 Sıraya girmek için sayı yazın\n"
        "🧽 Kendini silmek için: !benisil\n"
        "📘 Tüm komutlar: !yardım\n"
        "──────────────────────────────"
    )

    return embed


@bot.event
async def on_ready():
    print(f"Bot giriş yaptı: {bot.user}")


# ---------------------------------------------------------------------
# !listeolustur
# ---------------------------------------------------------------------
@bot.command()
async def listeolustur(ctx, *, liste):
    global LIST_CHANNEL_ID, LIST_MESSAGE_ID, LIST_ENTRIES

    LIST_ENTRIES = {}

    for line in liste.split("\n"):
        if ")" in line:
            num = int(line.split(")")[0])
            LIST_ENTRIES[num] = line.strip()

    embed = build_embed()
    msg = await ctx
