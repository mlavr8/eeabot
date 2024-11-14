import os
import io
import json
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

# Предварительная загрузка фонового изображения и шрифта
background_image = Image.open("welcomeeea.jpg")
font = ImageFont.truetype("welcomefont.ttf", 90)

# Определение уровня для каждой роли
LEVEL_ROLES = {
    5: 123456789012345678,  # ID роли для уровня 5
    10: 234567890123456789,  # ID роли для уровня 10
    15: 345678901234567890,  # ID роли для уровня 15
}

# Система уровней
def calculate_level(xp):
    return int((xp / 100) ** 0.5)  # Пример: уровень увеличивается каждые 100 XP

# Загрузка данных из JSON-файла
def load_data():
    try:
        with open("levels.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Сохранение данных в JSON-файл
def save_data(data):
    with open("levels.json", "w") as f:
        json.dump(data, f, indent=4)

# Загрузка данных пользователей
user_data = load_data()

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

@bot.event
async def on_message(message):
    """Отслеживает сообщения для начисления XP и проверки уровня"""
    if message.author.bot:
        return

    user_id = str(message.author.id)
    user_data.setdefault(user_id, {"xp": 0, "level": 0})

    # Начисляем XP
    user_data[user_id]["xp"] += 10  # Пример: 10 XP за сообщение
    new_level = calculate_level(user_data[user_id]["xp"])

    # Проверяем, повысился ли уровень
    if new_level > user_data[user_id]["level"]:
        user_data[user_id]["level"] = new_level
        await message.channel.send(f"{message.author.mention} достиг уровня {new_level}!")

        # Проверяем, нужно ли выдать новую роль
        if new_level in LEVEL_ROLES:
            role = message.guild.get_role(LEVEL_ROLES[new_level])
            if role:
                await message.author.add_roles(role)
                await message.channel.send(f"{message.author.mention} получил роль {role.name} за достижение уровня {new_level}!")

    # Сохраняем данные
    save_data(user_data)

    await bot.process_commands(message)

@bot.command()
async def rank(ctx, member: discord.Member = None):
    """Показывает уровень и XP пользователя"""
    member = member or ctx.author
    user_id = str(member.id)
    xp = user_data.get(user_id, {}).get("xp", 0)
    level = user_data.get(user_id, {}).get("level", 0)
    await ctx.send(f"{member.mention} - Уровень: {level}, XP: {xp}")

bot.run(BOT_TOKEN)
