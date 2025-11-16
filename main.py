import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import re

load_dotenv()

TOKEN = os.getenv("TOKEN")

LIST_CHANNEL_ID = None
LIST_MESSAGE_ID = None
ADMIN_ROLE_ID = None  # admin rol kaydı

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


# Admin kontrol fonksiyonu
def is_admin(member):
    if ADMIN_ROLE_ID is None:
        return False
    return any(role.id == ADMIN_ROLE_ID for role in member.roles)


@bot.event
async def on_ready():
    print(f"Bot giriş yaptı: {bot.user}")


# -----------------------------
# 1) Liste Oluşturma (YENİ KOMUT: !listeolustur)
# -----------------------------
@bot.command()
async def listeolustur(ctx, *, liste):
    """Liste oluşturur ve bot mesajını düzenlenebilir hale getirir."""
    global LIST_CHANNEL_ID, LIST_MESSAGE_ID

    msg = await ctx.send(liste)

    LIST_CHANNEL_ID = msg.channel.id
    LIST_MESSAGE_ID = msg.id

    await ctx.reply("✅ Liste oluşturuldu!")


# -----------------------------
# 2) Listeyi Göster
# -----------------------------
@bot.command()
async def listegoster(ctx):
    """Kayıtlı listeyi tekrar gösterir."""
    global LIST_CHANNEL_ID, LIST_MESSAGE_ID

    if LIST_MESSAGE_ID is None:
        return await ctx.reply("❌ Henüz bir liste yok.")

    channel = bot.get_channel(LIST_CHANNEL_ID)
    msg = await channel.fetch_message(LIST_MESSAGE_ID)

    await ctx.reply(f"📌 Mevcut liste:\n\n{msg.content}")


# -----------------------------
# 3) Listeyi Sıfırla
# -----------------------------
@bot.command()
async def listesifirla(ctx):
    """Listeyi tamamen temizler."""
    global LIST_MESSAGE_ID, LIST_CHANNEL_ID

    if LIST_MESSAGE_ID is None:
        return await ctx.reply("❌ Liste zaten yok.")

    if not is_admin(ctx.author):
        return await ctx.reply("❌ Bu komut sadece admin rolüne sahip olanlar tara
