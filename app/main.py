import uvicorn
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
    "http://localhost:5005",
    "http://localhost:3010",
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

include_routers(app)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port = os.environ["API_PORT"], reload=True, debug=True)