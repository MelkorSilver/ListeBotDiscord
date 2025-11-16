import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import re

# ENV yükle
load_dotenv()
TOKEN = os.getenv("TOKEN")

# Ek admin rol ID'si (!adminekle ile ayarlanacak)
EXTRA_ADMIN_ROLE_ID = None

# Aktif liste mesajı
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
def is_admin(member: discord.Member) -> bool:
    global EXTRA_ADMIN_ROLE_ID

    if not isinstance(member, discord.Member):
        return False

    # Sunucuda "Yönetici" izni varsa admin kabul et
    if member.guild_permissions.administrator:
        return True

    # Ek admin rolü tanımlıysa ve kullanıcıda varsa
    if EXTRA_ADMIN_ROLE_ID and any(r.id == EXTRA_ADMIN_ROLE_ID for r in member.roles):
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
    embed.add_field(name="!listegoster", value="Mevcut listeyi tekrar gönderir.", inline=False)
    embed.add_field(name="!listesifirla", value="Aktif listeyi sıfırlar (Admin).", inline=False)
    embed.add_field(name="!benisil", value="Kendi ismini listeden siler.", inline=False)
    embed.add_field(name="!adminekle @rol", value="Ek admin rolü tanımlar (Sunucu yöneticisi).", inline=False)
    embed.add_field(name="Sayı yaz", value="Sayı yazınca ismini ilgili satıra ekler.", inline=False)

    await ctx.send(embed=embed)


# ----------------------------
# LİSTE OLUŞTUR
# ----------------------------
@bot.command()
async def listeolustur(ctx, *, liste):
    """Metinden liste oluşturur, komut mesajını siler, thread açar."""
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

    # Sadece sunucu yöneticisi ek admin rolü atayabilsin
    if not ctx.author.guild_permissions.administrator:
        return await ctx.reply("❌ Bu komutu sadece sunucu yöneticileri kullanabilir.")

    EXTRA_ADMIN_ROLE_ID = rol.id
    await ctx.reply(f"🔐 `{rol.name}` artık ek admin rolü olarak ayarlandı!")


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

    # İlgili satırı bul (1, 1), 1-, 1. vs hepsi çalışsın)
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

    # Eski mention kalıntısı varsa temizle ve yeni mention ekle
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
