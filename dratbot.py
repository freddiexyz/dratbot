import discord
import yaml

with open('config.yaml', 'r') as yml:
    config = yaml.safe_load(yml)

discord_secret: str = config.get('discord_token')
channel_id:     int = config.get('channel_id')

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We are logged in as {client.user}.')
    
    await client.get_channel(channel_id).send('Hello everbody, my name is Dratbot')
    

@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return
    
    if message.content.startswith('!test'):
        await message.channel.send('test test')

client.run(discord_secret)