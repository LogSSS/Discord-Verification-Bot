import discord
import requests
import numpy as np
import cv2

from discord_components import Button, ButtonStyle
from pyzbar.pyzbar import decode
from src import responses
from src import verify
from src.cv import get_data as gt
from src import roles


async def handle_response(message, client):
    if message.guild is None and message.content.startswith("!ask"):
        response = await responses.ask_question(message, client)
        return response
    return responses.handle_response(message)


async def create_verification_channel(member, guild):
    try:
        if member and not member.bot:
            verification_channel_name = "verification"
            verification_channel = discord.utils.get(guild.channels, name=verification_channel_name)

            if verification_channel is not None:
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    member: discord.PermissionOverwrite(read_messages=True, send_messages=True)
                }

                channel_name = f"verif-{member.name}"

                if channel_name in [channel.name for channel in verification_channel.category.text_channels]:

                    channel = discord.utils.get(verification_channel.category.text_channels, name=channel_name)
                    await channel.send(f"HE-HE! {member.mention}, u already have a verification channel!")

                else:

                    channel = await verification_channel.category.create_text_channel(channel_name,
                                                                                      overwrites=overwrites)
                    await channel.send(
                        f"Welcome, {member.mention}! Here u can verify ur account.\n"
                        f"To verify upload qr code from diia app or student id card photo")

    except Exception as e:
        print(e)


async def verification(message, bot, loading_message):
    try:
        attachment = message.attachments[0]

        img = await get_img(attachment.url)

        link = await get_link(img)

        if link is not None:

            data = await verify.verify_by_qr(link)

            if data[0]:
                await loading_message.delete()
                await message.channel.send(f"Sorry but we cant verify u now\n{data[1]}")
                return False
            else:
                await loading_message.delete()
                await message.channel.send("Sorry, but your qr code is not valid! Please try again.")
                return False
        else:
            data = gt(img)
            await loading_message.delete()
            if data[0]:
                data = await verify.verify_by_card(data[1], message, bot)
                if data[0]:
                    data = data[1]
                    if not await roles.is_user_exists(message, data):
                        await roles.add_user(message, data)
                        await name_roles_and_channels(message, data)
                        await message.channel.send("You have been verified!")
                        return True
                    await message.channel.send("User already exists!")
                    return False
                else:
                    await message.channel.send("Sorry, but your student card is not valid! Please try again.")
                    await message.channel.send(data[1])
                    return False
            else:
                await message.channel.send(data[1] + "\nPlease try again.")
                return False
    except Exception as e:
        print(e)
        return False


async def get_link(img):
    decoded_objects = decode(img)
    link = None

    for obj in decoded_objects:
        c = obj.data.decode('utf-8')
        if "https://diia.app/documents/student-id-card/" in c and "/verify/" in c:
            link = obj.data.decode('utf-8')
            break
    return link


async def get_img(url):
    response = requests.get(url)
    img_array = np.frombuffer(response.content, dtype=np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    return img


async def name_roles_and_channels(message, data):
    try:
        await roles.change_name(message, data['name'])

        faculty = ''.join(word[0] for word in str(data['faculty']).split() if len(word) > 2).upper()
        role = data['group'] + " " + faculty

        if not roles.is_role_exists(message.guild, role):
            await roles.create_role(message.guild, role, None, True, 4)
            if not roles.is_role_exists(message.guild, faculty):
                await roles.create_role(message.guild, faculty, None, False)
                await roles.create_role(message.guild, f"Lecturer {faculty}", None, False)
            if not roles.is_category_exists(message.guild, faculty):
                await roles.create_faculty_channel(message.guild, faculty)
            await roles.create_channels(message.guild, data['group'], faculty)

        await roles.add_role(message, faculty)
        await roles.add_role(message, role)
        await roles.add_role(message, "Verified")
        await roles.remove_role(message, "Guest")
        await set_channels_for_lecturer(message.guild)
    except Exception as e:
        print(f"An error occurred1: {e}")


async def get_new_role_id(guild, role):
    for item in guild.roles:
        if any(char.isdigit() for char in item):
            return item.id
        if item.name > role:
            return item.id


async def set_channels_for_lecturer(guild):
    for category in guild.categories:
        if sum(char.isdigit() for char in category.name) == 1:
            for role in guild.roles:
                if role.name.startswith("Lecturer"):
                    await category.set_permissions(role, read_messages=True, send_messages=True)


async def on_guild_join(guild):
    await on_guild_join_create_roles(guild)
    await on_guild_join_create_channels(guild)


async def on_guild_join_create_roles(guild):
    if not roles.is_role_exists(guild, "Admin"):
        await roles.create_role(guild, "Admin", discord.Colour.from_rgb(103, 26, 153), True, 1,
                                discord.Permissions(administrator=True))
        await guild.owner.add_roles(discord.utils.get(guild.roles, name="Admin"))

    if not roles.is_role_exists(guild, "Graduate"):
        await roles.create_role(guild, "Graduate", discord.Colour.from_rgb(255, 255, 0), True)

    if not roles.is_role_exists(guild, "Verified"):
        await roles.create_role(guild, "Verified", discord.Colour.from_rgb(71, 7, 7), False)

    if not roles.is_role_exists(guild, "Guest"):
        await roles.create_role(guild, "Guest", discord.Colour.from_rgb(220, 210, 215), True)


async def on_guild_join_create_channels(guild):
    category = await guild.create_category("VERIFICATION")
    await category.set_permissions(discord.utils.get(guild.roles, name="Verified"), read_messages=False)

    channel = await guild.create_text_channel("VERIFICATION", category=category)
    await channel.set_permissions(guild.default_role, send_messages=False)
    await channel.set_permissions(discord.utils.get(guild.roles, name="Verified"), read_messages=False)

    message = await channel.send("Message for verification\nPress ✅ emoji to complete verification\n\n@everyone")
    await message.add_reaction("✅")

    with open("src/data/channels.txt", "r") as file:
        lines = file.readlines()

    if len(lines) > 0:
        if str(guild.id) not in lines:
            with open("src/data/channels.txt", "a") as file:
                file.write(f"{guild.id} - {message.id}\n")
        else:
            for i in range(len(lines)):
                if str(guild.id) in lines[i]:
                    lines[i] = f"{guild.id} - {message.id}\n"
                    break
    else:
        with open("src/data/channels.txt", "w") as file:
            file.write(f"{guild.id} - {message.id}\n")

    category = await guild.create_category("Questions and Answers")
    ask = await guild.create_text_channel("Ask", category=category)
    await ask.set_permissions(guild.default_role, read_messages=True, send_messages=False)
    await ask.send("To ask a question, please press the button below", components=[
        Button(style=ButtonStyle.green, label="Ask", custom_id="ask")
    ])
    mods_channel = await guild.create_text_channel("Questions", category=category)
    await mods_channel.set_permissions(guild.default_role, read_messages=False)
    answers = await guild.create_text_channel("Answers", category=category)
    await answers.set_permissions(guild.default_role, send_messages=True, read_messages=True)

    category = await guild.create_category("General")
    await guild.create_text_channel("General", category=category)
    news = await guild.create_text_channel("News", category=category)
    await news.set_permissions(guild.default_role, send_messages=False, read_messages=True)
    await guild.create_voice_channel("Meeting-1", category=category)
    await guild.create_voice_channel("Meeting-2", category=category)

    category = await guild.create_category("AFK")
    await category.set_permissions(discord.utils.get(guild.roles, name="Verified"), read_messages=True)

    channel = await guild.create_voice_channel("Тихий час", category=category)
    await channel.set_permissions(guild.default_role, read_messages=False)

    await guild.edit(afk_channel=channel)


async def date_check(guild):
    users = await roles.find_a_graduate()
    for user in users:
        user_id = user['user_id']
        server_id = user['server_id']
        user = await guild.fetch_member(user_id)
        # remove before adding
        await user.add_roles(discord.utils.get(guild.roles, name="Graduate"))
        await roles.remove_user(user_id, server_id)
