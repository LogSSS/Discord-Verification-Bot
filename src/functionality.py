import discord
import requests
import numpy as np
import cv2

from pyzbar.pyzbar import decode
from src import responses
from src import verify
from src.cv import get_data as gt
from src import roles


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


async def send_message(message, user_message, is_private):
    try:
        response = responses.handle_response(user_message)

        await message.author.send(response) if is_private else await message.channel.send(response)
    except Exception as e:
        print(e)


async def verification(message, bot, loading_message):
    try:
        attachment = message.attachments[0]

        img = await get_img(attachment.url)

        link = await get_link(img)

        if link is not None:

            data = verify.verify_by_qr(link)

            if data:
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
            await roles.create_role(message.guild, role, None, True, get_new_role_id(message.guild, role))
            if not roles.is_role_exists(message.guild, faculty):
                await roles.create_role(message.guild, faculty, None, False)
            if not roles.is_category_exists(message.guild, faculty):
                await roles.create_faculty_channel(message.guild, faculty)
            await roles.create_channels(message.guild, data['group'], faculty)

        await roles.add_role(message, faculty)
        await roles.add_role(message, role)
        await roles.add_role(message, "Verified")
    except Exception as e:
        print(f"An error occurred: {e}")


async def get_new_role_id(guild, role):
    for item in guild.roles:
        if any(char.isdigit() for char in item):
            return item.id
        if item.name > role:
            return item.id


async def on_guild_join(guild):
    await on_guild_join_create_roles(guild)
    await on_guild_join_create_channels(guild)


async def on_guild_join_create_roles(guild):
    if not roles.is_role_exists(guild, "Admin"):
        await roles.create_role(guild, "Admin", discord.Colour.from_rgb(103, 26, 153), True, 1,
                                discord.Permissions(administrator=True))
        await guild.owner.add_roles(discord.utils.get(guild.roles, name="Admin"))

    if not roles.is_role_exists(guild, "Verified"):
        await roles.create_role(guild, "Verified", discord.Colour.from_rgb(71, 7, 7), False)


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
            # change message id
            for i in range(len(lines)):
                if str(guild.id) in lines[i]:
                    lines[i] = f"{guild.id} - {message.id}\n"
                    break
    else:
        with open("src/data/channels.txt", "w") as file:
            file.write(f"{guild.id} - {message.id}\n")

    category = await guild.create_category("AFK")
    await category.set_permissions(discord.utils.get(guild.roles, name="Verified"), read_messages=True)

    channel = await guild.create_voice_channel("Тихий час", category=category)
    await channel.set_permissions(guild.default_role, read_messages=False)

    await guild.edit(afk_channel=channel)
