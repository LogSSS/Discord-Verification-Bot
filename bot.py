import discord
import responses


async def send_message(message, user_message, is_private):
    try:
        response = responses.handle_response(user_message)
        await message.author.send(response) if is_private else await message.channel.send(response)

    except Exception as e:
        print(e)


def run_discord_bot():
    TOKEN = 'MTE2NzA0MDYyNTM0Mjk1MTQyNA.GhygXI.jDM2L8h8kypwoZlAANa1_wBSsX0Wi1vN2kYoM0'
    client = discord.Client()

    @client.event
    async def on_ready():
        print(f"Logged in as {client.user}")
        await client.change_presence(activity=discord.Game('👀'))

    @client.event
    async def on_message(message):
        if message.author == client.user:
            return

        if message.content.startswith('!'):
            await send_message(message, message.content[1:], False)

    client.run(TOKEN)
