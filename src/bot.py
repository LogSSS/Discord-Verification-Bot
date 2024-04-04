import asyncio
import os

import discord
from discord.ext import commands, tasks
from discord_components import DiscordComponents, Button, ButtonStyle

from src import functionality as f
from src.db import create_db_pool


def run_discord_bot():
    client = discord.Client()
    intents = discord.Intents.default()
    intents.messages = True
    intents.guilds = True
    intents.members = True

    client = commands.Bot(command_prefix="!", intents=intents)
    DiscordComponents(client)

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
        await member.add_roles(discord.utils.get(member.guild.roles, name="Guest"))
        print(f"{member} has joined the server!")

    @tasks.loop(hours=24)
    async def date_check(guild):
        await f.date_check(guild)

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
    async def on_button_click(interaction):
        if interaction.component.label == "Close":
            await interaction.respond(type=6)
            await asyncio.sleep(2)
            await interaction.channel.delete()
            return
        if interaction.component.label == "Ask":
            await interaction.respond(type=6)
            name = "ask-" + interaction.user.name
            channel = discord.utils.get(interaction.guild.channels, name=name)
            if channel:
                await channel.send("You already have a channel for asking questions!")
                return
            channel = await interaction.guild.create_text_channel(name, category=discord.utils.get(
                interaction.guild.categories, name="Questions and Answers"))
            await channel.send("Ask your question here! And please close ticket. Thank you!", components=[
                Button(style=ButtonStyle.red, label="Close", custom_id="close")])
            return
        if interaction.component.label == "Approve":
            await interaction.respond(type=6)
            ans = discord.utils.get(interaction.guild.channels, name="answers")
            message = await ans.send(interaction.message.content)
            await message.pin()
            await interaction.message.delete()
            return
        if interaction.component.label == "Decline":
            await interaction.respond(type=6)
            await interaction.message.delete()
            return

    @client.event
    async def on_message(message):
        if message.author == client.user:
            return

        if message.content.startswith('!'):
            await f.handle_response(message, client)

        if isinstance(message.channel, discord.channel.TextChannel):
            if "ask-" in message.channel.name:
                channel = discord.utils.get(message.guild.channels, name="questions")
                await channel.send(message.content, components=[
                    Button(style=ButtonStyle.green, label="Approve", custom_id="approve"),
                    Button(style=ButtonStyle.red, label="Decline", custom_id="decline")
                ])

            elif message.channel.category and message.channel.category.name == "VERIFICATION":
                if message.attachments:
                    loading_message = await message.channel.send("Processing...")
                    if await f.verification(message, client, loading_message):
                        await asyncio.sleep(5)
                        await message.channel.delete()

    client.loop.run_until_complete(create_db_pool())
    client.run(os.environ['TOKEN'])
