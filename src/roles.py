import asyncio
import hashlib
import random
from datetime import datetime

import discord

from src.db import create_db_pool


async def add_role(message, role):
    try:
        await message.author.add_roles(discord.utils.get(message.guild.roles, name=role))
    except Exception as e:
        print(f"An error occurred while adding role: {e}")


async def remove_role(message, role):
    try:
        await message.author.remove_roles(discord.utils.get(message.guild.roles, name=role))
    except Exception as e:
        print(f"An error occurred while removing role: {e}")


async def remove_all_roles(user, guild):
    try:
        await user.edit(roles=[guild.default_role])
    except Exception as e:
        print(f"An error occurred while removing all roles: {e}")


async def create_faculty_channel(guild, faculty):
    try:
        category = discord.utils.get(guild.categories, name=faculty)
        if not category:
            category = await guild.create_category(faculty)
        target_role = discord.utils.get(guild.roles, name="Lecturer " + faculty)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            target_role: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        await category.set_permissions(guild.default_role, read_messages=False)
        await category.set_permissions(discord.utils.get(guild.roles, name=faculty), read_messages=True)
        await guild.create_text_channel("General", category=category)
        await guild.create_text_channel("News", category=category)
        news = await guild.create_text_channel(faculty + "-create-news", category=category,
                                               overwrites=overwrites)
        await news.send(
            "If u want to create news, please write it here in this format. Also u can make attachment(optional):\nTitle\nDate(DD:MM:YYYY)\nStart time(hh:mm)\nEnd time(hh:mm)\nPlace\nDescription")
        await news.send(
            "For example:\nMeeting\n21.05.2024\n13:00\n13:30\n231 room\nWe will discuss the future of our group\nU get a candy for participation")
        await guild.create_voice_channel("Meeting", category=category)
    except Exception as e:
        print(f"An error occurred while creating faculty channel '{faculty}': {e}")


async def create_channels(guild, group, faculty):
    try:
        name = group + " " + faculty
        name2 = "Lecturer " + faculty
        target_role = discord.utils.get(guild.roles, name=name)
        target_role2 = discord.utils.get(guild.roles, name=name2)
        target_role3 = discord.utils.get(guild.roles, name="Graduate")
        overwrites1 = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            target_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            target_role2: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            target_role3: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        overwrites2 = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            target_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            target_role2: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            target_role3: discord.PermissionOverwrite(read_messages=False, send_messages=False)
        }
        overwrites3 = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            target_role2: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        for i in range(0, 2):
            if i == 0:
                category = await guild.create_category(group + " " + faculty, overwrites=overwrites1)
                await guild.create_text_channel(group + "-news", category=category)
                news = await guild.create_text_channel(group + "-create-news", category=category,
                                                       overwrites=overwrites3)
                await news.send(
                    "If u want to create news, please write it here in this format. Also u can make attachment(optional):\nTitle\nDate(DD:MM:YYYY)\nStart time(hh:mm)\nEnd time(hh:mm)\nPlace\nDescription")
                await news.send(
                    "For example:\nMeeting\n21.05.2024\n13:00\n13:30\n231 room\nWe will discuss the future of our group\nU get a candy for participation")
                await guild.create_text_channel(group + "-general", category=category)
                await guild.create_voice_channel(group, category=category)
                await guild.create_voice_channel(group + "-defence", category=category, user_limit=2)
            else:
                category = await guild.create_category(group + f"{i} " + faculty, overwrites=overwrites2)
                await guild.create_text_channel(group + f"{i}-news", category=category)
                news = await guild.create_text_channel(group + f"{i}-create-news", category=category,
                                                       overwrites=overwrites3)
                await news.send(
                    "If u want to create news, please write it here in this format. Also u can make attachment(optional):\nTitle\nDate(DD:MM:YYYY)\nStart time(hh:mm)\nEnd time(hh:mm)\nPlace\nDescription")
                await news.send(
                    "For example:\nMeeting\n21.05.2024\n13:00\n13:30\n231 room\nWe will discuss the future of our group\nU get a candy for participation")
                await guild.create_text_channel(group + f"{i}-general", category=category)
                await guild.create_voice_channel(group + f"{i}", category=category)
                await guild.create_voice_channel(group + f"{i}-defence", category=category, user_limit=2)
    except Exception as e:
        print(f"An error occurred while creating group channels for '{faculty}': {e}")


async def create_role(guild, role_name, color=None, hoist=True, pos=-1, perm=None):
    try:
        if pos == -1:
            pos = len(guild.roles)

        if not perm:
            perm = discord.Permissions.none()

        if not color:
            color = discord.Colour.from_rgb(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

        new_role = await guild.create_role(name=role_name, colour=color, hoist=hoist, permissions=perm)
        await new_role.edit(position=pos)
        return new_role
    except Exception as e:
        print(f"An error occurred while creating role '{role_name}': {e}")
        return None


def is_role_exists(guild, role_name):
    if guild:
        role = discord.utils.get(guild.roles, name=role_name)
        if role:
            return True

    return False


def is_category_exists(guild, category_name):
    category = discord.utils.get(guild.categories, name=category_name)

    if category:
        return True

    return False


async def change_name(message, name):
    member = message.guild.get_member(message.author.id)
    await member.edit(nick=name)


async def set_channels_for_lecturer(guild):
    for category in guild.categories:
        if sum(char.isdigit() for char in category.name) == 1:
            for role in guild.roles:
                if role.name.startswith("Lecturer"):
                    await category.set_permissions(role, read_messages=True, send_messages=True)


async def add_user(message, data):
    series = hashlib.sha512(data['series'].encode()).hexdigest()
    async with await create_db_pool() as pool:
        async with pool.acquire() as con:
            async with con.transaction():
                query = "INSERT INTO discord_users (user_id, server_id, name, date, series) VALUES ($1, $2, $3, $4, $5)"
                await con.execute(query, str(message.author.id), str(message.guild.id),
                                  data['name'], datetime.strptime(data['expired'], '%d.%m.%Y').date(), series)


async def is_user_exists(message, data):
    series = hashlib.sha512(data['series'].encode()).hexdigest()
    async with await create_db_pool() as pool:
        async with pool.acquire() as con:
            async with con.transaction():
                query = "SELECT COUNT(*) FROM discord_users WHERE server_id = $1 AND name = $2 AND series = $3"
                count = await con.fetchval(query, str(message.guild.id), data['name'], series)
                return count > 0


async def remove_user(user_id, server_id):
    async with await create_db_pool() as pool:
        async with pool.acquire() as con:
            async with con.transaction():
                query = "DELETE FROM discord_users WHERE user_id = $1 AND server_id = $2"
                await con.execute(query, user_id, server_id)


async def find_a_graduate():
    async with await create_db_pool() as pool:
        async with pool.acquire() as con:
            async with con.transaction():
                query = "SELECT * FROM discord_users WHERE date < $1"
                return await con.fetch(query, datetime.now().date())
