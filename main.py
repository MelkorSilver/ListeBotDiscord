import os
import re
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
ADMIN_ROLE_ID = int(os.getenv("ADMIN_ROLE_ID", 0))

# Liste mesajının konumu
LIST_CHANNEL_ID = None
LIST_MESSAGE_ID = None

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


# ----------------------------------------------------------------------
# BOT AÇILDI
# ----------------------------------------------------------------------
@bot.event
async def on_ready():
    print(f"Bot giriş yaptı: {bot.user}")


# ----------------------------------------------------------------------
# LİSTE OLUŞTURMA KOMUTU
# ----------------------------------------------------------------------
@bot.command()
async def liste_olustur(ctx, *, liste):
    """Botun düzenleyebileceği bir liste mesajı oluşturur."""
    global LIST_CHANNEL_ID, LIST_MESSAGE_ID

    msg = await ctx.send(liste)

    LIST_CHANNEL_ID = msg.channel.id
    LIST_MESSAGE_ID = msg.id

    await ctx.reply("✅ Liste oluşturuldu! Kullanıcılar sayı yazarak adlarını ekleyebilir.")


# ----------------------------------------------------------------------
# SAYI YAZILDIĞINDA MENTION EKLEME
# ----------------------------------------------------------------------
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    await bot.process_commands(message)

    global LIST_CHANNEL_ID, LIST_MESSAGE_ID

    # Liste yoksa geç
    if LIST_CHANNEL_ID is None or LIST_MESSAGE_ID is None:
        return

    # Sadece sayı ise işleme al
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

    # İlgili satırı bul
    idx = next((i for i, l in enumerate(lines) if l.strip().startswith(f"{num})")), None)

    if idx is None:
        return

    # Eski mention'ı sil
    lines[idx] = re.sub(r"–\s*<@!?\d+>", "", lines[idx]).strip()

    # Yeni mention ekle
    lines[idx] = f"{lines[idx]} – <@{message.author.id}>"

    # Mesajı edit et
    await list_msg.edit(content="\n".join(lines))


# ----------------------------------------------------------------------
# MENTION SİLME KOMUTU
# ----------------------------------------------------------------------
@bot.command()
async def sil(ctx, sayi: int):
    """Kullanıcı kendi mention'unu silebilir; admin rolü herkesinkini silebilir."""
    global LIST_CHANNEL_ID, LIST_MESSAGE_ID, ADMIN_ROLE_ID

    if LIST_CHANNEL_ID is None or LIST_MESSAGE_ID is None:
        return await ctx.reply("❌ Önce liste oluşturmalısın.")

    channel = bot.get_channel(LIST_CHANNEL_ID)
    try:
        list_msg = await channel.fetch_message(LIST_MESSAGE_ID)
    except:
        return await ctx.reply("❌ Liste mesajı bulunamadı.")

    lines = list_msg.content.split("\n")

    # Satırı bul
    idx = next((i for i, l in enumerate(lines) if l.strip().startswith(f"{sayi})")), None)

    if idx is None:
        return await ctx.reply("❌ Bu numaraya ait satır yok.")

    # Satırdaki mention'u bul
    mention_match = re.search(r"<@!?(\d+)>", lines[idx])

    if not mention_match:
        return await ctx.reply("❌ Bu satırda mention yok.")

    mention_user_id = int(mention_match.group(1))

    # Kullanıcı admin rolünde mi?
    member = ctx.author
    is_admin = False
    if ADMIN_ROLE_ID != 0:
        is_admin = any(role.id == ADMIN_ROLE_ID for role in member.roles)

    # Yetkisi yoksa sadece kendi mention'unu silebilir
    if not is_admin and mention_user_id != ctx.author.id:
        return await ctx.reply("❌ Bu mention sana ait değil, silemezsin.")

    # Mention'ı temizle
    lines[idx] = re.sub(r"–\s*<@!?\d+>", "", lines[idx]).strip()

    await list_msg.edit(content="\n".join(lines))

    if is_admin:
        await ctx.reply(f"🛡️ Admin olarak {sayi}. satırdaki mention'u sildin!")
    else:
        await ctx.reply(f"✅ {sayi}. satırdaki kendi adın silindi!")


# ----------------------------------------------------------------------
# BOTU ÇALIŞTIR
# ----------------------------------------------------------------------
bot.run(TOKEN)
