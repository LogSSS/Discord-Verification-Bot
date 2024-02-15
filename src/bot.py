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
    async def on_member_join(member):
        print(f"{member} has joined the server!")

    @client.event
    async def on_raw_reaction_add(payload):
        if payload.emoji.name == "✅" and str(payload.message_id) == "1172528409436504167":
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
                    await f.read_image(message)

    client.run(os.environ['TOKEN'])
