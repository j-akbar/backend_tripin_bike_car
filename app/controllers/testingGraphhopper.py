from typing import List
from datetime import datetime
from sqlalchemy.orm import Session
from app.data.database import get_db
from app.data import schemas, models
from app.controllers.auth import PasswordHashing
from app.controllers.auth import jwt_auth_wrapper
from fastapi import APIRouter, HTTPException, status, Depends
import requests
import json
import os
from dotenv import load_dotenv
load_dotenv()
# Load environment variables
API_GRAPHHOPPER = os.getenv("API_GRAPHHOPPER", "https://graphhopper.com")
API_KEY_GRAPHHOPPER = os.getenv("API_KEY_GRAPHHOPPER", "1b74b955-1173-4395-9dda-2c74bddc73d1")

router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED, summary="Get all data for pickup from graphhopper")
def process_trip_bike_car(trip_bike_car: schemas.TripBikeCar, db: Session = Depends(get_db)):
    try:
        country_code = trip_bike_car.country_code
        region = trip_bike_car.region
        jarak_trip = trip_bike_car.jarak_trip
        waktu_trip = trip_bike_car.waktu_trip
        # ascend_trip = trip_bike_car.ascend_trip
        # descend_trip = trip_bike_car.descend_trip
        currency_price = db.query(models.CountryPrice).filter(models.CountryPrice.country_code == trip_bike_car.country_code).first()
        url = f"{API_GRAPHHOPPER}/api/1/route?point={trip_bike_car.pickup_lat},{trip_bike_car.pickup_lon}&point={trip_bike_car.dropoff_lat},{trip_bike_car.dropoff_lon}&vehicle={trip_bike_car.vehicle_type}&key={API_KEY_GRAPHHOPPER}&locale=en&points_encoded=false&type=json&snap_prevention={trip_bike_car.snap_prevention}&lang=en"
        # url = f"https://graphhopper.com/api/1/route?point=-6.210148482848382,106.79987197635523&point=-6.2345080653981455,106.80183657789513&vehicle=car&key=1b74b955-1173-4395-9dda-2c74bddc73d1&type=json&points_encoded=false&snap_prevention=ferry"
        response = requests.get(url)
        print(url)
        response.raise_for_status()
        if response.status_code == 200:
            data = response.json()
            if 'paths' in data and len(data['paths']) > 0:
                biaya = 0
                if trip_bike_car.vehicle_type.lower() == 'bike':
                    if jarak_trip <= currency_price.bike_harga_meter_pertama:
                        biaya = currency_price.bike_harga_pertama
                    else:
                        biaya = currency_price.bike_harga_pertama + ((jarak_trip - currency_price.bike_harga_meter_pertama) / 1000) * currency_price.bike_harga_permeter
                elif trip_bike_car.vehicle_type.lower() == 'car':
                    if jarak_trip <= currency_price.car_harga_meter_pertama:
                        biaya = currency_price.car_harga_pertama
                    else:
                        biaya = currency_price.car_harga_pertama + ((jarak_trip - currency_price.car_harga_meter_pertama) / 1000) * currency_price.car_harga_permeter
                # elif trip_bike_car.vehicle_type.lower() == 'motorcycle':
                #     if distance <= currency_price.motorcycle_harga_meter_pertama:
                #         biaya = currency_price.motorcycle_harga_pertama
                #     else:
                #         biaya = currency_price.motorcycle_harga_pertama + ((distance - currency_price.motorcycle_harga_meter_pertama) / 1000) * currency_price.motorcycle_harga_per_meter
                path = data['paths'][0]
                distance = path.get('distance', 0)
                time = path.get('time', 0)
                # ascend = path.get('ascend', 0)
                # descend = path.get('descend', 0)
                return {
                    "status_code": status.HTTP_200_OK,
                    "data": {
                        "country_code": country_code,
                        "region": region,
                        "distance_driver": distance,
                        "time_driver": time,
                        # "ascend_driver": ascend,
                        # "descend_driver": descend,
                        "waktu_trip": waktu_trip,
                        # "ascend_trip": ascend_trip,
                        # "descend_trip": descend_trip,
                        "currency_symbol": currency_price.currency_symbol,
                        "biaya": biaya,
                        "pickup_lat": trip_bike_car.pickup_lat,
                        "pickup_lon": trip_bike_car.pickup_lon,
                        "dropoff_lat": trip_bike_car.dropoff_lat,
                        "dropoff_lon": trip_bike_car.dropoff_lon,
                    }
                }
            else:
                return {"status_code": status.HTTP_404_NOT_FOUND, "detail": "No paths found"}
        else:
            return {"status_code": response.status_code, "detail": "Error fetching data from GraphHopper"}
        # data = response.json()
        # return data
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{e}")