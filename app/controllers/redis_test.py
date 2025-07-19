from typing import List
from datetime import datetime
from django import db
from sqlalchemy.orm import Session
from app.data.database import get_db
from app.data import schemas, models
from app.controllers.auth import PasswordHashing
from app.controllers.auth import jwt_auth_wrapper
from fastapi import APIRouter, HTTPException, status, Depends
from redis import Redis
import requests
import json
import os
from dotenv import load_dotenv
load_dotenv()

# REDIS
REDIS_URI = os.getenv("REDIS_URI", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "123456")
SET_CACHE = os.getenv("SET_CACHE")

router = APIRouter()

# REDIS ACTION
def get_redis():
    return Redis(host=REDIS_URI, port=REDIS_PORT, db=2, decode_responses=True)

@router.post("/redis-test", status_code=status.HTTP_200_OK, summary="Test Redis connection")
async def get_hanging_order(param_assign: schemas.HangingOrder, db: Session = Depends(get_db), redis: Redis = Depends(get_redis)):
    try:
        # redis_client = Redis(host=REDIS_URI, port=REDIS_PORT, password=REDIS_PASSWORD)
        cached_item = redis.hgetall(f"{param_assign.country_code.lower()}:{param_assign.region.lower()}")
        if cached_item:
            # data = json.loads(cached_item)
            json_data = json.dumps(cached_item)
            json_load = json.loads(json_data)
            return json_load
        else:
            # response = requests.get(
            #     f"{API_HOST_OPENROUTE}/geocode/search",
            #     params={
            #         "api_key": API_KEY_OPENROUTE_1,
            #         "country": country_code,
            #         "text": q
            #     }
            # )
            # if response.status_code == 200:
            #     data = response.json()
            #     redis.set(f"{country_code.lower()}:{q.lower()}", json.dumps(data), ex=3600)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"error")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Redis connection failed: {str(e)}")