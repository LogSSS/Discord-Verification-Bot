import asyncio

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
    pool = await create_db_pool()

    async with pool.acquire() as conn:
        existing_interest = await conn.fetchval(
            "SELECT 1 FROM interested_users WHERE user_id = $1 AND message_id = $2 AND guild_id = $3",
            user_id, message_id, guild_id
        )
        if existing_interest:
            await pool.close()
            return

        await conn.execute(
            "INSERT INTO interested_users (user_id, message_id, guild_id) "
            "VALUES ($1, $2, $3)",
            user_id, message_id, guild_id
        )
    await pool.close()
    interested_count = await get_interested_count(message_id, guild_id)

    await interaction.message.edit(content=interaction.message.content.replace(
        f"Interested: {interaction.message.content.splitlines()[7].split(': ')[1]}",
        f"Interested: {interested_count}"
    ))

    await interaction.user.send(
        "You have shown interest in the event. If you are no longer interested, please click the 'Not Interested' button.")


async def not_interested(interaction):
    await interaction.respond(type=6)
    user_id = str(interaction.user.id)
    message_id = str(interaction.message.id)
    guild_id = str(interaction.guild.id)
    pool = await create_db_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM interested_users WHERE user_id = $1 AND message_id = $2 AND guild_id = $3",
            user_id, message_id, guild_id
        )
    await pool.close()
    interested_count = await get_interested_count(message_id, guild_id)

    await interaction.message.edit(content=interaction.message.content.replace(
        f"Interested: {interaction.message.content.splitlines()[7].split(': ')[1]}",
        f"Interested: {interested_count}"
    ))


async def get_interested_count(message_id, guild_id):
    pool = await create_db_pool()
    async with pool.acquire() as conn:
        count = await conn.fetchval(
            "SELECT COUNT(*) FROM interested_users WHERE message_id = $1 AND guild_id = $2",
            message_id, guild_id
        )
    await pool.close()
    return count
