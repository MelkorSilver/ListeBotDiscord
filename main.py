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
