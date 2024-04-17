import asyncio
import os

import discord
from discord.ext import commands, tasks
from discord_components import DiscordComponents, Button, ButtonStyle, ActionRow

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

    @tasks.loop(minutes=30)
    async def news_check():
        await f.news_check(client)

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
            return await f.close_ticket(interaction)

        if interaction.component.label == "Approve":
            return await f.approve_question(interaction)

        if interaction.component.label == "Decline":
            return await f.decline_question(interaction)

        if interaction.component.label == "Ask":
            return await f.ask_question(interaction)

        if interaction.component.label == "Interested":
            return await f.interested(interaction)

        if interaction.component.label == "Not Interested":
            return await f.not_interested(interaction)

    @client.event
    async def on_message(message):
        if message.author == client.user:
            return

        if message.content.startswith('!'):
            await f.news_check(client)
            await f.handle_response(message, client)

        if isinstance(message.channel, discord.channel.TextChannel):
            if "create-news" in message.channel.name:
                resp = await f.create_news(message)
                if not resp[0]:
                    await asyncio.sleep(20)
                    await message.delete()

            if "ask-" in message.channel.name:
                channel = discord.utils.get(message.guild.channels, name="questions")
                await channel.send(message.content, components=[
                    ActionRow(
                        Button(style=ButtonStyle.green, label="Approve", custom_id="approve"),
                        Button(style=ButtonStyle.red, label="Decline", custom_id="decline")
                    )
                ])

            elif message.channel.category and message.channel.category.name == "VERIFICATION":
                if message.attachments:
                    loading_message = await message.channel.send("Processing...")
                    if await f.verification(message, client, loading_message):
                        await asyncio.sleep(5)
                        await message.channel.delete()

    client.loop.run_until_complete(create_db_pool())
    date_check.start()
    news_check.start()
    client.run(os.environ['TOKEN'])
