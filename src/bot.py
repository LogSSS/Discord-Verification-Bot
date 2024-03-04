import asyncio
import discord
import os

from discord.ext import commands
from src import functionality as f
from src import roles as r


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

        await r.create_role(guild, "Verified", discord.Colour.from_rgb(71, 7, 7))
        category = await guild.create_category("VERIFICATION")
        channel = await guild.create_text_channel("VERIFICATION", category=category)
        await channel.set_permissions(guild.default_role, read_messages=True, send_messages=False)
        message = await channel.send("Message for verification\nPress ✅ emoji to complete verification\n\n@everyone")
        await message.add_reaction("✅")
        await category.set_permissions(discord.utils.get(guild.roles, name="Verified"), read_messages=True)

    @client.event
    async def on_member_join(member):
        print(f"{member} has joined the server!")

    @client.event
    async def on_raw_reaction_add(payload):
        # get id by guild and message id
        message_id = "1214344664895987763"
        if payload.emoji.name == "✅" and str(payload.message_id) == message_id:
            guild = client.get_guild(payload.guild_id)
            await f.create_verification_channel(guild.get_member(payload.user_id), guild)

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
                    await loading_message.delete()

    client.run(os.environ['TOKEN'])
