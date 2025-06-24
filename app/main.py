import uvicorn
# start socketio
import socketio
from core.socket_io import sio
from routes.ws_no_prefix import NoPrefixNamespace
# end socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.controllers import include_routers
from app.data import models
from app.data.database import engine
import os
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="Backend TripIn for Bike and Car")

origins = [
    "http://localhost:5005",    # url server ini
    "http://localhost:3010",    # osmmap (tidak digunakan lagi)
    "http://localhost:3003",    # moblie_agent_travel_driver
    "http://localhost:3002",    # mobile_agent_travel_user
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


''' Automatically create table in database if any model is created '''
models.Base.metadata.create_all(bind=engine) 

@app.get("/")
def home():
    return ":("

include_routers(app)    # normal router api

# sio = socketio.Server() # for socketio
# sio = socketio.AsyncServer(async_mode='asgi')   # for socketio

sio.register_namespace(NoPrefixNamespace("/"))  # for socketio

# sio_asgi_app = socketio.ASGIApp(socketio_server=sio, other_asgi_app=app)    # for socketio
# sio_asgi_app = socketio.ASGIApp(sio, app, socketio_path="/api/socket.io")   # for socketio
# sio_asgi_app = socketio.ASGIApp(sio, app, socketio_path="/socket.io")   # for socketio
sio_asgi_app = socketio.ASGIApp(socketio_server=sio, other_asgi_app=app)
# sio.register_namespace(ws.ConnectNS('/'))   # for socketio
# app.mount("/socket.io", socketio.ASGIApp(sio))  # for socketio
app.add_route("/socket.io/", route=sio_asgi_app, methods=["GET", "POST"])   # for socketio
app.add_websocket_route("/socket.io/", sio_asgi_app)    # for socketio
@app.get("/hello")  # for socketio
async def root():
    await sio.emit("response", "hello everyone")
    return {"message": "hello"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port = os.environ["API_PORT"], reload=True, debug=True)