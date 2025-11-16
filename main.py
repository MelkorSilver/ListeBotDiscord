import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import re

# ENV yükle
load_dotenv()
TOKEN = os.getenv("TOKEN")

# Railway → Variables → MAIN_ADMIN_ROLE_ID (zorunlu)
MAIN_ADMIN_ROLE_ID = int(os.getenv("MAIN_ADMIN_ROLE_ID", "0"))
EXTRA_ADMIN_ROLE_ID = None

LIST_CHANNEL_ID = None
LIST_MESSAGE_ID = None

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


# ----------------------------
# ADMIN KONTROL
# ----------------------------
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


@bot.event
async def on_ready():
    print(f"Bot giriş yaptı: {bot.user}")


# ----------------------------
# YARDIM KOMUTU
# ----------------------------
@bot.command()
async def yardım(ctx):
    embed = discord.Embed(
        title="📌 Komut Listesi",
        description="Aşağıdaki komutları kullanabilirsiniz:",
        color=0x4CAF50
    )

    embed.add_field(name="!listeolustur metin", value="Yeni liste oluşturur.", inline=False)
    embed.add_field(name="!listegoster", value="Mevcut listeyi gösterir.", inline=False)
    embed.add_field(name="!listesifirla", value="Listeyi sıfırlar. (Admin)", inline=False)
    embed.add_field(name="!benisil", value="Kendi ismini listeden siler.", inline=False)
    embed.add_field(name="!adminekle @rol", value="Ek admin rolü ekler. (Ana admin)", inline=False)
    embed.add_field(name="Sayı yaz", value="Sayı yazınca ilgili satıra adın eklenir.", inline=False)

    await ctx.send(embed=embed)


# ----------------------------
# LİSTE OLUŞTUR
# ----------------------------
@bot.command()
async def listeolustur(ctx, *, liste):
    global LIST_CHANNEL_ID, LIST_MESSAGE_ID

    lines = liste.split("\n")

    final_text = "\n".join(lines) + \
        "\n──────────────────────────────\n" \
        "🔢 Sıraya girmek için sayı yazın\n" \
        "🧽 Kendini silmek için: !benisil\n" \
        "📘 Tüm komutlar: !yardım\n" \
        "──────────────────────────────"

    embed = discord.Embed(
        title="📋 Liste",
        description=final_text,
        color=0x3498db
    )

    msg = await ctx.send(embed=embed)

    LIST_CHANNEL_ID = msg.channel.id
    LIST_MESSAGE_ID = msg.id

    await ctx.reply("✅ Liste oluşturuldu! Kullanıcılar sayı yazabilir.")


# ----------------------------
# LİSTE GÖSTER
# ----------------------------
@bot.command()
async def listegoster(ctx):
    if LIST_MESSAGE_ID is None:
        return await ctx.reply("❌ Liste oluşturulmamış.")

    channel = bot.get_channel(LIST_CHANNEL_ID)
    msg = await channel.fetch_message(LIST_MESSAGE_ID)

    await ctx.send(embed=msg.embeds[0])


# ----------------------------
# LİSTE SIFIRLA
# ----------------------------
@bot.command()
async def listesifirla(ctx):
    global LIST_CHANNEL_ID, LIST_MESSAGE_ID

    if not is_admin(ctx.author):
        return await ctx.reply("❌ Bu komut sadece adminlere özeldir.")

    LIST_CHANNEL_ID = None
    LIST_MESSAGE_ID = None

    await ctx.reply("🗑️ Liste sıfırlandı!")


# ----------------------------
# KENDİ MENTION SİLME
# ----------------------------
@bot.command()
async def benisil(ctx):
    global LIST_CHANNEL_ID, LIST_MESSAGE_ID

    if LIST_MESSAGE_ID is None:
        return await ctx.reply("❌ Liste yok.")

    channel = bot.get_channel(LIST_CHANNEL_ID)
    msg = await channel.fetch_message(LIST_MESSAGE_ID)

    lines = msg.embeds[0].description.split("\n")
    user_tag = f"<@{ctx.author.id}>"

    new_lines = [re.sub(r"–\s*<@!?\d+>", "", line) if user_tag in line else line for line in lines]

    new_text = "\n".join(new_lines)

    embed = discord.Embed(
        title="📋 Liste",
        description=new_text,
        color=0x3498db
    )

    await msg.edit(embed=embed)
    await ctx.reply("🧹 İsmin listeden silindi!")


# ----------------------------
# ADMIN EKLE
# ----------------------------
@bot.command()
async def adminekle(ctx, rol: discord.Role):
    global EXTRA_ADMIN_ROLE_ID

    if MAIN_ADMIN_ROLE_ID not in [r.id for r in ctx.author.roles]:
        return await ctx.reply("❌ Bu komut sadece ana adminindir.")

    EXTRA_ADMIN_ROLE_ID = rol.id
    await ctx.reply(f"🔐 `{rol.name}` artık admin rolü olarak ayarlandı!")


# ----------------------------
# SAYI YAZILINCA OTOMATİK İŞLEME
# ----------------------------
@bot.event
async def on_message(message):
    global LIST_CHANNEL_ID, LIST_MESSAGE_ID

    if message.author.bot:
        return

    await bot.process_commands(message)

    if not message.content.isdigit():
        return

    if LIST_MESSAGE_ID is None:
        return

    num = int(message.content)

    channel = bot.get_channel(LIST_CHANNEL_ID)
    msg = await channel.fetch_message(LIST_MESSAGE_ID)

    lines = msg.embeds[0].description.split("\n")

    # ilgili satırı bul
    idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith(f"{num})"):
            idx = i
            break

    if idx is None:
        return

    # eski mention sil
    lines[idx] = re.sub(r"–\s*<@!?\d+>", "", lines[idx]).strip()

    # yeni mention ekle
    lines[idx] = f"{lines[idx]} – <@{message.author.id}>"

    new_text = "\n".join(lines)

    embed = discord.Embed(
        title="📋 Liste",
        description=new_text,
        color=0x3498db
    )

    await msg.edit(embed=embed)


# ----------------------------
# BOTU BAŞLAT
# ----------------------------
bot.run(TOKEN)
