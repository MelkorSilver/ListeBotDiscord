import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import re

load_dotenv()

TOKEN = os.getenv("TOKEN")

LIST_CHANNEL_ID = None
LIST_MESSAGE_ID = None

# --------------------
#   ADMIN ROLE SYSTEM
# --------------------
MAIN_ADMIN_ROLE_ID = 264037003258101767  # ← BUNU SANA GÖRE AYARLAYACAĞIM
EXTRA_ADMIN_ROLE_ID = None               # sonradan değiştirilebilir


intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


# ----------------------------
#  Admin kontrol fonksiyonu
# ----------------------------
def is_admin(member):
    """Sabit admin veya ek admin rolüne sahip mi?"""
    role_ids = [role.id for role in member.roles]
    return (
        MAIN_ADMIN_ROLE_ID in role_ids or
        (EXTRA_ADMIN_ROLE_ID in role_ids if EXTRA_ADMIN_ROLE_ID else False)
    )


# ----------------------------
# Embed oluşturucu
# ----------------------------
def make_embed(content: str):
    embed = discord.Embed(
        title="📋 Kayıt Listesi",
        description=content,
        color=discord.Color.blue()
    )
    embed.set_footer(text="Liste otomatik olarak güncellenir.")
    return embed


@bot.event
async def on_ready():
    print(f"Bot giriş yaptı: {bot.user}")


# ----------------------------
# 1) Embed liste oluştur
# ----------------------------
@bot.command()
async def listeolustur(ctx, *, liste):
    global LIST_CHANNEL_ID, LIST_MESSAGE_ID

    embed = make_embed(liste)
    msg = await ctx.send(embed=embed)

    LIST_CHANNEL_ID = msg.channel.id
    LIST_MESSAGE_ID = msg.id

    await ctx.reply("✅ Embed liste oluşturuldu!")


# ----------------------------
# 2) Liste göster
# ----------------------------
@bot.command()
async def listegoster(ctx):
    if LIST_MESSAGE_ID is None:
        return await ctx.reply("❌ Liste yok.")

    channel = bot.get_channel(LIST_CHANNEL_ID)
    msg = await channel.fetch_message(LIST_MESSAGE_ID)

    await ctx.reply(embed=msg.embeds[0])


# ----------------------------
# 3) Liste sıfırla (Sadece admin)
# ----------------------------
@bot.command()
async def listesifirla(ctx):
    if LIST_MESSAGE_ID is None:
        return await ctx.reply("❌ Liste yok.")

    if not is_admin(ctx.author):
        return await ctx.reply("❌ Bu komutu sadece adminler kullanabilir.")

    channel = bot.get_channel(LIST_CHANNEL_ID)
    msg = await channel.fetch_message(LIST_MESSAGE_ID)

    content = msg.embeds[0].description
    lines = [re.sub(r"–\s*<@!?\d+>", "", l).strip() for l in content.split("\n")]

    new_embed = make_embed("\n".join(lines))
    await msg.edit(embed=new_embed)

    await ctx.reply("🧹 Liste sıfırlandı!")


# ----------------------------
# 4) Belirli satır mention sil
# ----------------------------
@bot.command()
async def sil(ctx, sayi: int):
    if LIST_MESSAGE_ID is None:
        return await ctx.reply("❌ Liste yok.")

    channel = bot.get_channel(LIST_CHANNEL_ID)
    msg = await channel.fetch_message(LIST_MESSAGE_ID)

    content = msg.embeds[0].description
    lines = content.split("\n")

    idx = next((i for i, l in enumerate(lines) if l.startswith(f"{sayi})")), None)
    if idx is None:
        return await ctx.reply("❌ Böyle bir satır yok.")

    satir = lines[idx]
    mention = re.search(r"<@!?(\d+)>", satir)

    if mention:
        user_id = int(mention.group(1))
        if ctx.author.id != user_id and not is_admin(ctx.author):
            return await ctx.reply("❌ Bu satırı silme yetkin yok.")

    lines[idx] = re.sub(r"–\s*<@!?\d+>", "", lines[idx]).strip()

    await msg.edit(embed=make_embed("\n".join(lines)))
    await ctx.reply(f"🗑 {sayi}. satırdan mention silindi!")


# ----------------------------
# 5) Kullanıcı kendi adını silsin
# ----------------------------
@bot.command()
async def benisil(ctx):
    if LIST_MESSAGE_ID is None:
        return await ctx.reply("❌ Liste yok.")

    channel = bot.get_channel(LIST_CHANNEL_ID)
    msg = await channel.fetch_message(LIST_MESSAGE_ID)

    content = msg.embeds[0].description
    lines = content.split("\n")

    edited = False
    for i, l in enumerate(lines):
        if f"<@{ctx.author.id}>" in l or f"<@!{ctx.author.id}>" in l:
            lines[i] = re.sub(r"–\s*<@!?\d+>", "", l).strip()
            edited = True

    if not edited:
        return await ctx.reply("ℹ Listede adın yok.")

    await msg.edit(embed=make_embed("\n".join(lines)))
    await ctx.reply("🧹 Adın listeden silindi!")


# ----------------------------
# 6) EKSTRA admin rolü ekle
# ----------------------------
@bot.command()
async def adminekle(ctx, rol: discord.Role):
    global EXTRA_ADMIN_ROLE_ID

    # Yalnızca adminler bu komutu kullanabilir
    if not is_admin(ctx.author):
        return await ctx.reply("❌ Bu komutu sadece adminler kullanabilir.")

    EXTRA_ADMIN_ROLE_ID = rol.id
    await ctx.reply(f"🔐 Ek admin rolü ayarlandı: **{rol.name}**")


# ----------------------------
# 7) Yardım menüsü
# ----------------------------
@bot.command()
async def yardim(ctx):
    text = """
🟦 **Embed Liste Botu Komutları**

📌 **!listeolustur <liste>**  
Embed liste oluşturur.

📌 **!listegoster**  
Aktif listeyi gösterir.

📌 **!listesifirla**  
Listeyi sıfırlar (admin).

📌 **!sil <sayi>**  
Satırdaki mention’u siler.

📌 **!benisil**  
Kendi adını listeden kaldırır.

📌 **!adminekle @rol**  
Ek admin rolü ayarlar.  
Sabit admin rolü değiştirilemez.

📌 **(komut değil)**  
Kullanıcı sayı yazınca ilgili satıra otomatik eklenir.
"""
    await ctx.reply(text)


# ----------------------------
# 8) Sayı yazınca otomatik ekleme
# ----------------------------
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    await bot.process_commands(message)

    if LIST_MESSAGE_ID is None:
        return

    if not message.content.isdigit():
        return

    num = int(message.content)

    channel = bot.get_channel(LIST_CHANNEL_ID)
    msg = await channel.fetch_message(LIST_MESSAGE_ID)

    content = msg.embeds[0].description
    lines = content.split("\n")

    idx = next((i for i, l in enumerate(lines) if l.startswith(f"{num})")), None)
    if idx is None:
        return

    lines[idx] = re.sub(r"–\s*<@!?\d+>", "", lines[idx]).strip()
    lines[idx] = f"{lines[idx]} – <@{message.author.id}>"

    await msg.edit(embed=make_embed("\n".join(lines)))


bot.run(TOKEN)

