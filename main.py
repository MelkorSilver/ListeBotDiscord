import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import re

# ENV yükle
load_dotenv()
TOKEN = os.getenv("TOKEN")

MAIN_ADMIN_ROLE_ID = int(os.getenv("MAIN_ADMIN_ROLE_ID", "0"))
EXTRA_ADMIN_ROLE_ID = None

LIST_CHANNEL_ID = None
LIST_MESSAGE_ID = None
LIST_ENTRIES = {}   # sadece gerçek liste satırları

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# --------------------------------------------------------
# ADMIN KONTROL
# --------------------------------------------------------
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


# --------------------------------------------------------
# Embed oluşturucu
# --------------------------------------------------------
def build_embed():
    embed = discord.Embed(
        title="📋 Liste",
        description="──────────────────────────────\n"
                    "🔢 Sıraya girmek için sayı yazın\n"
                    "🧽 Kendini silmek için: !benisil\n"
                    "📘 Tüm komutlar: !yardım\n"
                    "──────────────────────────────",
        color=0x3498db
    )

    for num in sorted(LIST_ENTRIES.keys()):
        embed.add_field(
            name=f"{num})",
            value=LIST_ENTRIES[num],
            inline=False
        )

    return embed


# --------------------------------------------------------
# YARDIM KOMUTU
# --------------------------------------------------------
@bot.command()
async def yardım(ctx):
    embed = discord.Embed(
        title="📌 Komut Listesi",
        description="Aşağıdaki komutları kullanabilirsiniz:",
        color=0x4CAF50
    )

    embed.add_field(name="!listeolustur", value="Yeni liste oluşturur.", inline=False)
    embed.add_field(name="!listegoster", value="Listeyi gösterir.", inline=False)
    embed.add_field(name="!listesifirla", value="Listeyi sıfırlar. (Admin)", inline=False)
    embed.add_field(name="!benisil", value="Kendi ismini siler.", inline=False)
    embed.add_field(name="!adminekle @rol", value="Admin rolü ekler.", inline=False)
    embed.add_field(name="Sayı yaz", value="Belirli satıra adını ekler.", inline=False)

    await ctx.send(embed=embed)


# --------------------------------------------------------
# LİSTE OLUŞTUR
# --------------------------------------------------------
@bot.command()
async def listeolustur(ctx, *, liste):
    global LIST_CHANNEL_ID, LIST_MESSAGE_ID, LIST_ENTRIES

    LIST_ENTRIES = {}

    for line in liste.split("\n"):
        line = line.strip()
        if ")" in line:
            num = int(line.split(")")[0])
            LIST_ENTRIES[num] = line

    embed = build_embed()
    msg = await ctx.send(embed=embed)

    LIST_CHANNEL_ID = msg.channel.id
    LIST_MESSAGE_ID = msg.id

    await ctx.reply("✅ Liste oluşturuldu!")


# --------------------------------------------------------
# LİSTE GÖSTER
# --------------------------------------------------------
@bot.command()
async def listegoster(ctx):
    if LIST_MESSAGE_ID is None:
        return await ctx.reply("❌ Liste yok.")

    channel = bot.get_channel(LIST_CHANNEL_ID)
    msg = await channel.fetch_message(LIST_MESSAGE_ID)

    await ctx.send(embed=msg.embeds[0])


# --------------------------------------------------------
# LİSTE SIFIRLA
# --------------------------------------------------------
@bot.command()
async def listesifirla(ctx):
    global LIST_CHANNEL_ID, LIST_MESSAGE_ID, LIST_ENTRIES

    if not is_admin(ctx.author):
        return await ctx.reply("❌ Admin değilsin.")

    LIST_CHANNEL_ID = None
    LIST_MESSAGE_ID = None
    LIST_ENTRIES = {}

    await ctx.reply("🗑️ Liste sıfırlandı!")


# --------------------------------------------------------
# KENDİ MENTION SİL
# --------------------------------------------------------
@bot.command()
async def benisil(ctx):
    global LIST_ENTRIES, LIST_MESSAGE_ID

    if LIST_MESSAGE_ID is None:
        return await ctx.reply("❌ Liste yok.")

    user_tag = f"<@{ctx.author.id}>"

    for num in LIST_ENTRIES:
        LIST_ENTRIES[num] = re.sub(r"–\s*<@!?\d+>", "", LIST_ENTRIES[num]).strip()

    embed = build_embed()

    channel = bot.get_channel(LIST_CHANNEL_ID)
    msg = await channel.fetch_message(LIST_MESSAGE_ID)
    await msg.edit(embed=embed)

    await ctx.reply("🧹 İsmin silindi!")


# --------------------------------------------------------
# ADMIN EKLE
# --------------------------------------------------------
@bot.command()
async def adminekle(ctx, rol: discord.Role):
    global EXTRA_ADMIN_ROLE_ID

    if MAIN_ADMIN_ROLE_ID not in [r.id for r in ctx.author.roles]:
        return await ctx.reply("❌ Bu komut ana admin içindir.")

    EXTRA_ADMIN_ROLE_ID = rol.id
    await ctx.reply(f"🔐 `{rol.name}` artık admin!")


# --------------------------------------------------------
# SAYI YAZMA İŞLEME
# --------------------------------------------------------
@bot.event
async def on_message(message):
    global LIST_ENTRIES, LIST_MESSAGE_ID

    if message.author.bot:
        return

    await bot.process_commands(message)

    if not message.content.isdigit():
        return

    if LIST_MESSAGE_ID is None:
        return

    num = int(message.content)

    if num not in LIST_ENTRIES:
        return

    LIST_ENTRIES[num] = re.sub(r"–\s*<@!?\d+>", "", LIST_ENTRIES[num]).strip()
    LIST_ENTRIES[num] = f"{LIST_ENTRIES[num]} – <@{message.author.id}>"

    embed = build_embed()

    channel = bot.get_channel(LIST_CHANNEL_ID)
    msg = await channel.fetch_message(LIST_MESSAGE_ID)
    await msg.edit(embed=embed)


bot.run(TOKEN)
