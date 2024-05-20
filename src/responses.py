import asyncio
import re

import discord
from discord_components import Button, ButtonStyle, ActionRow
from src.db import create_db_pool


def handle_response(message):
    p_message = message.content.lower()

    if p_message == "!help":
        return "Commands: !help, !refresh(only in verification channel), !ask <question> in DM"


async def ask_anon(message, client):
    questions_channel = discord.utils.get(client.get_guild(1162071358549803170).channels, name="questions")
    question = message.content.split(" ", 1)[1]
    await questions_channel.send(question, components=[
        ActionRow(
            Button(style=ButtonStyle.green, label="Approve", custom_id="approve"),
            Button(style=ButtonStyle.red, label="Decline", custom_id="decline")
        )
    ])
    return "Your question has been sent to the admins!"


async def close_ticket(interaction):
    await interaction.respond(type=6)
    await asyncio.sleep(2)
    await interaction.channel.delete()


async def approve_question(interaction):
    await interaction.respond(type=6)
    ans = discord.utils.get(interaction.guild.channels, name="answers")
    message = await ans.send(interaction.message.content)
    await message.pin()
    await interaction.message.delete()


async def decline_question(interaction):
    await interaction.respond(type=6)
    await interaction.message.delete()


async def ask_question(interaction):
    await interaction.respond(type=6)
    name = "ask-" + interaction.user.name
    channel = discord.utils.get(interaction.guild.channels, name=name)
    if channel:
        await channel.send("You already have a channel for asking questions!")
        return
    category = discord.utils.get(interaction.guild.categories, name="Questions and Answers")
    overwrites = {
        interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        interaction.author: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }
    channel = await interaction.guild.create_text_channel(name, category=category, overwrites=overwrites)
    await channel.send(
        f"Hey, {interaction.author.mention}, ask your question here! And please close ticket. Thank you!",
        components=[
            Button(style=ButtonStyle.red, label="Close", custom_id="close")])

    async def delete_channel(chan):
        await asyncio.sleep(3600)
        await chan.delete()

    asyncio.ensure_future(delete_channel(channel))


async def interested(interaction):
    await interaction.respond(type=6)
    user_id = str(interaction.user.id)
    message_id = str(interaction.message.id)
    guild_id = str(interaction.guild.id)
    async with await create_db_pool() as pool:
        async with pool.acquire() as conn:
            existing_interest = await conn.fetchval(
                "SELECT 1 FROM interested_users WHERE user_id = $1 AND message_id = $2 AND guild_id = $3",
                user_id, message_id, guild_id
            )
            if existing_interest:
                return

            await conn.execute(
                "INSERT INTO interested_users (user_id, message_id, guild_id) "
                "VALUES ($1, $2, $3)",
                user_id, message_id, guild_id
            )
    interested_count = await get_interested_count(message_id, guild_id)

    await set_interested_count(interaction, interested_count)

    data = await parse_news_text(interaction.message.content)

    link = await create_google_calendar_link(data)

    text = interaction.message.content.split("\n")[0]
    await interaction.user.send(
        f"You have shown interest in \"{text}\". Also you can add this event to your Google Calendar.",
        components=[
            ActionRow(
                Button(style=ButtonStyle.URL, label="Google Calendar", url=link)
            )
        ]
    )


async def not_interested(interaction):
    await interaction.respond(type=6)
    user_id = str(interaction.user.id)
    message_id = str(interaction.message.id)
    guild_id = str(interaction.guild.id)
    async with await create_db_pool() as pool:
        async with pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM interested_users WHERE user_id = $1 AND message_id = $2 AND guild_id = $3",
                user_id, message_id, guild_id
            )
    interested_count = await get_interested_count(message_id, guild_id)

    await set_interested_count(interaction, interested_count)


async def create_google_calendar_link(data):
    title = data[0]
    description = data[1].replace("\n", "%0A")
    date = data[2]
    start_time = data[3]
    end_time = data[4]
    location = data[5]

    base_url = "https://www.google.com/calendar/render?action=TEMPLATE"
    title_param = "&text=" + title.replace(" ", "+")
    description_param = "&details=" + description.replace(" ", "+")
    date_parts = date.split(".")
    date_param = "&dates=" + date_parts[2] + date_parts[1] + date_parts[0] + "T" + start_time.replace(":",
                                                                                                      "") + "00+0300/" + \
                 date_parts[2] + date_parts[1] + date_parts[0] + "T" + end_time.replace(":", "") + "00+0300"

    location_param = "&location=" + location.replace(" ", "+")

    return base_url + title_param + description_param + date_param + location_param


async def parse_news_text(str):
    lines = str.split("\n")
    title = lines[0]

    description = ""
    for i, line in enumerate(lines[1:], start=1):
        if line.startswith("Start date:"):
            break
        description += line + "\n"
    description = description.strip()

    date_match = re.search(r"Start date: (\d{2}\.\d{2}\.\d{4})", str)
    start_time_match = re.search(r"Start time: (\d{2}:\d{2})", str)
    end_time_match = re.search(r"End time: (\d{2}:\d{2})", str)
    place_match = re.search(r"Place: (.+)", str)

    if date_match and start_time_match and end_time_match and place_match:
        date = date_match.group(1)
        start_time = start_time_match.group(1)
        end_time = end_time_match.group(1)
        location = place_match.group(1)
    else:
        raise ValueError("News text is not formatted properly")
    return title, description, date, start_time, end_time, location


async def set_interested_count(interaction, count):
    content = interaction.message.content
    pattern = r'Interested: \d+\n'
    content = re.sub(pattern, f'Interested: {count}\n', content)
    await interaction.message.edit(content=content)


async def get_interested_count(message_id, guild_id):
    async with await create_db_pool() as pool:
        async with pool.acquire() as conn:
            count = await conn.fetchval(
                "SELECT COUNT(*) FROM interested_users WHERE message_id = $1 AND guild_id = $2",
                message_id, guild_id
            )
    return count
