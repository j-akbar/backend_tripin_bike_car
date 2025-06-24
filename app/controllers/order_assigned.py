from typing import List
from datetime import datetime
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
# Load environment variables
API_HOST_OPENROUTE = os.getenv("API_HOST_OPENROUTE", "https://api.openrouteservice.org/v2")
API_KEY_OPENROUTE_1 = os.getenv("API_KEY_OPENROUTE_1", "5b3ce3597851110001cf62484b287f906b044a428c0c78eaa93d4785")
API_KEY_OPENROUTE_2 = os.getenv("API_KEY_OPENROUTE_2", "5b3ce3597851110001cf62480d243b5c45574f75b9111fc7a706b280")

# REDIS
REDIS_URI = os.getenv("REDIS_URI", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "123456")
SET_CACHE = os.getenv("SET_CACHE")

router = APIRouter()

# REDIS ACTION
def get_redis():
    return Redis(host=REDIS_URI, port=REDIS_PORT, db=2, decode_responses=True)


def set_status_nearest(param_assign, sts, db: Session = Depends(get_db)):
    # db: Session = Depends(get_db)
    # 0 = order no process, 1 = order near 0-5 minutes , 2 = order near 5-10 minutes, 3 = order near 10-30 minutes, 4 = order near than 30-120 minutes, 5 = order not assigned, 6 = state dan city tidak ditemukan, kesalahan query di cursor
    order_pickup = db.query(models.OrderPickup).filter(
    models.OrderPickup.id_user == param_assign.id_user
    ).first()
    if not order_pickup:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data order tidak ditemukan, status tidak bisa diset!")
    else:
        order_pickup.updated_on = datetime.now()
        order_pickup.status_nearest = sts

        # update status_nearest orders
        orders = db.query(models.Order).filter(
            models.Order.id_user == order_pickup.id_user
        ).all()
        for order in orders:
            order.status_nearest = sts
            order.updated_on = datetime.now()
        db.commit()
        return order_pickup


def response_for_pickup_nearest_driver(cursor, duration, redis: Redis = Depends(get_redis)):
    results = {
        "id_driver": cursor.id_driver,
        "id_user": cursor.id_user,
        "description": {
            "id": cursor.id,
            "id_driver": cursor.id_driver,
            "phone": cursor.phone,
            "name": cursor.name,
            # "place_id": cursor.place_id,
            # "place_type": cursor.place_type,
            # "place_key": cursor.place_key,
            # "place_value": cursor.place_value,
            # "lat": cursor.lat,
            # "lon": cursor.lon,
            "country_code": cursor.country_code,
            # "country_name": cursor.country_name,
            # "country_code_iso3": cursor.country_code_iso3,
            "region": cursor.region,
            "province": cursor.province,
            "city": cursor.city,
            "label": cursor.label,
            "sublabel": cursor.sublabel,
            "postcode": cursor.postcode,
            "district": cursor.district,
            "locality": cursor.locality,
            "place": cursor.place,
            "neighborhood": cursor.neighborhood,
            "address": cursor.address,
            "vehicle_type": cursor.vehicle_type,
            "vehicle_number": cursor.vehicle_number,
            # "priority": cursor.priority,
            "progress_order": cursor.progress_order,
            "active": cursor.active,
            # "last_active": cursor.last_active,
            # "daily_order_count": cursor.daily_order_count,
            # "daily_completed_count": cursor.daily_completed_count,
            # "daily_cancelled_count": cursor.daily_cancelled_count,
            "status": cursor.status,
            # "is_active": cursor.is_active,
            # "created_on": cursor.created_on,
            # "updated_on": cursor.updated_on,
            "id_user": cursor.id_user,
            "id_order": cursor.id_order,
            # "user_phone": cursor.user_phone,
            # "user_name": cursor. user_name,
            # "user_address": cursor.user_address,
            # "user_description": cursor.user_description,
            # "user_lon": cursor.lon,
            # "user_lat": cursor.user_lat,
            "waktu_jemput": duration[0],
            "status_nearest": cursor.status_nearest
        }
    }
    return results
    # set order ke redis karena tidak ada driver yang aktif/ belum dipickup driver
    # redis.set(f"op:{cursor.country_code.lower()}-id_driver:{cursor.id_driver}", json.dumps(results), ex=SET_CACHE)
    # return results

# def response_for_pickup_nearest_driver_status_6(param_assign, sts, db: Session = Depends(get_db)):
#     response_data = {
#         "status": 
#     }
#     return response_data



@router.post("/process-pickup-nearest-driver/", status_code=status.HTTP_200_OK, summary="Process get all nearest driver for pickup triggered by user")
def create_assign_order(param_assign: schemas.ProcessAssign, db: Session = Depends(get_db), redis: Redis = Depends(get_redis)):
    # Logic to create an assign order
    try:
        # check order apakah sudah di assign
        assigned_orders = db.execute(
            f"""SELECT DC.*, OA.waiting_time, OA.waktu_jemput, OA.waktu_antar
                FROM order_assigned OA
                JOIN driver_coords DC
                ON OA.id_driver = DC.id_driver
                WHERE OA.status=1 AND OA.is_active=1 AND DC.progress_order = 1
                AND OA.id_user={param_assign.id_user}"""
        ).first()
        if assigned_orders:
            db.commit()
            return assigned_orders
        else:
            # check data order pickup yang dibuat oleh user
            order_pickup = db.query(models.OrderPickup).filter(
            models.OrderPickup.id_user == param_assign.id_user,
            models.OrderPickup.status == 0,
            models.OrderPickup.id_driver == 0,  # Assuming 0 means no driver assigned
            models.OrderPickup.is_pickup == 0,  # Assuming 0 means not picked up yet
            models.OrderPickup.running == 0,    # Assuming 0 means not in progress
            models.OrderPickup.finished == 0,    # Assuming 0 means not finished
            models.OrderPickup.vehicle_type_ordered == param_assign.vehicle_type,
            models.OrderPickup.is_active == 1,  # Assuming 1 means active
            models.OrderPickup.country_code == param_assign.country_code,
            models.OrderPickup.region == param_assign.region
            ).first()
        if not order_pickup:
            db.commit()
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order pickup tidak ditemukan")
        else:
            # get nearest driver
            cursor = db.execute(
            f"""SELECT DC.*, 
                OP.id_user, OP.id_order, 
                OP.phone user_phone, OP.name user_name, OP.address user_address, OP.description user_description, OP.lon user_lon, OP.lat user_lat, OP.status_nearest 
                FROM order_pickup OP 
                JOIN driver_coords DC 
                ON OP.vehicle_type_ordered = DC.vehicle_type AND OP.country_code = DC.country_code AND OP.region = DC.region 
                WHERE OP.id_user = {order_pickup.id_user} AND OP.vehicle_type_ordered = {order_pickup.vehicle_type_ordered} AND 
                DC.status = 1 AND DC.active = 1 AND DC.progress_order = 0 AND
                DC.is_active = 1 AND 
                OP.country_code = '{order_pickup.country_code}' AND (OP.state = '{order_pickup.state}' OR OP.city = '{order_pickup.city}')
                ORDER BY DC.priority, DC.daily_order_count, DC.daily_cancelled_count ASC""").all()
            if not cursor:
                print(f"status param 5 ke 1 {param_assign}")
                set_sts_nearest_order = set_status_nearest(param_assign, 6, db)
                # response_data = response_for_pickup_nearest_driver_status_6(param_assign, 6, db)
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver tidak tersedia")
            else:
                jumlah_driver = [len(cursor),len(cursor)] # mendapatkan jumlah driver dihitung dari 0
                lon_lat_driver = [] # e.g: [['106.734242608533', '-6.31829872108153'], ['106.738404508861', '-6.2907219825044']]
                for row in cursor:
                    lon_lat_driver.append([row.lon, row.lat])
                lon_lat_driver.append([order_pickup.lon, order_pickup.lat]) # menambah destination pickup ke array log_lan_driver
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
                data = response.json()
                durations = data.get('durations', [])
                results = []    # untuk menampung order dengan "status_nearest" 3 sampai 6
                if response.status_code == 200:
                    if not durations or len(durations) == 0:
                        return {"status_code": status.HTTP_404_NOT_FOUND, "detail": "No durations found in the response"}
                    for i in range(len(durations)):
                        # print(f'duration {durations[i]}')
                        # print(f"Index: {i}, Value: {durations[i]}")
                        # print(f"Duration for driver {i}: {durations[i][0]} seconds")
                        if durations[i][0] > 0.0 and durations[i][0] <= 300.0:  # 0-5 minutes
                            # Create a new assignment for the driver
                            new_assignment = models.OrderAssigned(
                                id_order_pickup=order_pickup.id,
                                id_user=order_pickup.id_user,
                                id_driver=cursor[i].id_driver,
                                vehicle_type=param_assign.vehicle_type,
                                waktu_jemput=durations[i][0],
                                waktu_antar=order_pickup.waktu,
                                url=param_assign.url,  # URL for the latest location of the driver
                                status=1,  # 0 = new, 1 = in progress, 2 = completed, 3 = cancelled
                                is_active=1,  # 0 = tidak aktif, 1 = aktif
                                created_on=datetime.now()
                            )
                            db.add(new_assignment)
                            # update the order pickup with the assigned driver
                            order_pickup.updated_on = datetime.now()
                            order_pickup.status = 1  # 0 = new, 1 = in progress, 2 = completed, 3 = cancelled
                            order_pickup.id_driver = cursor[i].id_driver

                            # update the driver coordinates to set progress_order to 1
                            driver_coords = db.query(models.DriverCoords).filter(
                                models.DriverCoords.id_driver == cursor[i].id_driver,
                                # models.DriverCoords.place_id == driver_coords.place_id
                            ).first()
                            driver_coords.progress_order = 1

                            # update the driver daily order count
                            driver_coords.daily_order_count += 1

                            # update status orders
                            orders = db.query(models.Order).filter(
                                models.Order.id_user == order_pickup.id_user
                            ).all()
                            for order in orders:
                                order.status = 1
                                order.updated_on = datetime.now()
                                
                            db.commit()
                            response_data = response_for_pickup_nearest_driver(cursor[i], durations[i], redis)
                            results.append(response_data)
                            return response_data
                        elif durations[i][0] > 300.0 and durations[i][0] <= 600.0:  # 5-10 minutes
                            # print(f"Driver {i} has a duration of {durations[i][0]} seconds (5-10 minutes)")
                            # check if the driver is already assigned to this order
                            # check_assigned = db.query(models.OrderAssigned).filter(
                            #     models.OrderAssigned.id_user == order_pickup.id_user,
                            #     models.OrderAssigned.id_driver == cursor[i].id_driver,
                            #     models.OrderAssigned.status == 1,  # Assuming status 0 means 'new' or 'pending'
                            #     models.OrderAssigned.is_active == 1,  # Assuming 1 means active
                            # ).order_by(models.OrderAssigned.created_on.desc()
                            # ).all()
                            # for assignment in check_assigned:
                            #     db.delete(assignment)
                            # db.commit()
                            # Create a new assignment for the driver
                            new_assignment = models.OrderAssigned(
                                id_order_pickup=order_pickup.id,
                                id_user=order_pickup.id_user,
                                id_driver=cursor[i].id_driver,
                                waktu_jemput=durations[i][0],
                                waktu_antar=order_pickup.waktu,
                                status=1,  # 0 = new, 1 = in progress, 2 = completed, 3 = cancelled
                                is_active=1,  # 0 = tidak aktif, 1 = aktif
                                created_on=datetime.now()
                            )
                            db.add(new_assignment)
                            # update the order pickup with the assigned driver
                            order_pickup.updated_on = datetime.now()
                            order_pickup.status = 1  # Assuming 1 means 'in progress'
                            order_pickup.id_driver = cursor[i].id_driver

                            # update the driver coordinates to set progress_order to 1
                            driver_coords = db.query(models.DriverCoords).filter(
                                models.DriverCoords.id_driver == cursor[i].id_driver,
                                # models.DriverCoords.place_id == driver_coords.place_id
                            ).first()
                            driver_coords.progress_order = 1

                            # update the driver daily order count
                            driver_coords.daily_order_count += 1

                            # update status orders
                            orders = db.query(models.Order).filter(
                                models.Order.id_user == order_pickup.id_user
                            ).all()
                            for order in orders:
                                order.status = 1
                                order.updated_on = datetime.now()
                            db.commit()
                            response_data = response_for_pickup_nearest_driver(cursor[i], durations[i], redis)
                            results.append(response_data)
                            return response_data
                        elif durations[i][0] > 600.0 and durations[i][0] <= 1800.0: # 10-30 minutes
                            print(f"driver 10-30 minutes {param_assign}")
                            set_sts_nearest_order = set_status_nearest(param_assign, 3, db)
                            db.commit()
                            response_data = response_for_pickup_nearest_driver(cursor[i], durations[i], redis)
                            results.append(response_data)
                            # raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{set_sts_nearest_order}")
                        elif durations[i][0] > 1800.0 and durations[i][0] <= 7200.0: # 30-120 minutes
                            print(f"driver 30-120 minutes {param_assign}")
                            set_sts_nearest_order = set_status_nearest(param_assign, 4, db)
                            db.commit()
                            response_data = response_for_pickup_nearest_driver(cursor[i], durations[i], redis)
                            results.append(response_data)
                            # raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{set_sts_nearest_order}")
                        elif durations[i][0] > 7200.0: # diluar jangkauan driver
                            print(f"driver lebih dari 120 minutes {param_assign}")
                            set_sts_nearest_order = set_status_nearest(param_assign, 4, db)
                            db.commit()
                            response_data = response_for_pickup_nearest_driver(cursor[i], durations[i], redis)
                            results.append(response_data)
                    # return {"status_code": status.HTTP_200_OK, "detail": "Successfully fetched data from OpenRouteService"}
                    redis.set(f"op:{param_assign.country_code.lower()}-region:{param_assign.region.lower()}", json.dumps(results), ex=SET_CACHE)
                else:
                    print(f"status param 5 ke 2 {param_assign}")
                    # set_sts_nearest_order = set_status_nearest(param_assign, 5, db)
                    # response_data = response_for_pickup_nearest_driver(cursor[i], 0.0, redis)
                    # db.commit()
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver route tidak tersedia")
                    # return {"status_code": response.status_code, "detail": "Error fetching data from OpenRouteService"}
    except Exception as e:
        print(f"status param 5 ke 3 {param_assign}")
        # set_sts_nearest_order = set_status_nearest(param_assign, 5, db)
        # db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Terjadi kesalahan jaringan...")
        # raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{e} Proses assign sudah selesai, silahkan tunggu driver datang menjemput anda")

@router.get("/", status_code=status.HTTP_200_OK, summary="Get all assigned orders")
def get_assign_order(db: Session = Depends(get_db)):
    try:
        assigned_orders = db.query(models.OrderAssigned).all()
        return assigned_orders
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/get-assign-order-driver/{id_driver}/", status_code=status.HTTP_200_OK, summary="Get all assigned orders for a specific driver, trigered by driver")
def get_assign_order_driver(id_driver: int, db: Session = Depends(get_db)):
    try:
        assigned_orders = db.execute(
            f"""SELECT OP.*, OA.waktu_jemput, OA.waktu_antar
                FROM order_assigned OA
                JOIN order_pickup OP
                ON OA.id_order_pickup = OP.id
                WHERE OA.status=1 AND OA.is_active=1
                AND OA.id_driver={id_driver}"""
        ).first()
        if not assigned_orders:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No assigned orders found for this order pickup")
        else:
            return assigned_orders
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get("/get-assigned-driver/{id_user}/", status_code=status.HTTP_200_OK, summary="get the driver assigned to the order, trigered by user")
def get_assigned_driver(id_user: int, db: Session = Depends(get_db)):
    try:
        assigned_orders = db.execute(
            f"""SELECT DC.*, OA.waiting_time, OA.waktu_jemput, OA.waktu_antar
                FROM order_assigned OA
                JOIN driver_coords DC
                ON OA.id_driver = DC.id_driver
                WHERE OA.status=1 AND OA.is_active=1
                AND OA.id_user={id_user}"""
        ).first()
        if not assigned_orders:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No assigned orders found for this driver")
        else:
            # user_trip = db.execute(
            #     f"""SELECT DC.*, OA.waiting_time, OA.waktu_jemput, OA.waktu_antar
            #         FROM order_assigned OA
            #         JOIN driver_coords DC
            #         ON OA.id_driver = DC.id_driver
            #         WHERE OA.status=1 AND OA.is_active=1
            #         AND OA.id_user={id_user}"""
            # ).all()
            return assigned_orders
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.delete("/{id_user}/", status_code=status.HTTP_202_ACCEPTED, summary="Delete all order by id_user")
def delete_assign_order(id_user: int, db: Session = Depends(get_db)):
    try:
        # delete order_pickup by id_user
        order_pickup = db.query(models.OrderPickup).filter(models.OrderPickup.id_user == id_user).first()
        db.delete(order_pickup)

        # delete order_assigned
        assigned_orders = db.query(models.OrderAssigned).filter(models.OrderAssigned.id_user == id_user).first()
        db.delete(assigned_orders)

        # delete all order by id_user
        orders = db.query(models.Order).filter(models.Order.id_user == id_user).all()
        for order in orders:
            db.delete(order)

        # set status driver_coords
        driver_sts = db.query(models.DriverCoords).filter(
            models.DriverCoords.id_driver == order_pickup.id_driver,
            models.DriverCoords.vehicle_type == order_pickup.vehicle_type_ordered
            ).first()
        if driver_sts:
            driver_sts.progress_order = 0

        db.commit()
        return {"status_code": status.HTTP_202_ACCEPTED, "detail": "Successfully deleted all orders by id_user"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))