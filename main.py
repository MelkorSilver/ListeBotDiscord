import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import re

# ENV yükle
load_dotenv()
TOKEN = os.getenv("TOKEN")

# Railway → Variables → MAIN_ADMIN_ROLE_ID
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
# Admin kontrol fonksiyonu
# ----------------------------
def is_admin(user):
    global MAIN_ADMIN_ROLE_ID, EXTRA_ADMIN_ROLE_ID

    if not hasattr(user, "roles"):
        return False

    role_ids = [r.id for r in user.roles]

    # Ana admin rolü
    if MAIN_ADMIN_ROLE_ID in role_ids:
        return True

    # Ek admin rolü
    if EXTRA_ADMIN_ROLE_ID and EXTRA_ADMIN_ROLE_ID in role_ids:
        return True

    return False


@bot.event
async def on_ready():
    print(f"Bot giriş yaptı: {bot.user}")


# ----------------------------
# YARDIM
# ----------------------------
@bot.command()
async def yardım(ctx):
    embed = discord.Embed(
        title="📌 Komutlar",
        description="Aşağıdaki komutları kullanabilirsiniz:",
        color=0x4CAF50
    )
    embed.add_field(name="!listeolustur metin", value="Yeni liste oluşturur.", inline=False)
    embed.add_field(name="!listegoster", value="Mevcut listeyi gösterir.", inline=False)
    embed.add_field(name="!listesifirla", value="Listeyi sıfırlar (Admin).", inline=False)
    embed.add_field(name="!benisil", value="Kendi ismini listeden siler.", inline=False)
    embed.add_field(name="!adminekle @rol", value="Ek admin tanımlar (Ana admin).", inline=False)
    embed.add_field(name="Sayı yaz", value="Sayı yazınca ismini ilgili satıra ekler.", inline=False)

    await ctx.send(embed=embed)


# ----------------------------
# LİSTE OLUŞTUR
# ----------------------------
@bot.command()
async def listeolustur(ctx, *, liste):
    """
    Metinden liste oluşturur, thread açar, komut mesajını siler.
    Örnek:
    !listeolustur
    1) Tank
    2) Healer
    3) DPS
    """
    global LIST_CHANNEL_ID, LIST_MESSAGE_ID

    lines = liste.split("\n")

    # Alt talimat bloğu
    info_block = (
        "──────────────────────────────\n"
        "🔢 Sıraya girmek için sayı yazın\n"
        "🧽 Kendini silmek için: !benisil\n"
        "📘 Tüm komutlar: !yardım\n"
        "──────────────────────────────"
    )

    final_text = "\n".join(lines) + "\n\n" + info_block

    embed = discord.Embed(
        title="📋 Liste",
        description=final_text,
        color=0x3498db
    )

    # Liste mesajını gönder
    msg = await ctx.send(embed=embed)

    LIST_CHANNEL_ID = msg.channel.id
    LIST_MESSAGE_ID = msg.id

    # Otomatik thread aç
    try:
        thread_name = f"Liste – {ctx.author.display_name}"
        await msg.create_thread(
            name=thread_name,
            auto_archive_duration=1440  # 24 saat
        )
    except Exception as e:
        print(f"Thread oluşturulamadı: {e}")

    # Kullanıcıya bilgi mesajı
    await ctx.reply("✅ Liste oluşturuldu! Kullanıcılar sayı yazabilir.", mention_author=False)

    # Komut mesajını sil
    try:
        await ctx.message.delete()
    except Exception as e:
        print(f"Komut mesajı silinemedi: {e}")


# ----------------------------
# LİSTE GÖSTER
# ----------------------------
@bot.command()
async def listegoster(ctx):
    if LIST_MESSAGE_ID is None:
        return await ctx.reply("❌ Henüz liste oluşturulmamış.")

    channel = bot.get_channel(LIST_CHANNEL_ID)
    if not channel:
        return await ctx.reply("❌ Liste kanalı bulunamadı.")

    try:
        msg = await channel.fetch_message(LIST_MESSAGE_ID)
    except discord.NotFound:
        return await ctx.reply("❌ Liste mesajı bulunamadı.")
    except Exception as e:
        print(e)
        return await ctx.reply("❌ Liste mesajına erişilemiyor.")

    await ctx.send(embed=msg.embeds[0])


# ----------------------------
# LİSTE SIFIRLA
# ----------------------------
@bot.command()
async def listesifirla(ctx):
    global LIST_CHANNEL_ID, LIST_MESSAGE_ID

    if not is_admin(ctx.author):
        return await ctx.reply("❌ Bu komutu sadece adminler kullanabilir.")

    LIST_CHANNEL_ID = None
    LIST_MESSAGE_ID = None

    await ctx.reply("🗑️ Liste sıfırlandı!")


# ----------------------------
# KENDİ MENTION SİLME
# ----------------------------
@bot.command()
async def benisil(ctx):
    global LIST_MESSAGE_ID, LIST_CHANNEL_ID

    if LIST_MESSAGE_ID is None:
        return await ctx.reply("❌ Liste yok.")

    channel = bot.get_channel(LIST_CHANNEL_ID)
    if not channel:
        return await ctx.reply("❌ Liste kanalı bulunamadı.")

    try:
        msg = await channel.fetch_message(LIST_MESSAGE_ID)
    except discord.NotFound:
        return await ctx.reply("❌ Liste mesajı bulunamadı.")
    except Exception as e:
        print(e)
        return await ctx.reply("❌ Liste mesajına erişilemiyor.")

    lines = msg.embeds[0].description.split("\n")
    user_tag = f"<@{ctx.author.id}>"

    new_lines = [
        re.sub(r"–\s*<@!?\d+>", "", line) if user_tag in line else line
        for line in lines
    ]

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

    # Sadece MAIN_ADMIN_ROLE_ID rolüne sahip olan kullanabilsin
    if MAIN_ADMIN_ROLE_ID not in [r.id for r in ctx.author.roles]:
        return await ctx.reply("❌ Bu komutu sadece ana admin kullanabilir.")

    EXTRA_ADMIN_ROLE_ID = rol.id
    await ctx.reply(f"🔐 `{rol.name}` artık admin rolü olarak ayarlandı!")


# ----------------------------
# SAYI YAZAN OTOMATİK İŞLEM
# ----------------------------
@bot.event
async def on_message(message):
    global LIST_CHANNEL_ID, LIST_MESSAGE_ID

    if message.author.bot:
        return

    # Önce komutları çalıştır
    await bot.process_commands(message)

    # Sonrası sadece düz sayı mesajları için
    if LIST_MESSAGE_ID is None:
        return

    if not message.content.isdigit():
        return

    num = int(message.content)

    channel = bot.get_channel(LIST_CHANNEL_ID)
    if not channel:
        return

    try:
        msg = await channel.fetch_message(LIST_MESSAGE_ID)
    except Exception:
        return

    if not msg.embeds:
        return

    lines = msg.embeds[0].description.split("\n")

    # Talimat bloğunu ayır
    list_lines = []
    info_lines = []
    info_start = False

    for line in lines:
        if line.startswith("──────────────────────────────"):
            info_start = True

        if info_start:
            info_lines.append(line)
        else:
            list_lines.append(line)

    # Kullanıcının zaten listede bir yeri var mı?
    user_tag = f"<@{message.author.id}>"
    for line in list_lines:
        if user_tag in line:
            await message.reply("❌ Zaten listede bir sıran var. Önce `!benisil` yazıp temizle, sonra yeni numara al.")
            return

    # İlgili satırı bul (1, 1), 1-, 1. hepsi çalışsın)
    idx = None
    pattern = re.compile(rf"^{num}\b")  # satır başı: "1", "1)", "1-", "1." vb

    for i, line in enumerate(list_lines):
        if pattern.match(line.strip()):
            idx = i
            break

    if idx is None:
        return

    # SLOT DOLU MU? (herhangi bir mention varsa)
    if re.search(r"<@!?\d+>", list_lines[idx]):
        await message.reply("❌ Bu numara zaten dolu, başka bir numara seç.")
        return

    # Güvenlik amaçlı, eski mention kalıntısı varsa temizle
    list_lines[idx] = re.sub(r"–\s*<@!?\d+>", "", list_lines[idx]).strip()
    list_lines[idx] = f"{list_lines[idx]} – <@{message.author.id}>"

    # Embed yeniden oluştur
    final_text = "\n".join(list_lines) + "\n" + "\n".join(info_lines)

    new_embed = discord.Embed(
        title="📋 Liste",
        description=final_text,
        color=0x3498db
    )

    await msg.edit(embed=new_embed)


# ----------------------------
# BOTU BAŞLAT
# ----------------------------
bot.run(TOKEN)
