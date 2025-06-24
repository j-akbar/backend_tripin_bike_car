# from typing import List
# from datetime import datetime
# from sqlalchemy.orm import Session
from app.data.database import get_db
from app.data import schemas, models
# from app.controllers.auth import PasswordHashing
# from app.controllers.auth import jwt_auth_wrapper
from fastapi import APIRouter, HTTPException, status, Depends
# from typing import Optional
from urllib.parse import quote
from redis import Redis
import requests
import json
import os
from dotenv import load_dotenv
load_dotenv()
# Load environment variables
API_AUTOCOMPLETE_PHOTON = os.getenv("API_AUTOCOMPLETE_PHOTON", "https://photon.komoot.io")
SET_CACHE = os.getenv("SET_CACHE")
# REDIS
REDIS_URI = os.getenv("REDIS_URI", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "123456")

router = APIRouter()

# REDIS ACTION
def get_redis():
    return Redis(host=REDIS_URI, port=REDIS_PORT, db=1, decode_responses=True)

# REVERSE FROM RESPONSE
def reverse_name_words(name):
    words = name.split()  # Split the name into a list of words
    reversed_words = words[::-1]  # Reverse the list of words
    return " ".join(reversed_words) # Join the reversed words back into a string

def get_state(state):
    if(state):
        state_name = state
        if state == "North Jakarta":
            state_name = "Jakarta Utara"
        elif state == "South Jakarta":
            state_name = "Jakarta Selatan"
        elif state == "East Jakarta":
            state_name = "Jakarta Timur"
        elif state == "West Jakarta":
            state_name = "Jakarta Barat"
        else:
            state_name = state.replace('North', 'Utara').replace('South', 'Selatan').replace('East', 'Timur').replace('West', 'Barat').replace('Java', 'Jawa')
        reversed_state_name = reverse_name_words(state_name)
        return reversed_state_name
    else: return ''

def get_city(city):
    if(city):
        city_name = city
        if city == "North Jakarta":
            city_name = "Jakarta Utara"
        elif city == "South Jakarta":
            city_name = "Jakarta Selatan"
        elif city == "East Jakarta":
            city_name = "Jakarta Timur"
        elif city == "West Jakarta":
            city_name = "Jakarta Barat"
        else:
            city_name = city.replace('North', 'Utara').replace('South', 'Selatan').replace('East', 'Timur').replace('West', 'Barat').replace('Java', 'Jawa')
        reversed_city_name = reverse_name_words(city_name)
        return reversed_city_name
    else: return ''

def get_name(name):
    if(name):
        transl_name = name
        if name == "Outer Ring Road":
            transl_name = "Jalan Lingkar Luar"
        elif name == "North Jakarta":
            transl_name = "Jakarta Utara"
        elif name == "South Jakarta":
            transl_name = "Jakarta Selatan"
        elif name == "East Jakarta":
            transl_name = "Jakarta Timur"
        elif name == "West Jakarta":
            transl_name = "Jakarta Barat"
        else:
            transl_name = name.replace('Outer', 'Luar').replace('Ring', 'Lingkar').replace('Road', 'Jalan').replace('North', 'Utara').replace('South', 'Selatan').replace('East', 'Timur').replace('West', 'Barat').replace('Java', 'Jawa')
        return transl_name
    else: return ''


def query_get(q):
    url = f"{API_AUTOCOMPLETE_PHOTON}/api/?q={q}&lang=en"
    response = requests.get(url)
    data = response.json()
    # print(f"query_get {data}")
    return data

def query_get_lanlot(q,lat,lon):
    url = f"{API_AUTOCOMPLETE_PHOTON}/api/?q={q}&lat={lat}&lon={lon}&lang=en"    # /api/?q=berlin&lat=52.3879&lon=13.0582"
    response = requests.get(url)
    data = response.json()
    # print(f"query_get_lanlot {data}")
    return data

# def query_get_state_city(state,city):
#     new_q = quote(f"{state} {city}")
#     url = f"{API_AUTOCOMPLETE_PHOTON}/api/?q={new_q}&lang=en"    # /api/?q=berlin%20lux&lat=52.3879&lon=13.0582"
#     response = requests.get(url)
#     data = response.json()
#     # print(f"query_get_lanlot {data}")
#     return data

def query_reverse(lat,lon):
    url = f"{API_AUTOCOMPLETE_PHOTON}/reverse?lon={lon}&lat={lat}&lang=en&limit=1"
    response = requests.get(url)
    data = response.json()
    # print(f"query_reverse {data}")
    return data


@router.post("/search/")
async def get_autocomplete(params: schemas.Autocomplete, redis: Redis = Depends(get_redis)):
    try:
        country_code = params.country_code
        q = params.q
        lat = params.lat
        lon = params.lon
        # cached_item = redis.get(f"item:{q}")
        if(country_code and q and not lat and not lon):  # jika !latlon
            cached_item = redis.get(f"ac:{country_code.lower()}-q:{q.lower()}")
            if cached_item:
                return json.loads(cached_item)
            else:
                url = query_get(q)
                feature_datas = url.get('features', [])
                results = []
                for features in feature_datas:
                    state_indo_lang = get_state(features.get("properties").get("state"))
                    city_indo_lang = get_city(features.get("properties").get("city"))
                    name_indo_lang = get_name(features.get("properties").get("name"))

                    results.append({
                        "types": "Feature",
                        "properties": {
                            "type": f"{features.get("properties").get("type")}", # house, street, city
                            "place": f"{features.get("properties").get("place") or ''}",
                            "street": f"{features.get("properties").get("street") or ''}",
                            "housenumber": f"{features.get("properties").get("housenumber") or ''}",
                            "streetnumber": f"{features.get("properties").get("streetnumber") or ''}",
                            "city": f"{city_indo_lang or ''}",
                            "district": f"{features.get("properties").get("district") or ''}",
                            "county": f"{features.get("properties").get("county") or ''}",
                            "state": f"{state_indo_lang or ''}",
                            "locality": f"{features.get("properties").get("locality") or ''}",
                            "postcode": f"{features.get("properties").get("postcode") or ''}",
                            "country": f"{features.get("properties").get("country") or ''}",
                            "countrycode": f"{features.get("properties").get("countrycode")}",
                            "osm_key": f"{features.get("properties").get("osm_key")}",
                            "osm_value": f"{features.get("properties").get("osm_value")}",
                            "osm_type": f"{features.get("properties").get("osm_type")}",
                            "osm_id": f"{features.get("properties").get("osm_id")}",
                            "name": f"{name_indo_lang}",
                            "extent": features.get("properties").get("extent", [])
                        },
                        "geometry": {
                            "type": f"{features.get("geometry").get("type")}",
                            "coordinates": features.get("geometry").get("coordinates", []),
                        }
                    })
                redis.set(f"ac:{country_code.lower()}-q:{q.lower()}", json.dumps(results), ex=SET_CACHE)
                return results
            
        elif(country_code and q and lat and lon): # semua data lengkap
            new_lat = round(lat, 0)
            new_lon = round(lon, 0)
            cached_item = redis.get(f"ac:{country_code.lower()}-q:{q.lower()}-lat:{new_lat}-lon:{new_lon}")
            if cached_item:
                return json.loads(cached_item)
            else:
                url = query_get_lanlot(q,lat,lon)
                feature_datas = url.get('features', [])
                results = []
                for features in feature_datas:
                    state_indo_lang = get_state(features.get("properties").get("state"))
                    city_indo_lang = get_city(features.get("properties").get("city"))
                    name_indo_lang = get_name(features.get("properties").get("name"))

                    results.append({
                        "types": "Feature",
                        "properties": {
                            "type": f"{features.get("properties").get("type")}", # house, street, city
                            "place": f"{features.get("properties").get("place") or ''}",
                            "street": f"{features.get("properties").get("street") or ''}",
                            "housenumber": f"{features.get("properties").get("housenumber") or ''}",
                            "streetnumber": f"{features.get("properties").get("streetnumber") or ''}",
                            "city": f"{city_indo_lang or ''}",
                            "district": f"{features.get("properties").get("district") or ''}",
                            "county": f"{features.get("properties").get("county") or ''}",
                            "state": f"{state_indo_lang or ''}",
                            "locality": f"{features.get("properties").get("locality") or ''}",
                            "postcode": f"{features.get("properties").get("postcode") or ''}",
                            "country": f"{features.get("properties").get("country") or ''}",
                            "countrycode": f"{features.get("properties").get("countrycode")}",
                            "osm_key": f"{features.get("properties").get("osm_key")}",
                            "osm_value": f"{features.get("properties").get("osm_value")}",
                            "osm_type": f"{features.get("properties").get("osm_type")}",
                            "osm_id": f"{features.get("properties").get("osm_id")}",
                            "name": f"{name_indo_lang}",
                            "extent": features.get("properties").get("extent", [])
                        },
                        "geometry": {
                            "type": f"{features.get("geometry").get("type")}",
                            "coordinates": features.get("geometry").get("coordinates", []),
                        }
                    })
                redis.set(f"ac:{country_code.lower()}-q:{q.lower()}-lat:{new_lat}-lon:{new_lon}", json.dumps(results), ex=SET_CACHE)
                return results
            
        elif(country_code and not q and lat and lon):    # jika hanya latlon
            # new_lat = round(lat, 0)
            # new_lon = round(lon, 0)
            # cached_item = redis.get(f"autocomplete:{country_code}-{new_lat}-{new_lon}")
            # if cached_item:
            #     return json.loads(cached_item)
            # else:
                print("masuk kesini")
                url = query_reverse(lat,lon)
                feature_datas = url.get('features', [])
                results = []
                for features in feature_datas:
                    state_indo_lang = get_state(features.get("properties").get("state"))
                    city_indo_lang = get_city(features.get("properties").get("city"))
                    name_indo_lang = get_name(features.get("properties").get("name"))

                    results.append({
                        "types": "Feature",
                        "properties": {
                            "type": f"{features.get("properties").get("type")}", # house, street, city
                            "place": f"{features.get("properties").get("place") or ''}",
                            "street": f"{features.get("properties").get("street") or ''}",
                            "housenumber": f"{features.get("properties").get("housenumber") or ''}",
                            "streetnumber": f"{features.get("properties").get("streetnumber") or ''}",
                            "city": f"{city_indo_lang or ''}",
                            "district": f"{features.get("properties").get("district") or ''}",
                            "county": f"{features.get("properties").get("county") or ''}",
                            "state": f"{state_indo_lang or ''}",
                            "locality": f"{features.get("properties").get("locality") or ''}",
                            "postcode": f"{features.get("properties").get("postcode") or ''}",
                            "country": f"{features.get("properties").get("country") or ''}",
                            "countrycode": f"{features.get("properties").get("countrycode")}",
                            "osm_key": f"{features.get("properties").get("osm_key")}",
                            "osm_value": f"{features.get("properties").get("osm_value")}",
                            "osm_type": f"{features.get("properties").get("osm_type")}",
                            "osm_id": f"{features.get("properties").get("osm_id")}",
                            "name": f"{name_indo_lang}",
                            "extent": features.get("properties").get("extent", [])
                        },
                        "geometry": {
                            "type": f"{features.get("geometry").get("type")}",
                            "coordinates": features.get("geometry").get("coordinates", []),
                        }
                    })
                # redis.set(f"autocomplete:{country_code}-{new_lat}-{new_lon}", json.dumps(results), ex=SET_CACHE)
                return results

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# BACKUP (terlalu rumit)
# async def get_autocomplete(params: schemas.Autocomplete, redis: Redis = Depends(get_redis)):
#     try:
#         country_code = params.country_code
#         q = params.q
#         state = params.state
#         city = params.city
#         lat = params.lat
#         lon = params.lon
#         # cached_item = redis.get(f"item:{q}")
#         if(country_code and q and state and city and not lat and not lon):  # jika !latlon
#             cached_item = redis.get(f"autocomplete:{country_code.lower()}-{state.lower()}-{city.lower()}-{q.lower()}")
#             if cached_item:
#                 return json.loads(cached_item)
#             else:
#                 url = query_get(q)
#                 feature_datas = url.get('features', [])
#                 results = []
#                 for features in feature_datas:
#                     results.append({
#                         "types": "Feature",
#                         "properties": {
#                             "type": f"{features.get("properties").get("type")}", # house, street, city
#                             "place": f"{features.get("properties").get("place") or ''}",
#                             "street": f"{features.get("properties").get("street") or ''}",
#                             "housenumber": f"{features.get("properties").get("housenumber") or ''}",
#                             "streetnumber": f"{features.get("properties").get("streetnumber") or ''}",
#                             "city": f"{features.get("properties").get("city") or ''}",
#                             "district": f"{features.get("properties").get("district") or ''}",
#                             "county": f"{features.get("properties").get("county") or ''}",
#                             "state": f"{features.get("properties").get("state") or ''}",
#                             "locality": f"{features.get("properties").get("locality") or ''}",
#                             "postcode": f"{features.get("properties").get("postcode") or ''}",
#                             "country": f"{features.get("properties").get("country") or ''}",
#                             "countrycode": f"{features.get("properties").get("countrycode")}",
#                             "osm_key": f"{features.get("properties").get("osm_key")}",
#                             "osm_value": f"{features.get("properties").get("osm_value")}",
#                             "osm_type": f"{features.get("properties").get("osm_type")}",
#                             "osm_id": f"{features.get("properties").get("osm_id")}",
#                             "name": f"{features.get("properties").get("name")}",
#                             "extent": features.get("properties").get("extent", [])
#                         },
#                         "geometry": {
#                             "type": f"{features.get("geometry").get("type")}",
#                             "coordinates": features.get("geometry").get("coordinates", []),
#                         }
#                     })
#                 redis.set(f"autocomplete:{country_code.lower()}-{state.lower()}-{city.lower()}-{q.lower()}", json.dumps(results), ex=SET_CACHE)
#                 return results
            
#         elif(country_code and q and state and city and lat and lon): # semua data lengkap
#             new_lat = round(lat, 0)
#             new_lon = round(lon, 0)
#             cached_item = redis.get(f"autocomplete:{country_code.lower()}-{state.lower()}-{city.lower()}-{q.lower()}-{new_lat}-{new_lon}")
#             if cached_item:
#                 return json.loads(cached_item)
#             else:
#                 url = query_get_lanlot(q,lat,lon)
#                 feature_datas = url.get('features', [])
#                 results = []
#                 for features in feature_datas:
#                     results.append({
#                         "types": "Feature",
#                         "properties": {
#                             "type": f"{features.get("properties").get("type")}", # house, street, city
#                             "place": f"{features.get("properties").get("place") or ''}",
#                             "street": f"{features.get("properties").get("street") or ''}",
#                             "housenumber": f"{features.get("properties").get("housenumber") or ''}",
#                             "streetnumber": f"{features.get("properties").get("streetnumber") or ''}",
#                             "city": f"{features.get("properties").get("city") or ''}",
#                             "district": f"{features.get("properties").get("district") or ''}",
#                             "county": f"{features.get("properties").get("county") or ''}",
#                             "state": f"{features.get("properties").get("state") or ''}",
#                             "locality": f"{features.get("properties").get("locality") or ''}",
#                             "postcode": f"{features.get("properties").get("postcode") or ''}",
#                             "country": f"{features.get("properties").get("country") or ''}",
#                             "countrycode": f"{features.get("properties").get("countrycode")}",
#                             "osm_key": f"{features.get("properties").get("osm_key")}",
#                             "osm_value": f"{features.get("properties").get("osm_value")}",
#                             "osm_type": f"{features.get("properties").get("osm_type")}",
#                             "osm_id": f"{features.get("properties").get("osm_id")}",
#                             "name": f"{features.get("properties").get("name")}",
#                             "extent": features.get("properties").get("extent", [])
#                         },
#                         "geometry": {
#                             "type": f"{features.get("geometry").get("type")}",
#                             "coordinates": features.get("geometry").get("coordinates", []),
#                         }
#                     })
#                 redis.set(f"autocomplete:{country_code.lower()}-{state.lower()}-{city.lower()}-{q.lower()}-{new_lat}-{new_lon}", json.dumps(results), ex=SET_CACHE)
#                 return results
            
#         elif(country_code and not q and state and city and not lat and not lon):    # jika hanya state dan city
#             # tanda baru edit
#             cached_item = redis.get(f"autocomplete:{country_code.lower()}-{state.lower()}-{city.lower()}")
#             if cached_item:
#                 return json.loads(cached_item)
#             else:
#                 url = query_get_state_city(state,city)
#                 feature_datas = url.get('features', [])
#                 results = []
#                 for features in feature_datas:
#                     results.append({
#                         "types": "Feature",
#                         "properties": {
#                             "type": f"{features.get("properties").get("type")}", # house, street, city
#                             "place": f"{features.get("properties").get("place") or ''}",
#                             "street": f"{features.get("properties").get("street") or ''}",
#                             "housenumber": f"{features.get("properties").get("housenumber") or ''}",
#                             "streetnumber": f"{features.get("properties").get("streetnumber") or ''}",
#                             "city": f"{features.get("properties").get("city") or ''}",
#                             "district": f"{features.get("properties").get("district") or ''}",
#                             "county": f"{features.get("properties").get("county") or ''}",
#                             "state": f"{features.get("properties").get("state") or ''}",
#                             "locality": f"{features.get("properties").get("locality") or ''}",
#                             "postcode": f"{features.get("properties").get("postcode") or ''}",
#                             "country": f"{features.get("properties").get("country") or ''}",
#                             "countrycode": f"{features.get("properties").get("countrycode")}",
#                             "osm_key": f"{features.get("properties").get("osm_key")}",
#                             "osm_value": f"{features.get("properties").get("osm_value")}",
#                             "osm_type": f"{features.get("properties").get("osm_type")}",
#                             "osm_id": f"{features.get("properties").get("osm_id")}",
#                             "name": f"{features.get("properties").get("name")}",
#                             "extent": features.get("properties").get("extent", [])
#                         },
#                         "geometry": {
#                             "type": f"{features.get("geometry").get("type")}",
#                             "coordinates": features.get("geometry").get("coordinates", []),
#                         }
#                     })
#                 redis.set(f"autocomplete:{country_code.lower()}-{state.lower()}-{city.lower()}", json.dumps(results), ex=SET_CACHE)
#                 return results
            
#         elif(country_code and not q and not state and not city and lat and lon):    # jika hanya latlon
#             # new_lat = lat # round(lat, 5)
#             # new_lon = lon # round(lon, 5)
#             # cached_item = redis.get(f"autocomplete:{country_code}-{new_lat}-{new_lon}")
#             # if cached_item:
#             #     return json.loads(cached_item)
#             # else:
#                 url = query_reverse(lat,lon)
#                 feature_datas = url.get('features', [])
#                 results = []
#                 for features in feature_datas:
#                     results.append({
#                         "types": "Feature",
#                         "properties": {
#                             "type": f"{features.get("properties").get("type")}", # house, street, city
#                             "place": f"{features.get("properties").get("place") or ''}",
#                             "street": f"{features.get("properties").get("street") or ''}",
#                             "housenumber": f"{features.get("properties").get("housenumber") or ''}",
#                             "streetnumber": f"{features.get("properties").get("streetnumber") or ''}",
#                             "city": f"{features.get("properties").get("city") or ''}",
#                             "district": f"{features.get("properties").get("district") or ''}",
#                             "county": f"{features.get("properties").get("county") or ''}",
#                             "state": f"{features.get("properties").get("state") or ''}",
#                             "locality": f"{features.get("properties").get("locality") or ''}",
#                             "postcode": f"{features.get("properties").get("postcode") or ''}",
#                             "country": f"{features.get("properties").get("country") or ''}",
#                             "countrycode": f"{features.get("properties").get("countrycode")}",
#                             "osm_key": f"{features.get("properties").get("osm_key")}",
#                             "osm_value": f"{features.get("properties").get("osm_value")}",
#                             "osm_type": f"{features.get("properties").get("osm_type")}",
#                             "osm_id": f"{features.get("properties").get("osm_id")}",
#                             "name": f"{features.get("properties").get("name")}",
#                             "extent": features.get("properties").get("extent", [])
#                         },
#                         "geometry": {
#                             "type": f"{features.get("geometry").get("type")}",
#                             "coordinates": features.get("geometry").get("coordinates", []),
#                         }
#                     })
#                 # redis.set(f"autocomplete:{country_code}-{new_lat}-{new_lon}", json.dumps(results), ex=SET_CACHE)
#                 return results

#     except Exception as e:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))