from flask import Flask, request, jsonify

import discord
from discord.ext import tasks

import googleapiclient.discovery
import threading
import requests
import yaml

# Globals
latest_youtube_video_id: str = None
discord_channel: discord.channel.TextChannel = None
twitch_channel_id: int = 25618880 # twitch.tv/dratnos

# Load secrets from config
with open('config.yaml', 'r') as yml:
    config = yaml.safe_load(yml)

discord_secret: str     = config.get('discord_token')
discord_channel_id: int = config.get('discord_channel_id')
youtube_api_key: str    = config.get('youtube_api_key')
youtube_channel_id: str = config.get('youtube_channel_id')
twitch_client_id: str   = config.get('twitch_client_id')
twitch_secret: str      = config.get('twitch_secret')

# Initialise Youtube API
youtube = googleapiclient.discovery.build(
    'youtube', 'v3', developerKey=youtube_api_key
)

# Initialise Discord API
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@tasks.loop(seconds=30)
async def check_youtube_videos():
    global latest_youtube_video_id

    request = youtube.search().list(
            part='snippet',
            channelId=youtube_channel_id,
            order='date',
            maxResults=1
        )
    response = request.execute()
    new_youtube_video = response['items'][0]
    new_youtube_video_id: str = new_youtube_video['id']['videoId']

    if latest_youtube_video_id is None:
        latest_youtube_video_id = new_youtube_video_id

    if new_youtube_video_id != latest_youtube_video_id:
        print('New video uploaded')
        alert_message = 'New Dratnos Youtube video!\n' + f'https://www.youtube.com/watch?v={new_youtube_video_id}'
        await discord_channel.send(alert_message)
        latest_youtube_video_id = new_youtube_video_id
    else:
        print('No new video detected')

async def stream_online_alert():
    alert_message = 'Dratnos is live!\n' + f'https://twitch.tv/dratnos'
    await discord_channel.send(alert_message)

@client.event
async def on_ready():
    print(f'We are logged in as {client.user}.')
    # Initalise channel once connected
    global discord_channel
    discord_channel = client.get_channel(discord_channel_id)
    await discord_channel.send('Hello everbody, my name is Dratbot')
    
    # Start Tasks
    check_youtube_videos.start()

# Initalise Flask Webserver
app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def twitch_webhook():
    print(request.data)

    return jsonify({"message": "Webhook received successfully"}), 200

# Get OAuth token
auth_url = 'https://id.twitch.tv/oauth2/token'
auth_payload = {
    'client_id': twitch_client_id,
    'client_secret': twitch_secret,
    'grant_type': 'client_credentials'
}
auth_response = requests.post(auth_url, params=auth_payload)
auth_data = auth_response.json()
oauth_token = auth_data['access_token']

# Subscribe to 'stream.online' webhook
webhook_url = 'https://api.twitch.tv/helix/eventsub/subscriptions'
headers = {
    'Client-ID': twitch_client_id,
    'Authorization': f'Bearer {oauth_token}',
    'Content-Type': 'application/json'
}
payload = {
    "type": "stream.online",
    "version": "1",
    "condition": {
        "broadcaster_user_id": f'{twitch_channel_id}'
    },
    "transport": {
        "method": "webhook",
        "callback": 'https://95ec-125-238-24-178.ngrok.io/webhook',
        "secret": "YourSecretString"  # Replace with your own secret string for verifying incoming notifications
    }
}
response = requests.post(webhook_url, headers=headers, json=payload)
app.run(port=5000)

# DratBot Launch Sequence
# client.run(discord_secret)
