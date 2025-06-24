import socketio
from dotenv import load_dotenv
import os
load_dotenv()

# REDIS
REDIS_URI = os.getenv("REDIS_URI", "127.0.0.1")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "123456")

# comment/edit line 5 if you don't want use redis or using other message queue
# see https://python-socketio.readthedocs.io/en/latest/server.html#using-a-message-queue
# redis_url = f"redis://:{REDIS_PASSWORD}@{REDIS_URI}:{REDIS_PORT}/0" #"redis://user:password@host:port/db"  # Replace with your Redis URL
# (default) => redis_url = "redis://127.0.0.1:6379/0"
redis_url = f"redis://{REDIS_URI}:{REDIS_PORT}/0"
mgr = socketio.AsyncRedisManager(url=redis_url) 
sio = socketio.AsyncServer(
    async_mode="asgi", cors_allowed_origins="*", client_manager=mgr
)
