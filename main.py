import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import re

# Load .env
load_dotenv()

TOKEN = os.getenv("TOKEN")

# Railway → Variables → MAIN_ADMIN_ROLE_ID (zorunlu)
MAIN_ADMIN_ROLE_ID = int(os.getenv("MAIN_ADMIN_ROLE_ID", "0"))

# Sonradan !adminekle ile ayarlanacak
EXTRA_ADMIN_ROLE_ID = None

LIST_CHANNEL_ID = None
LIST_MESSAGE_ID = None
LIST_DATA = {}  # embed içeriği için

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


# -----------------------
# ADMIN KONTROL FONKSİYONU
# -----------------------
def is_admin(user):
    global MAIN_ADMIN_ROLE_ID, EXTRA_ADMIN_ROLE_ID
    if not hasattr(user, "roles"):
        return False

    role_ids = [r.id for r in user.roles]

    if MAIN_ADMIN_ROLE_ID in role_ids:
        return True

    if EXTRA_ADMIN_ROLE_ID and EXTRA_ADMIN_ROLE_ID in role_ids:
        return True

    return False


# -----------------------
# BOT BAŞLANGICI
# -----------------------
@bot.event
async def on_ready():
    print(f"Bot giriş yaptı: {bot.user}")


# -----------------------
# YARDIM KOMUTU
# -----------------------
@bot.command()
async def yardım(ctx):
    embed = discord.Embed(
        title="📌 Komut Listesi",
        description="Botun tüm komutları aşağıdadır:",
        color=0x4CAF50
    )

    embed.add_field(name="!listeolustur metin", value="Yeni bir liste oluşturur.", inline=False)
    embed.add_field(name="!listegoster", value="Mevcut listeyi embed olarak gösterir.", inline=False)
    embed.add_field(name="!listesifirla", value="Listeyi tamamen sıfırlar. (Sadece admin)", inline=False)
    embed.add_field(name="!benisil", value="Kendi isminizi listeden siler.", inline=False)
    embed.add_field(name="!adminekle @rol", value="Ek bir admin rolü ekler. (Sadece ana admin)", inline=False)
    embed.add_field(name="Sayınızı yazın", value="Sayı yazan kişinin ismi ilgili satıra işlenir.", inline=False)

    embed.set_footer(text="Liste Bot • Developed by ChatGPT")

    await ctx.send(embed=embed)


# -----------------------
# LİSTE OLUŞTURMA
# -----------------------
@bot.command()
async def listeolustur(ctx, *, liste):
    """Listeyi embed olarak oluşturur ve işlenebilir hale getirir."""
    global LIST_CHANNEL_ID, LIST_MESSAGE_ID, LIST_DATA

    LIST_DATA = {}
    lines = liste.split("\n")

    embed = discord.Embed(title="📋 Liste", color=0x3498db)

    for line in lines:
        if ")" in line:
            num = line.split(")")[0].strip()
            LIST_DATA[int(num)] = line

    text = "\n".join(lines)
    msg = await ctx.send(embed=discord.Embed(title="📋 Liste", description=text, color=0x3498db))

    LIST_CHANNEL_ID = msg.channel.id
    LIST_MESSAGE_ID = msg.id

    await ctx.reply("✅ Liste oluşturuldu! Kullanıcılar sayı yazabilir.")


# -----------------------
# LİSTE GÖSTER
# -----------------------
@bot.command()
async def listegoster(ctx):
    if LIST_MESSAGE_ID is None:
        return await ctx.reply("❌ Henüz bir liste oluşturulmadı.")

    channel = bot.get_channel(LIST_CHANNEL_ID)
    msg = await channel.fetch_message(LIST_MESSAGE_ID)

    embed = discord.Embed(title="📋 Mevcut Liste", description=msg.embeds[0].description, color=0x3498db)
    await ctx.send(embed=embed)


# -----------------------
# LİSTE SIFIRLA
# -----------------------
@bot.command()
async def listesifirla(ctx):
    global LIST_CHANNEL_ID, LIST_MESSAGE_ID, LIST_DATA

    if not is_admin(ctx.author):
        return await ctx.reply("❌ Bu komutu sadece adminler kullanabilir.")

    LIST_CHANNEL_ID = None
    LIST_MESSAGE_ID = None
    LIST_DATA = {}

    await ctx.reply("🗑️ Liste sıfırlandı!")


# -----------------------
# KENDİ MENTION SİLME
# -----------------------
@bot.command()
async def benisil(ctx):
    """Kullanıcı kendi adını listeden sildirebilir."""
    global LIST_CHANNEL_ID, LIST_MESSAGE_ID

    if LIST_MESSAGE_ID is None:
        return await ctx.reply("❌ Liste yok.")

    channel = bot.get_channel(LIST_CHANNEL_ID)
    msg = await channel.fetch_message(LIST_MESSAGE_ID)

    lines = msg.embeds[0].description.split("\n")

    user_tag = f"<@{ctx.author.id}>"

    new_lines = [re.sub(r"–\s*<@!?\d+>", "", line) if user_tag in line else line for line in lines]

    new_text = "\n".join(new_lines)
    new_embed = discord.Embed(title="📋 Liste", description=new_text, color=0x3498db)

    await msg.edit(embed=new_embed)
    await ctx.reply("🧹 İsmin listeden silindi!")


# -----------------------
# ADMİN EKLEME
# -----------------------
@bot.command()
async def adminekle(ctx, rol: discord.Role):
    global EXTRA_ADMIN_ROLE_ID

    # sadece MAIN_ADMIN_ROLE_ID kullanabilir
    if MAIN_ADMIN_ROLE_ID not in [r.id for r in ctx.author.roles]:
        return await ctx.reply("❌ Bu komutu sadece ana admin kullanabilir.")

    EXTRA_ADMIN_ROLE_ID = rol.id
    await ctx.reply(f"🔐 `{rol.name}` artık admin rolü olarak ayarlandı!")


# -----------------------
# SAYI YAZAN İŞLENİR
# -----------------------
@bot.event
async def on_message(message):
    global LIST_CHANNEL_ID, LIST_MESSAGE_ID

    if message.author.bot:
        return

    await bot.process_commands(message)

    # Sayı değilse devam etmesin
    if not message.content.isdigit():
        return

    if LIST_MESSAGE_ID is None:
        return

    num = int(message.content)

    channel = bot.get_channel(LIST_CHANNEL_ID)
    msg = await channel.fetch_message(LIST_MESSAGE_ID)

    lines = msg.embeds[0].description.split("\n")

    idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith(f"{num})"):
            idx = i
            break

    if idx is None:
        return

    # eski mention kaldır
    lines[idx] = re.sub(r"–\s*<@!?\d+>", "", lines[idx]).strip()

    # yeni mention ekle
    lines[idx] = f"{lines[idx]} – <@{message.author.id}>"

    new_text = "\n".join(lines)
    new_embed = discord.Embed(title="📋 Liste", description=new_text, color=0x3498db)

    await msg.edit(embed=new_embed)


# -----------------------
# BOTU ÇALIŞTIR
# -----------------------
bot.run(TOKEN)
