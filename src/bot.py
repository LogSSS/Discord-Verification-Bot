import asyncio
import discord
import os

from discord.ext import commands
from src import functionality as f


def run_discord_bot():
    client = discord.Client()
    intents = discord.Intents.default()
    intents.messages = True
    intents.guilds = True
    intents.members = True

    client = commands.Bot(command_prefix="!", intents=intents)

    @client.event
    async def on_ready():
        print(f"Logged in as {client.user}")
        await client.change_presence(activity=discord.Game('👀'))

    @client.event
    async def on_guild_join(guild):
        print(f'Bot joined server: {guild.name} (ID: {guild.id})')
        if guild.system_channel:
            await guild.system_channel.send("Hello! I`m landed here! Use !help to get more information about me!")
        await f.on_guild_join(guild)

    @client.event
    async def on_member_join(member):
        print(f"{member} has joined the server!")

    @client.event
    async def on_raw_reaction_add(payload):
        try:
            with open("src/data/channels.txt", "r") as file:
                lines = file.readlines()

            message_id = None
            for line in lines:
                if str(payload.guild_id) in line:
                    message_id = line.split(" - ")[1].strip()
                    break

            if payload.emoji.name == "✅" and str(payload.message_id) == message_id:
                guild = client.get_guild(payload.guild_id)
                await f.create_verification_channel(guild.get_member(payload.user_id), guild)
        except Exception as e:
            print(f"An error occurred while adding reaction: {e}")

    @client.event
    async def on_message(message):
        if message.author == client.user:
            return

        if message.content.startswith('!'):
            await f.send_message(message, message.content[1:], False)

        if isinstance(message.channel, discord.channel.TextChannel):
            if message.channel.category and message.channel.category.name == "VERIFICATION":
                if message.attachments:
                    loading_message = await message.channel.send("Processing...")
                    if await f.verification(message):
                        await asyncio.sleep(5)
                        await message.channel.delete()
                    else:
                        await loading_message.delete()

    client.run(os.environ['TOKEN'])
