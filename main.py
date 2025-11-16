import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import re

load_dotenv()

TOKEN = os.getenv("TOKEN")

LIST_CHANNEL_ID = None
LIST_MESSAGE_ID = None

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot giriş yaptı: {bot.user}")


# -----------------------------
#  KOMUT: LİSTE OLUŞTUR
# -----------------------------
@bot.command()
async def liste_olustur(ctx, *, liste):
    global LIST_CHANNEL_ID, LIST_MESSAGE_ID

    msg = await ctx.send(liste)

    LIST_CHANNEL_ID = msg.channel.id
    LIST_MESSAGE_ID = msg.id

    await ctx.reply("✅ Liste oluşturuldu! Artık kullanıcılar sayı yazabilir.")


# -----------------------------
#  MESAJ EVENTİ (sayı kontrolü)
# -----------------------------
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # BUNUN MUTLAKA EN ÜSTE YAKIN OLMASI GEREKİYOR
    await bot.process_commands(message)

    global LIST_CHANNEL_ID, LIST_MESSAGE_ID

    if LIST_CHANNEL_ID is None or LIST_MESSAGE_ID is None:
        return

    # sadece sayı yazıldıysa devam et
    if not message.content.isdigit():
        return

    num = int(message.content)

    channel = bot.get_channel(LIST_CHANNEL_ID)
    if not channel:
        return

    try:
        list_msg = await channel.fetch_message(LIST_MESSAGE_ID)
    except:
        return

    lines = list_msg.content.split("\n")

    # DOĞRU PARANTEZ DÜZELTİLDİ
    idx = next((i for i, l in enumerate(lines) if l.strip().startswith(f"{num})")), None)

    if idx is None:
        return

    # eski mention sil
    lines[idx] = re.sub(r"–\s*<@!?\d+>", "", lines[idx]).strip()

    # yeni mention ekle
    lines[idx] = f"{lines[idx]} – <@{message.author.id}>"

    # bot mesajı → düzenleyebilir
    await list_msg.edit(content="\n".join(lines))


bot.run(TOKEN)
