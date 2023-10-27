from websockets.client import connect
import websockets.server
import json
import time
import wave
import io
import requests
import logging
import websockets
from asyncio.queues import Queue, PriorityQueue
from pydub import AudioSegment
import asyncio
from dataclasses import dataclass, field

import twitch

@dataclass
class SpeechEvent:
    response_text: str = field(default = None, compare = False)
    audio_segment: AudioSegment = field(default = None, compare = False)
    pass

@dataclass(init = False, order = True)
class ChatSpeechEvent(SpeechEvent):
    priority: int = 0
    user_message: str = field(default = None, compare = False)
    def __init__(self, user_message):
        self.response_text = None
        self.audio_segment = None
        self.user_message = user_message
    pass

async def fetch_llm(prompt):
    start = time.time()
    response = requests.post("https://melba.shuni.moe/generate_response", json = {"message": prompt, "prompt_setting": 0,"person": "Chat"})
    end = time.time()
    if response.status_code == 200:
        print("LLM time:", end - start)
        return response.json()["response_text"]
    else:
        return None

chat_messages = PriorityQueue(maxsize=10)
tts_queue = Queue(maxsize=5)
speech_queue = Queue(maxsize=5)

async def llm_loop():
    while True:
        message = await chat_messages.get()
        response = await fetch_llm(message.user_message)
        if response is not None:
            try:
                message.response_text = response
                await tts_queue.put(message)
            except asyncio.QueueFull:
                print("TTS queue full, dropping message: " + message.response_text)

async def fetch_tts(text):
    start = time.time()
    response = requests.post("https://melba-tts.zuzu.red/synthesize", data = {'text': text, 'voice': 'voice1'})
    end = time.time()
    print("TTS time:", end - start)
    return AudioSegment.from_file(io.BytesIO(response.content))

async def tts_loop():
    while True:
        message = await tts_queue.get()
        response = await fetch_tts(message.response_text)
        if response is not None:
            message.audio_segment = response
            await speech_queue.put(message)

# Connection to Melba Toaster
class Toaster:
    def __init__(self):
        self._websocket_clients = []

        self.toast = True
        self.void = False

    async def listen(self):
        try:
            async with websockets.server.serve(self._websocket_handler, host = "127.0.0.1", port = 9876) as server:
                await server.serve_forever()
        except asyncio.CancelledError:
            print("Cancelled!")

    async def _websocket_handler(self, websocket):
        print("Toaster connected")
        self._websocket_clients.append(websocket)
        while True:
            await asyncio.sleep(.5) # surely nothing will go wrong if i set it to 0.5 :clueless:
        print("Websocket handler exited")

    async def _send_message(self, message):
        for client in self._websocket_clients:
            try:
                await client.send(message)
            except ConnectionClosed:
                print("Toaster connection closed")
                self._websocket_clients.remove(websocket)

    async def speak_audio(self, audio_segment): # TODO: maybe somehow pass the speech without using files?
        mp3_file = io.BytesIO()
        audio_segment.export(mp3_file, format="mp3")
        await self._send_message(mp3_file.getvalue())

async def speech_loop(toaster):
    while True:
        speech_event = await speech_queue.get()
        print("Speaking: " + speech_event.response_text)
        print("Responding to: " + speech_event.user_message)
        await toaster.speak_audio(speech_event.audio_segment)
        print("Done speaking")

async def add_message(message: str):
    print("Chat message:", message)
    await chat_messages.put(ChatSpeechEvent(message))
    pass

async def main():
    toaster = Toaster()
    twitch_chat = twitch.Chat("<channel>", onmessage = add_message)
    async with asyncio.TaskGroup() as tg:
        tg.create_task(toaster.listen())
        tg.create_task(llm_loop())
        tg.create_task(tts_loop())
        tg.create_task(speech_loop(toaster))
        tg.create_task(twitch_chat.connect())
        print(f"started at {time.strftime('%X')}")

if __name__ == "__main__":
    asyncio.run(main())
