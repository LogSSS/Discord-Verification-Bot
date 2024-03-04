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


async def verification(message):
    try:
        attachment = message.attachments[0]

        response = requests.get(attachment.url)
        img_array = np.frombuffer(response.content, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        decoded_objects = decode(img)
        link = None

        for obj in decoded_objects:
            c = obj.data.decode('utf-8')
            if "https://diia.app/documents/student-id-card/" in c and "/verify/" in c:
                link = obj.data.decode('utf-8')
                break

        if link is not None:

            data = verify.verify_by_qr(link)

            if data:
                await message.channel.send(f"Sorry but we cant verify u now\n{data[1]}")
            else:
                await message.channel.send("Sorry, but your qr code is not valid! Please try again.")
                return False
        else:
            data = gt(img)
            if data:

                if verify.verify_by_card(data):
                    await name_roles_and_channels(message, data)
                    await message.channel.send("You have been verified!")
                else:
                    await message.channel.send("Sorry, but your student card is not valid! Please try again.")
            else:
                await message.channel.send("Uploaded image is not valid! Please try again.")
                return False
    except Exception as e:
        print(e)
        return False
    return True


async def name_roles_and_channels(message, data):
    try:
        await roles.change_name(message, data[1]['name'])

        faculty = ''.join(word[0] for word in str(data[1]['faculty']).split() if len(word) > 2).upper()
        role = data[1]['group'] + " " + faculty

        if not roles.is_role_exists(message, role):
            await roles.create_role(message.guild, role)
            if not roles.is_role_exists(message, faculty):
                await roles.create_role(message.guild, faculty)
            if not roles.is_category_exists(message.guild, faculty):
                await roles.create_faculty_channel(message.guild, faculty)
            await roles.create_channels(message.guild, data[1]['group'], faculty)

        await roles.add_role(message, faculty)
        await roles.add_role(message, role)
        await roles.add_role(message, "Verified")
    except Exception as e:
        print(f"An error occurred: {e}")
