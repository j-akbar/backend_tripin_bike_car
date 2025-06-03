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
API_HOST_OPENROUTE = os.getenv("API_HOST_OPENROUTE", "https://api.openrouteservice.org/v2")
API_KEY_OPENROUTE_1 = os.getenv("API_KEY_OPENROUTE_1", "5b3ce3597851110001cf62484b287f906b044a428c0c78eaa93d4785")
API_KEY_OPENROUTE_2 = os.getenv("API_KEY_OPENROUTE_2", "5b3ce3597851110001cf62480d243b5c45574f75b9111fc7a706b280")

router = APIRouter()

@router.post("/", status_code=status.HTTP_200_OK, summary="Get all data for pickup from graphhopper")
def process_trip_bike_car(trip_bike_car: schemas.TripBikeCar, db: Session = Depends(get_db)):
    try:
        country_code = trip_bike_car.country_code
        region = trip_bike_car.region
        jarak_trip = trip_bike_car.jarak_trip
        waktu_trip = trip_bike_car.waktu_trip
        currency_price = db.query(models.CountryPrice).filter(models.CountryPrice.country_code == trip_bike_car.country_code).first()
        # https://api.openrouteservice.org/v2/directions/driving-car?api_key=5b3ce3597851110001cf62484b287f906b044a428c0c78eaa93d4785&start=106.73279441262972,-6.31250745&end=106.6525156,-6.1272786&language=id&avoid_features=ferries,tollways
        url = f"{API_HOST_OPENROUTE}/v2/directions/driving-car?api_key={API_KEY_OPENROUTE_1}&start={trip_bike_car.pickup_lon},{trip_bike_car.pickup_lat}&end={trip_bike_car.dropoff_lon},{trip_bike_car.dropoff_lat}&language=id&avoid_features=ferries,tollways"
        response = requests.get(url)
        print(url)
        response.raise_for_status()
        if response.status_code == 200:
            data = response.json()
            if 'features' in data and len(data['features']) > 0:
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
                features = data['features'][0]
                properties = features['properties']
                if 'segments' not in properties or len(properties['segments']) == 0:
                    return {"status_code": status.HTTP_404_NOT_FOUND, "detail": "No segments found in the response"}
                distance = properties['segments'][0].get('distance', 0)
                time = properties['segments'][0].get('duration', 0)
                return {
                    "country_code": country_code,
                    "region": region,
                    "distance_pickup": distance,
                    "time_to_pickup": time,
                    "type_trip": trip_bike_car.type_trip,
                    "jarak_trip": jarak_trip,
                    "waktu_trip": waktu_trip,
                    "currency_symbol": currency_price.currency_symbol,
                    "biaya": biaya,
                    "pickup_lat": trip_bike_car.pickup_lat,
                    "pickup_lon": trip_bike_car.pickup_lon,
                    "dropoff_lat": trip_bike_car.dropoff_lat,
                    "dropoff_lon": trip_bike_car.dropoff_lon,
                }
            else:
                return {"status_code": status.HTTP_404_NOT_FOUND, "detail": "No paths found"}
        else:
            return {"status_code": response.status_code, "detail": "Error fetching data from GraphHopper"}
        # data = response.json()
        # return data
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{e}")
    


@router.post("/{id_user}/{vehicle_type}/", status_code=status.HTTP_200_OK, summary="Create pickup order")
def create_pickup_order(id_user: int, vehicle_type: str, country_code: str, region: str, db: Session = Depends(get_db)):
    # Logic to create a pickup order
    try:
        order_pickup = db.query(models.OrderPickup).filter(
            models.OrderPickup.id_user == id_user,
            models.OrderPickup.status == 0,
            models.OrderPickup.id_driver == 0,  # Assuming 0 means no driver assigned
            models.OrderPickup.is_pickup == 0,  # Assuming 0 means not picked up yet
            models.OrderPickup.running == 0,    # Assuming 0 means not in progress
            models.OrderPickup.finished == 0,    # Assuming 0 means not finished
            models.OrderPickup.vehicle_type_ordered == vehicle_type,
            models.OrderPickup.is_active == 1,  # Assuming 1 means active
            ).first()
        if not order_pickup:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pickup order not found")
        else:
            cursor = db.execute(
            f"""SELECT DC.*, 
                OP.id_user, OP.id_order, 
                OP.phone user_phone, OP.name user_name, OP.address user_address, OP.description user_description, OP.lon user_lon, OP.lat user_lat 
                FROM order_pickup OP 
                JOIN driver_coords DC 
                ON OP.vehicle_type_ordered = DC.vehicle_type AND OP.country_code = DC.country_code AND OP.region = DC.region 
                WHERE OP.id_user = {order_pickup.id_user} AND OP.vehicle_type_ordered = {order_pickup.vehicle_type_ordered} AND 
                DC.status = 1 AND DC.active = 1 AND DC.progress_order = 0 AND
                DC.is_active = 1 AND 
                OP.country_code = '{order_pickup.country_code}' AND OP.region = '{order_pickup.region}' AND 
                OP.province = '{order_pickup.province}' AND 
                ( OP.postcode = '{order_pickup.postcode}' OR OP.city = '{order_pickup.city}' OR 
                OP.district = '{order_pickup.district}' OR OP.address = '{order_pickup.address}' OR 
                OP.neighborhood = '{order_pickup.neighborhood}' OR OP.locality = '{order_pickup.locality}' OR 
                OP.label = '{order_pickup.label}' OR OP.sublabel = '{order_pickup.sublabel}') 
                ORDER BY DC.priority, DC.daily_order_count, DC.daily_cancelled_count ASC""").all()
            if not cursor:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver coordinates not found")
            else:
                jumlah_driver = [len(cursor),len(cursor)] # mendapatkan jumlah driver dihitung dari 0
                lon_lat_driver = [] # e.g: [['106.734242608533', '-6.31829872108153'], ['106.738404508861', '-6.2907219825044']]
                for row in cursor:
                    lon_lat_driver.append([row.lon, row.lat])
                lon_lat_driver.append([order_pickup.lon, order_pickup.lat]) # menambah destination pickup ke array log_lan_driver
                # print(lon_lat_driver)
                # print(jumlah_driver)
                # Assuming order_pickup has the necessary attributes like lon and lat
                url = f"{API_HOST_OPENROUTE}/v2/matrix/driving-car"
                headers = {
                    "Content-Type": "application/json; charset=utf-8",
                    "Authorization": API_KEY_OPENROUTE_1
                    }
                body = {
                    "locations": lon_lat_driver,  # List of driver coordinates
                    "destinations": jumlah_driver,  # Only the last location is the destination (pickup location)
                    # "sources": [0],  # Only the first location is the source (driver)
                    "metrics": ["distance", "duration"],
                    "resolve_locations":"false",
                    "units":"m"
                }
                # print("Request Body:", json.dumps(body, indent=2))
                response = requests.post(url, headers=headers, json=body)
                # # response.raise_for_status()
                if response.status_code == 200:
                    data = response.json()
                    durations = data.get('durations', [])
                    if not durations or len(durations) == 0:
                        return {"status_code": status.HTTP_404_NOT_FOUND, "detail": "No durations found in the response"}
                    for i in range(len(durations)):
                        # print(f"Index: {i}, Value: {durations[i]}")
                        # print(f"Duration for driver {i}: {durations[i][0]} seconds")
                        if durations[i][0] > 0.0 and durations[i][0] <= 300.0:
                            # print(f"Driver {i} has a duration of {durations[i][0]} seconds (0-5 minutes)")
                            return cursor[i]
                            # break
                        elif durations[i][0] > 300.0 and durations[i][0] <= 600.0:
                            # print(f"Driver {i} has a duration of {durations[i][0]} seconds (5-10 minutes)")
                            return cursor[i]
                            # break
                        elif durations[i][0] > 600.0:
                            # print(f"Driver {i} has a duration of {durations[i][0]} seconds (more than 10 minutes)")
                            return cursor
                            # continue
                        # cursor.close()
                    # return {"status_code": status.HTTP_200_OK, "detail": "Successfully fetched data from OpenRouteService"}
                else:
                    return {"status_code": response.status_code, "detail": "Error fetching data from OpenRouteService"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))