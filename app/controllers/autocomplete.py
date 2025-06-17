from typing import List
from datetime import datetime
from sqlalchemy.orm import Session
from app.data.database import get_db
from app.data import schemas, models
from app.controllers.auth import PasswordHashing
from app.controllers.auth import jwt_auth_wrapper
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Optional
from redis import Redis
import requests
import json
import os
from dotenv import load_dotenv
load_dotenv()
# Load environment variables
API_AUTOCOMPLETE_PHOTON = os.getenv("API_AUTOCOMPLETE_PHOTON", "https://photon.komoot.io")
SET_CACHE = os.getenv("SET_CACHE")

router = APIRouter()

def get_redis():
    return Redis(host='localhost', port=6379, db=1)


def query_get(q):
    url = f"{API_AUTOCOMPLETE_PHOTON}/api/?q={q}&lang=en"
    response = requests.get(url)
    data = response.json()
    print(f"query_get {data}")
    return data

def query_get_lanlot(q,lat,lon):
    url = f"{API_AUTOCOMPLETE_PHOTON}/api/?q={q}&lat={lat}&lon={lon}&lang=en"    # /api/?q=berlin&lat=52.3879&lon=13.0582"
    response = requests.get(url)
    data = response.json()
    print(f"query_get_lanlot {data}")
    return data

def query_reverse(lat,lon):
    url = f"{API_AUTOCOMPLETE_PHOTON}/reverse?lon={lon}&lat={lat}&lang=en"
    response = requests.get(url)
    data = response.json()
    print(f"query_reverse {data}")
    return data


@router.post("/search/")
async def get_autocomplete(params: schemas.Autocomplete, redis: Redis = Depends(get_redis)):
    try:
        country_code = params.country_code
        q = params.q
        lat = params.lat
        lon = params.lon
        # cached_item = redis.get(f"item:{q}")
        if(country_code and q and not lat and not lon):
            cached_item = redis.get(f"autocomplete:{country_code}-{q}")
            if cached_item:
                print(f"data ada 1")
                return json.loads(cached_item)
            else:
                url = query_get(q)
                redis.set(f"autocomplete:{country_code}-{q}", json.dumps(url), ex=SET_CACHE)
                return url
            
        elif(country_code and q and lat and lon):
            cached_item = redis.get(f"autocomplete:{country_code}-{q}-{lat}-{lon}")
            if cached_item:
                print(f"data ada 2")
                return json.loads(cached_item)
            else:
                url = query_get(q,lat,lon)
                redis.set(f"autocomplete:{country_code}-{q}-{lat}-{lon}", json.dumps(url), ex=SET_CACHE)
                return url
            
        elif(country_code and not q and lat and lon):
            cached_item = redis.get(f"autocomplete:{country_code}-{lat}-{lon}")
            if cached_item:
                print(f"data ada 3")
                return json.loads(cached_item)
            else:
                url = query_reverse(lat,lon)
                redis.set(f"autocomplete:{country_code}-{lat}-{lon}", json.dumps(url), ex=SET_CACHE)
                return url

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))