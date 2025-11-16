import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
LIST_CHANNEL_ID = os.getenv("LIST_CHANNEL_ID")
LIST_MESSAGE_ID = os.getenv("LIST_MESSAGE_ID")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot giriş yaptı: {bot.user}")

@bot.command()
async def liste_ayarla(ctx):
    """Liste mesajını ayarlar (mesaja reply olarak kullanılacak)."""
    global LIST_CHANNEL_ID, LIST_MESSAGE_ID

    if not ctx.message.reference:
        return await ctx.reply("Bu komutu **liste mesajına cevap atarak** kullanmalısın.")

    LIST_CHANNEL_ID = str(ctx.channel.id)
    LIST_MESSAGE_ID = str(ctx.message.reference.message_id)

    print("Kayıt yapıldı:", LIST_CHANNEL_ID, LIST_MESSAGE_ID)

    await ctx.reply("✅ Liste mesajı kaydedildi!")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    await bot.process_commands(message)

    global LIST_CHANNEL_ID, LIST_MESSAGE_ID

    # sadece sayı yazılmış mı?
    if message.content.isdigit():
        if not LIST_CHANNEL_ID or not LIST_MESSAGE_ID:
            return

        num = int(message.content)

        channel = bot.get_channel(int(LIST_CHANNEL_ID))
        if not channel:
            return

        try:
            list_msg = await channel.fetch_message(int(LIST_MESSAGE_ID))
        except:
            return

        lines = list_msg.content.split("\n")

        idx = next((i for i, l in enumerate(lines) if l.strip().startswith(f"{num})")), None)

        if idx is None:
            return

        # Eski mention temizle
        import re
        lines[idx] = re.sub(r"–\s*<@!?\d+>", "", lines[idx]).strip()

        # Yeni mention ekle
        lines[idx] = f"{lines[idx]} – <@{message.author.id}>"

        await list_msg.edit(content="\n".join(lines))

bot.run(TOKEN)
