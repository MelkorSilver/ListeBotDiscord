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
LIST_TEXT_LINES = []  # liste satırları

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


# -------------------------
# Admin kontrol
# -------------------------
def is_admin(user):
    role_ids = [r.id for r in getattr(user, "roles", [])]
    return (
        MAIN_ADMIN_ROLE_ID in role_ids or
        (EXTRA_ADMIN_ROLE_ID and EXTRA_ADMIN_ROLE_ID in role_ids)
    )


# -------------------------
# Embed oluşturucu
# -------------------------
def build_embed():
    list_part = "\n".join(LIST_TEXT_LINES)

    footer = (
        "──────────────────────────────\n"
        "🔢 Sıraya girmek için sayı yazın\n"
        "🧽 Kendini silmek için: !benisil\n"
        "📘 Tüm komutlar: !yardım\n"
        "──────────────────────────────"
    )

    return discord.Embed(
        title="📋 Liste",
        description=f"{list_part}\n\n{footer}",
        color=0x3498db
    )


@bot.event
async def on_ready():
    print(f"Bot giriş yaptı: {bot.user}")


# -------------------------
# !listeolustur
# -------------------------
@bot.command()
async def listeolustur(ctx, *, liste):
    """
    Kullanıcı şu şekilde tek mesaj atar:
    !listeolustur
    1) Tank
    2) Healer
    3) DPS
    """
    global LIST_CHANNEL_ID, LIST_MESSAGE_ID, LIST_TEXT_LINES

    # Komut mesajından sadece liste kısmını çek
    lines = liste.split("\n")
    LIST_TEXT_LINES = []

    for line in lines:
        line = line.strip()
        if ")" in line:
            LIST_TEXT_LINES.append(line)

    embed = build_embed()
    msg = await ctx.send(embed=embed)

    LIST_CHANNEL_ID = msg.channel.id
    LIST_MESSAGE_ID = msg.id

    await ctx.reply("✅ Liste oluşturuldu!")


# -------------------------
# listegoster
# -------------------------
@bot.command()
async def listegoster(ctx):
    if LIST_MESSAGE_ID is None:
        return await ctx.reply("❌ Liste yok.")

    channel = bot.get_channel(LIST_CHANNEL_ID)
    msg = await channel.fetch_message(LIST_MESSAGE_ID)

    await ctx.send(embed=msg.embeds[0])


# -------------------------
# listesifirla
# -------------------------
@bot.command()
async def listesifirla(ctx):
    global LIST_CHANNEL_ID, LIST_MESSAGE_ID, LIST_TEXT_LINES

    if not is_admin(ctx.author):
        return await ctx.reply("❌ Bu komut sadece admin içindir.")

    LIST_CHANNEL_ID = None
    LIST_MESSAGE_ID = None
    LIST_TEXT_LINES = []

    await ctx.reply("🗑️ Liste sıfırlandı!")


# -------------------------
# benisil
# -------------------------
@bot.command()
async def benisil(ctx):
    global LIST_TEXT_LINES

    if LIST_MESSAGE_ID is None:
        return await ctx.reply("❌ Liste yok.")

    user_tag = f"<@{ctx.author.id}>"
    new_lines = []

    for line in LIST_TEXT_LINES:
        if user_tag in line:
            line = re.sub(r"–\s*<@!?\d+>", "", line).strip()
        new_lines.append(line)

    LIST_TEXT_LINES = new_lines

    channel = bot.get_channel(LIST_CHANNEL_ID)
    msg = await channel.fetch_message(LIST_MESSAGE_ID)
    await msg.edit(embed=build_embed())

    await ctx.reply("🧹 İsmin listeden silindi!")


# -------------------------
# adminekle
# -------------------------
@bot.command()
async def adminekle(ctx, rol: discord.Role):
    global EXTRA_ADMIN_ROLE_ID

    if MAIN_ADMIN_ROLE_ID not in [r.id for r in ctx.author.roles]:
        return await ctx.reply("❌ Bu komut ana admin içindir.")

    EXTRA_ADMIN_ROLE_ID = rol.id
    await ctx.reply(f"🔐 `{rol.name}` artık admin rolüdür.")


# -------------------------
# sayı yazınca işlem
# -------------------------
@bot.event
async def on_message(message):
    global LIST_TEXT_LINES, LIST_MESSAGE_ID, LIST_CHANNEL_ID

    if message.author.bot:
        return

    await bot.process_commands(message)

    if LIST_MESSAGE_ID is None:
        return

    if not message.content.isdigit():
        return

    num = int(message.content)

    for i, line in enumerate(LIST_TEXT_LINES):
        if line.startswith(f"{num})"):

            # mention sil
            LIST_TEXT_LINES[i] = re.sub(r"–\s*<@!?\d+>", "", LIST_TEXT_LINES[i]).strip()
            # yeni mention
            LIST_TEXT_LINES[i] += f" – <@{message.author.id}>"

            channel = bot.get_channel(LIST_CHANNEL_ID)
            msg = await channel.fetch_message(LIST_MESSAGE_ID)
            await msg.edit(embed=build_embed())
            break


bot.run(TOKEN)
