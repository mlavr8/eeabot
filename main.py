import os
import io
import discord
import requests
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont, ImageOps
import aiohttp
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents)

# Предварительная загрузка фонового изображения и шрифта для оптимизации
background_image = Image.open("welcomeeea.jpg")
font = ImageFont.truetype("welcomefont.ttf", 90)

@bot.event
async def on_ready():
    print("BOT ONLINE")

async def fetch_avatar(url):
    """Асинхронная функция для загрузки аватарки"""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.read()

def process_avatar(avatar_bytes):
    """Функция обработки аватарки пользователя для добавления маски"""
    avatar_image = Image.open(io.BytesIO(avatar_bytes))
    avatar_image = avatar_image.resize((550, 550))
    mask = Image.new('L', avatar_image.size, 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.ellipse((0, 0, avatar_image.width, avatar_image.height), fill=255)
    return ImageOps.fit(avatar_image, mask.size, centering=(0.5, 0.5)).convert("RGBA"), mask

@bot.event
async def on_member_join(member):
    """Создает и отправляет приветственное изображение при присоединении нового участника"""
    avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
    avatar_bytes = await fetch_avatar(avatar_url)
    avatar_image, mask = process_avatar(avatar_bytes)
    
    background = background_image.copy()
    background.paste(avatar_image, (207, 196), mask=mask)
    draw = ImageDraw.Draw(background)
    draw.text((490, 850), f"{member.name}", font=font, fill=(255, 255, 255), anchor="mm")
    
    # Сохраняем и отправляем изображение
    background.save("welcome_image.png")
    channel = discord.utils.get(member.guild.channels, name="🏠・welcome")
    if channel:
        await channel.send(f"Hey {member.mention}, welcome to **Eastern European Association**!", file=discord.File("welcome_image.png"))

@bot.event
async def on_member_remove(member):
    """Отправляет сообщение о выходе участника с сервера"""
    channel = discord.utils.get(member.guild.channels, name="🏠・welcome")
    if channel:
        await channel.send(f"Пользователь **{member.name}** покинул сервер")

# Установите ID ролей, которым разрешен доступ к команде
adm = [870045414856998912, 1158362465164328962, 1258722224890839090]
ALLOWED_ROLES = [1158361900179017728, 870344875009257534]

@bot.slash_command(name='giverole', description='Выдача конкретной роли нескольким пользователям.')
@commands.has_any_role(*ALLOWED_ROLES, *adm)
async def giverole(ctx, role: discord.Role, member1: discord.Member, member2: discord.Member = None):
    """Выдает указанную роль указанным пользователям"""
    try:
        await member1.add_roles(role)
        if member2:
            await member2.add_roles(role)
        await ctx.send(f"Роль '{role.mention}' была выдана пользователям: {member1.mention}" +
                       (f", {member2.mention}" if member2 else "") + ".")
    except discord.Forbidden:
        await ctx.send(f"У меня недостаточно прав для выдачи роли '{role.name}'.")

bot.run(BOT_TOKEN)
