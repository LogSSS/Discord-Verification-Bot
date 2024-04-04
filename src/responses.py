import discord
from discord_components import Button, ButtonStyle


def handle_response(message):
    p_message = message.content.lower()

    if p_message == "!help":
        return "Commands: !help, !refresh(only in verification channel), !ask <question> in DM"


async def ask_question(message, client):
    questions_channel = discord.utils.get(client.get_guild(1162071358549803170).channels, name="questions")
    question = message.content.split(" ", 1)[1]
    await questions_channel.send(question, components=[
        Button(style=ButtonStyle.green, label="Approve", custom_id="approve"),
        Button(style=ButtonStyle.red, label="Decline", custom_id="decline")
    ])
    return "Your question has been sent to the admins!"
