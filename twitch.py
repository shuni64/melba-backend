from twitchio import Client

import config

class Chat():
    def __init__(self, channel, onmessage):
        self._channel = channel
        self.onmessage = onmessage
    async def connect(self):
        client = Client(token=config.twitch_access_token, initial_channels=[self._channel])
        await client.connect()
        client.event_message = self._onmessage
        print("Twitch chat connected")

    async def _onmessage(self, message):
        await self.onmessage(message.content, message.author.name)

