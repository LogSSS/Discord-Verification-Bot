import discord
import responses
import requests
import numpy as np
import cv2
from pyzbar.pyzbar import decode
from cv import get_data as gt


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


async def read_image(message):
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
            # verify by link
            await message.channel.send(f"Verification link: {link}\n")
        else:
            data = gt(img)
            if data:
                # verify by data
                await message.channel.send(data)
            else:
                await message.channel.send("Your image is not valid! Please try again.")
    except Exception as e:
        print(e)
    return

#                    await message.author.send("You have been verified!")
#                    await message.author.add_roles(discord.utils.get(message.guild.roles, name="Verified"))
