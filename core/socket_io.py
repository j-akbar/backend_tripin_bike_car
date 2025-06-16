import socketio

# comment/edit line 5 if you don't want use redis or using other message queue
# see https://python-socketio.readthedocs.io/en/latest/server.html#using-a-message-queue
redis_url = "redis://127.0.0.1:6379/0" #"redis://user:password@host:port/db"  # Replace with your Redis URL
mgr = socketio.AsyncRedisManager(url=redis_url) 
sio = socketio.AsyncServer(
    async_mode="asgi", cors_allowed_origins="*", client_manager=mgr
)
