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
        return await ctx.reply("❌ Bu komut sadece admin rolüne sahip olanlar tarafından kullanılabilir.")

    channel = bot.get_channel(LIST_CHANNEL_ID)
    msg = await channel.fetch_message(LIST_MESSAGE_ID)

    # tüm mentionlar kaldırılır
    lines = [re.sub(r"–\s*<@!?\d+>", "", l).strip() for l in msg.content.split("\n")]

    await msg.edit(content="\n".join(lines))
    await ctx.reply("🧹 Liste tamamen sıfırlandı.")


# -----------------------------
# 4) Belirli Satırı Sil (!sil <sayi>)
# -----------------------------
@bot.command()
async def sil(ctx, sayi: int):
    """Belirli satırdaki mention'u siler."""
    global LIST_CHANNEL_ID, LIST_MESSAGE_ID

    if LIST_MESSAGE_ID is None:
        return await ctx.reply("❌ Önce liste oluşturmalısın.")

    channel = bot.get_channel(LIST_CHANNEL_ID)
    msg = await channel.fetch_message(LIST_MESSAGE_ID)

    lines = msg.content.split("\n")

    idx = next((i for i, l in enumerate(lines) if l.strip().startswith(f"{sayi})")), None)
    if idx is None:
        return await ctx.reply("❌ Böyle bir satır yok.")

    # admin değilse → kendi mention'unu silebilir
    satir = lines[idx]
    mention = re.search(r"<@!?(\d+)>", satir)

    if mention:
        user_id = int(mention.group(1))
        if ctx.author.id != user_id and not is_admin(ctx.author):
            return await ctx.reply("❌ Bu kişiyi silmeye yetkin yok.")

    lines[idx] = re.sub(r"–\s*<@!?\d+>", "", lines[idx]).strip()

    await msg.edit(content="\n".join(lines))
    await ctx.reply(f"🗑 {sayi}. satır temizlendi.")


# -----------------------------
# 5) Kendi Mention’unu Sil (!benisil)
# -----------------------------
@bot.command()
async def benisil(ctx):
    """Kullanıcının listeden kendi adını siler."""
    global LIST_MESSAGE_ID, LIST_CHANNEL_ID

    if LIST_MESSAGE_ID is None:
        return await ctx.reply("❌ Liste bulunamadı.")

    channel = bot.get_channel(LIST_CHANNEL_ID)
    msg = await channel.fetch_message(LIST_MESSAGE_ID)

    lines = msg.content.split("\n")
    edited = False

    for i, satir in enumerate(lines):
        if f"<@{ctx.author.id}>" in satir or f"<@!{ctx.author.id}>" in satir:
            lines[i] = re.sub(r"–\s*<@!?\d+>", "", satir).strip()
            edited = True

    if not edited:
        return await ctx.reply("ℹ Listede adın yok.")

    await msg.edit(content="\n".join(lines))
    await ctx.reply("🧹 Adın listeden silindi.")


# -----------------------------
# 6) Admin Rolü Ekle (!adminekle @rol)
# -----------------------------
@bot.command()
async def adminekle(ctx, rol: discord.Role):
    """Admin rolü tanımlar."""
    global ADMIN_ROLE_ID

    if not ctx.author.guild_permissions.administrator:
        return await ctx.reply("❌ Bu komutu yalnızca yöneticiler kullanabilir.")

    ADMIN_ROLE_ID = rol.id
    await ctx.reply(f"🔐 Admin rolü ayarlandı: **{rol.name}**")


# -----------------------------
# 7) Yardım Komutu (!yardim)
# -----------------------------
@bot.command()
async def yardim(ctx):
    """Tüm komutları gösterir."""
    text = """
🟦 **Komut Listesi**

📌 **!listeolustur <liste>**
Liste oluşturur.

📌 **!listegoster**
Mevcut listeyi gönderir.

📌 **!listesifirla**
Listeyi sıfırlar (sadece admin).

📌 **!sil <sayi>**
İlgili satırdaki mention'u siler.

📌 **!benisil**
Kendi adını listeden kaldırır.

📌 **!adminekle @rol**
Admin rolü atar.

📌 **!yardim**
Bu listeyi gösterir.

📌 **(komut değil)**  
Kullanıcı sadece sayı yazınca → o satıra otomatik eklenir.
"""
    await ctx.reply(text)


# -----------------------------
# 8) Sayı yazılınca otomatik mention ekleme
# -----------------------------
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    await bot.process_commands(message)

    global LIST_CHANNEL_ID, LIST_MESSAGE_ID

    if LIST_MESSAGE_ID is None:
        return

    # sayı mı?
    if not message.content.isdigit():
        return

    num = int(message.content)

    channel = bot.get_channel(LIST_CHANNEL_ID)
    msg = await channel.fetch_message(LIST_MESSAGE_ID)

    lines = msg.content.split("\n")

    idx = next((i for i, l in enumerate(lines) if l.strip().startswith(f"{num})")), None)
    if idx is None:
        return

    # eski mention sil
    lines[idx] = re.sub(r"–\s*<@!?\d+>", "", lines[idx]).strip()

    # yeni mention ekle
    lines[idx] = f"{lines[idx]} – <@{message.author.id}>"

    await msg.edit(content="\n".join(lines))


bot.run(TOKEN)
