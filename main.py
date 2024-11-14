import os
import io
import json
import discord
import requests
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont, ImageOps  # welcome

from dotenv import load_dotenv

load_dotenv()
# Получаем переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents)

@bot.event
async def on_ready():
    print("BOT ONLINE")


background_image_path = "welcomeeea.jpg"  # welcome

@bot.event
async def on_member_join(member):
    # Получаем аватарку участника
    avatar_url = member.avatar.url if member.avatar else member.default_avatar.url # Уменьшаем размер аватарки
    avatar_bytes = requests.get(avatar_url).content  # Загружаем аватарку

    # Загружаем картинку для фона
    background = Image.open(background_image_path)

    # Создаем объект для рисования на картинке
    draw = ImageDraw.Draw(background)

    # Загружаем шрифт (можно использовать любой шрифт)
    font = ImageFont.truetype("welcomefont.ttf", 90)

    # Рисуем аватарку на картинке
    avatar_image = Image.open(io.BytesIO(avatar_bytes))
    avatar_image = avatar_image.resize((550, 550))  # Уменьшаем размер аватарки
    mask = Image.new('L', avatar_image.size, 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.ellipse((0, 0, avatar_image.width, avatar_image.height), fill=255)
    avatar_image = ImageOps.fit(avatar_image, mask.size, centering=(0.5, 0.5))
    background.paste(avatar_image, (207, 196), mask=mask)  # Позиция для аватарки

    # Рисуем ник на картинке
    draw.text((490, 850), f"{member.name}", font=font, fill=(255, 255, 255), anchor="mm")

    # Сохраняем полученную картинку
    background.save("welcome_image.png")

    # Отправляем сообщение с картинкой
    channel = discord.utils.get(member.guild.channels, name="🏠・welcome")
    await channel.send(f"Hey {member.mention}, welcome to **Eastern European Association**!", file=discord.File("welcome_image.png"))

@bot.event
async def on_member_remove(member):

    channel = discord.utils.get(member.guild.channels, name="🏠・welcome")
    await channel.send(f"Пользователь **{member.name}** покинул сервер")


# Установите ID ролей, которым разрешен доступ к команде
adm = [870045414856998912, 1158362465164328962, 1258722224890839090]
ALLOWED_ROLES = [1158361900179017728, 870344875009257534] # Замените на реальные ID ролей

@bot.slash_command(name='giverole', description='Выдача конкретной роли нескольким пользователям.')
@commands.has_any_role(*ALLOWED_ROLES, *adm)
async def giverole(ctx, role: discord.Role, member1: discord.Member, member2: discord.Member = None):
    """Выдает указанную роль указанному пользователю."""

    # Проверяем, есть ли у бота права на выдачу роли
    if ctx.guild.me.top_role <= role:
        await ctx.send(f"У меня недостаточно прав для выдачи роли '{role.name}'.")
        return

    await member1.add_roles(role)
    await ctx.send(f"Роль '{role.mention}' была выдана пользователю: {member1.mention}.")

    if member2:
        await member2.add_roles(role)
        await ctx.send(f"Роль '{role.mention}' была выдана следующим пользователям: {member1.mention}, {member2.mention}.")


bot.run(BOT_TOKEN)