import logging
import os
import asyncio
import json

import tornado.ioloop
import tornado.web
import tornado.websocket
import redis.asyncio as redis
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv("params.env")
APP_HOST = os.getenv("APP_HOST", "localhost")
APP_PORT = int(os.getenv("APP_PORT", 8888))
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
connections = {}

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("templates/index.html")

class RealtimeChatHandler(tornado.websocket.WebSocketHandler):
    redis_client = None
    user_name = None
    chat_room = None

    def initialize(self, redis_client):
        self.redis_client = redis_client

    def check_origin(self, origin) -> bool:
        return True

    async def open(self):
        self.user_name = self.get_argument("user", "admin")
        self.chat_room = self.get_argument("room_name", "admin_room")
        connections[self.user_name] = self

        await self._join_chat_room()
        asyncio.create_task(self.listen_to_redis())
        await self._notify_room_of_join()

    async def _join_chat_room(self):
        logging.info(f"User '{self.user_name}' is joining chat room '{self.chat_room}'")

    async def _notify_room_of_join(self):
        await asyncio.sleep(1)
        join_message = json.dumps({"type": "join", "user": self.user_name})
        await self.redis_client.publish(self.chat_room, join_message)
        logging.info(f"User '{self.user_name}' notified chat room '{self.chat_room}'")

    async def on_message(self, message):
        try:
            data = json.loads(message)
            room = data.get("room", self.chat_room)
            text = data.get("text", "")
            if text:
                await self._broadcast_message(room, text)
        except json.JSONDecodeError:
            logging.error("Failed to decode message: %s", message)

    async def _broadcast_message(self, room, text):
        message = json.dumps({"type": "message", "user": self.user_name, "text": text})
        await self.redis_client.publish(room, message)
        logging.info(f"User '{self.user_name}' sent message to room '{room}': {text}")

    async def listen_to_redis(self):
        pubsub = self.redis_client.pubsub()
        await pubsub.subscribe(self.chat_room)
        logging.info(f"Listening to Redis channel: {self.chat_room}")
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True)
            if message and message.get("data"):
                await self.write_message(json.loads(message["data"]))

    def on_close(self):
        if self.user_name in connections:
            del connections[self.user_name]
        logging.info(f"User '{self.user_name}' disconnected from chat room '{self.chat_room}'")

async def make_app():
    redis_client = await redis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}", decode_responses=True)
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/websocket", RealtimeChatHandler, {"redis_client": redis_client}),
    ], static_path="static")

if __name__ == "__main__":
    app = asyncio.run(make_app())
    app.listen(APP_PORT)
    logging.info(f"Server started at http://{APP_HOST}:{APP_PORT}")
    tornado.ioloop.IOLoop.current().start()
