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


def response_for_pickup_nearest_mitra(cursor, duration, waktu_antar, jarak_antar, id_assigned, db: Session = Depends(get_db)):
    kode_negara = cursor.country_code.upper()
    country_price = db.query(models.CountryPrice).filter(models.CountryPrice.country_code == kode_negara).first()
    biaya = 0
    if(cursor.vehicle_type == 0 and jarak_antar > 0):
        if(jarak_antar <= country_price.bike_harga_meter_pertama):
            biaya = country_price.bike_harga_pertama
        elif(jarak_antar > country_price.bike_harga_meter_pertama):
            jarak_antar = jarak_antar - country_price.bike_harga_meter_pertama
            biaya = country_price.bike_harga_pertama + ((jarak_antar / 1000) * country_price.bike_harga_permeter)
    elif(cursor.vehicle_type == 1 and jarak_antar > 0):
        if(jarak_antar <= country_price.car_harga_meter_pertama):
            biaya = country_price.car_harga_pertama
        elif(jarak_antar > country_price.car_harga_meter_pertama):
            jarak_antar = jarak_antar - country_price.car_harga_meter_pertama
            biaya = country_price.car_harga_pertama + ((jarak_antar / 1000) * country_price.car_harga_permeter)
    results = {
        "id_mitra": cursor.id_mitra,
        "id_user": cursor.id_user,
        "description": {
            "id": cursor.id,
            "id_mitra": cursor.id_mitra,
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
            "user_lon": cursor.user_lon if cursor.user_lon else 0.0,
            "user_lat": cursor.user_lat if cursor.user_lat else 0.0,
            "id_assigned": id_assigned if id_assigned else '',
            "waktu_jemput": duration,
            "jarak_antar": jarak_antar if jarak_antar else 0,
            "waktu_antar": waktu_antar if waktu_antar else 0,
            "status_nearest": cursor.status_nearest,
            "biaya": biaya
        }
    }
    return results
    # set order ke redis karena tidak ada mitra yang aktif/ belum dipickup mitra
    # redis.set(f"op:{cursor.country_code.lower()}-id_mitra:{cursor.id_mitra}", json.dumps(results), ex=SET_CACHE)
    # return results

# def response_for_pickup_nearest_mitra_status_6(param_assign, sts, db: Session = Depends(get_db)):
#     response_data = {
#         "status": 
#     }
#     return response_data


def empty_assignment_order(order_pickup, param_assign, db: Session = Depends(get_db)):
    try:
        order_assignment = db.query(models.OrderAssigned).filter(
            models.OrderAssigned.id_user == param_assign.id_user,
            models.OrderAssigned.status != 0,
            models.OrderAssigned.is_active != 0
        ).first()
        if order_assignment:
            order_assignment.is_active = 0
            order_assignment.status = 0   
        
        # create new empty assignment order
        empty_assignment = models.OrderAssigned(
            id_order_pickup=order_pickup.id,
            id_user=order_pickup.id_user,
            id_mitra=0,  # 0 means no mitra assigned
            vehicle_type=param_assign.vehicle_type,
            waiting_time=0.0,  # waktu tunggu mitra pickup customer
            jarak_antar=order_pickup.jarak,
            waktu_antar=order_pickup.waktu,
            url=param_assign.url,  # URL for the latest location of the mitra
            status=5,  # 0 = new, 1 = in progress, 2 = completed, 3 = cancelled, 4 = pending, 5 = not assigned
            is_active=1,  # 0 = tidak aktif, 1 = aktif
            created_on=datetime.now()
        )
        db.add(empty_assignment)
        db.commit()
        return empty_assignment
    except Exception as e:
        print(f"Error creating empty assignment order: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create empty assignment order")


@router.post("/process-pickup-nearest-mitra/", status_code=status.HTTP_200_OK, summary="Process get all nearest mitra for pickup triggered by user")
def create_assign_order(param_assign: schemas.ProcessAssign, db: Session = Depends(get_db), redis: Redis = Depends(get_redis), payload=Depends(jwt_auth_wrapper)):
    # Logic to create an assign order
    try:
        # check order apakah sudah di assign
        assigned_orders = db.execute(
            f"""SELECT DC.*, OA.id id_assigned, OA.id_order_pickup id_order, OA.id_user, OA.waiting_time, OA.waktu_jemput, OA.jarak_antar, OA.waktu_antar, OP.status_nearest,
            OP.lon user_lon, OP.lat user_lat     
                FROM order_assigned OA
                JOIN mitra_coords DC
                ON OA.id_mitra = DC.id_mitra
                JOIN order_pickup OP
                ON OA.id_order_pickup = OP.id
                WHERE OA.status=1 AND OA.is_active=1 AND DC.progress_order = 1 AND DC.id_layanan = 1 
                AND OA.id_user={param_assign.id_user}"""
        ).first()
        if assigned_orders:
            db.commit()
            response_data = response_for_pickup_nearest_mitra(assigned_orders, assigned_orders.waktu_jemput, assigned_orders.waktu_antar, assigned_orders.jarak_antar, assigned_orders.id_assigned, db)
            print(f"assigned_orders: {response_data}")
            return response_data
        else:
            # check data order pickup yang dibuat oleh user
            order_pickup = db.query(models.OrderPickup).filter(
            models.OrderPickup.id_user == param_assign.id_user,
            models.OrderPickup.status == 0,
            models.OrderPickup.id_mitra == 0,  # Assuming 0 means no mitra assigned
            models.OrderPickup.is_pickup == 0,  # Assuming 0 means not picked up yet
            models.OrderPickup.running == 0,    # Assuming 0 means not in progress
            models.OrderPickup.finished == 0,    # Assuming 0 means not finished
            models.OrderPickup.vehicle_type_ordered == param_assign.vehicle_type,
            models.OrderPickup.is_active == 1,  # Assuming 1 means active
            models.OrderPickup.country_code == param_assign.country_code,
            models.OrderPickup.region == param_assign.region
            ).first()
            if not order_pickup:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order pickup tidak ditemukan")
            else:
                # get nearest mitra
                cursor = db.execute(
                f"""SELECT DC.*, 
                    OP.id_user, OP.id_order, 
                    OP.phone user_phone, OP.name user_name, OP.address user_address, OP.description user_description, OP.lon user_lon, OP.lat user_lat, OP.status_nearest, OP.waktu, OP.jarak 
                    FROM order_pickup OP 
                    JOIN mitra_coords DC 
                    ON OP.vehicle_type_ordered = DC.vehicle_type AND OP.country_code = DC.country_code 
                    WHERE OP.id_user = {order_pickup.id_user} AND OP.vehicle_type_ordered = {order_pickup.vehicle_type_ordered} AND 
                    DC.status = 1 AND DC.active = 1 AND DC.progress_order = 0 AND DC.id_layanan = 1 AND 
                    DC.is_active = 1 
                    ORDER BY DC.priority, DC.daily_order_count, DC.daily_cancelled_count ASC""").all()
                if not cursor:
                    print(f"status param 5 ke 1 {param_assign}")
                    set_sts_nearest_order = set_status_nearest(param_assign, 6, db)
                    empty_assignment = empty_assignment_order(order_pickup, param_assign, db)
                    # response_data = response_for_pickup_nearest_mitra_status_6(param_assign, 6, db)
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mitra tidak tersedia")
                else:
                    jumlah_mitra = [len(cursor),len(cursor)] # mendapatkan jumlah mitra dihitung dari 0
                    lon_lat_mitra = [] # e.g: [['106.734242608533', '-6.31829872108153'], ['106.738404508861', '-6.2907219825044']]
                    for row in cursor:
                        lon_lat_mitra.append([row.lon, row.lat])
                    lon_lat_mitra.append([order_pickup.lon, order_pickup.lat]) # menambah destination pickup ke array log_lan_mitra
                    # Assuming order_pickup has the necessary attributes like lon and lat
                    url = f"{API_HOST_OPENROUTE}/v2/matrix/driving-car"
                    headers = {
                        "Content-Type": "application/json; charset=utf-8",
                        "Authorization": API_KEY_OPENROUTE_1
                        }
                    body = {
                        "locations": lon_lat_mitra,  # List of mitra coordinates
                        "destinations": jumlah_mitra,  # Only the last location is the destination (pickup location)
                        # "sources": [0],  # Only the first location is the source (mitra)
                        "metrics": ["distance", "duration"],
                        "resolve_locations":"false",
                        "units":"m"
                    }
                    # print("Request Body:", json.dumps(body, indent=2))
                    response = requests.post(url, headers=headers, json=body)
                    # # response.raise_for_status()
                    data = response.json()
                    durations = data.get('durations', [])
                    if response.status_code == 200:
                        results = []    # untuk menampung order dengan "status_nearest" 3 sampai 6
                        if not durations or len(durations) == 0:
                            return {"status_code": status.HTTP_404_NOT_FOUND, "detail": "No durations found in the response"}
                        for i in range(len(durations)):
                            if durations[i][0] > 0.0 and durations[i][0] <= 300.0:  # 0-5 minutes
                                # Create a new assignment for the mitra
                                new_assignment = models.OrderAssigned(
                                    id_order_pickup=order_pickup.id,
                                    id_user=order_pickup.id_user,
                                    id_mitra=cursor[i].id_mitra,
                                    vehicle_type=param_assign.vehicle_type,
                                    waktu_jemput=durations[i][0],
                                    jarak_antar=order_pickup.jarak,
                                    waktu_antar=order_pickup.waktu,
                                    url=param_assign.url,  # URL for the latest location of the mitra
                                    status=1,  # 0 = new, 1 = in progress, 2 = completed, 3 = cancelled
                                    is_active=1,  # 0 = tidak aktif, 1 = aktif
                                    created_on=datetime.now()
                                )
                                db.add(new_assignment)
                                # update the order pickup with the assigned mitra
                                order_pickup.updated_on = datetime.now()
                                order_pickup.status = 1  # 0 = new, 1 = in progress, 2 = completed, 3 = cancelled
                                order_pickup.id_mitra = cursor[i].id_mitra

                                # update the mitra coordinates to set progress_order to 1
                                mitra_coords = db.query(models.MitraCoords).filter(
                                    models.MitraCoords.id_mitra == cursor[i].id_mitra,
                                    # models.MitraCoords.place_id == mitra_coords.place_id
                                ).first()
                                mitra_coords.progress_order = 1

                                # update the mitra daily order count
                                mitra_coords.daily_order_count += 1

                                # update status orders
                                orders = db.query(models.Order).filter(
                                    models.Order.id_user == order_pickup.id_user
                                ).all()
                                for order in orders:
                                    order.status = 1
                                    order.updated_on = datetime.now()
                                    
                                db.commit()
                                response_data = response_for_pickup_nearest_mitra(cursor[i], durations[i][0], new_assignment.waktu_antar, new_assignment.jarak_antar, new_assignment.id, db)
                                results.append(response_data)
                                return response_data
                            elif durations[i][0] > 300.0 and durations[i][0] <= 600.0:  # 5-10 minutes
                                # Create a new assignment for the mitra
                                new_assignment = models.OrderAssigned(
                                    id_order_pickup=order_pickup.id,
                                    id_user=order_pickup.id_user,
                                    id_mitra=cursor[i].id_mitra,
                                    vehicle_type=param_assign.vehicle_type,
                                    waktu_jemput=durations[i][0],
                                    jarak_antar=order_pickup.jarak,
                                    waktu_antar=order_pickup.waktu,
                                    url=param_assign.url,  # URL for the latest location of the mitra
                                    status=1,  # 0 = new, 1 = in progress, 2 = completed, 3 = cancelled
                                    is_active=1,  # 0 = tidak aktif, 1 = aktif
                                    created_on=datetime.now()
                                )
                                db.add(new_assignment)
                                # update the order pickup with the assigned mitra
                                order_pickup.updated_on = datetime.now()
                                order_pickup.status = 1  # Assuming 1 means 'in progress'
                                order_pickup.id_mitra = cursor[i].id_mitra

                                # update the mitra coordinates to set progress_order to 1
                                mitra_coords = db.query(models.MitraCoords).filter(
                                    models.MitraCoords.id_mitra == cursor[i].id_mitra,
                                    # models.MitraCoords.place_id == mitra_coords.place_id
                                ).first()
                                mitra_coords.progress_order = 1

                                # update the mitra daily order count
                                mitra_coords.daily_order_count += 1

                                # update status orders
                                orders = db.query(models.Order).filter(
                                    models.Order.id_user == order_pickup.id_user
                                ).all()
                                for order in orders:
                                    order.status = 1
                                    order.updated_on = datetime.now()
                                db.commit()
                                response_data = response_for_pickup_nearest_mitra(cursor[i], durations[i][0], new_assignment.waktu_antar, new_assignment.jarak_antar, new_assignment.id, db)
                                results.append(response_data)
                                return response_data
                            elif durations[i][0] > 600.0 and durations[i][0] <= 1800.0: # 10-30 minutes
                                # kirim ke order publik
                                set_sts_nearest_order = set_status_nearest(param_assign, 3, db)
                                db.commit()
                                response_data = response_for_pickup_nearest_mitra(cursor[i], durations[i][0], cursor[i].waktu, cursor[i].jarak, 0, db)
                                results.append(response_data)
                                # send to redis for another mitra to pickup manually
                                # redis.hset(f"{param_assign.country_code.lower()}:{param_assign.region.lower()}", f"id_mitra:{cursor[i].id_mitra}:id_user:{param_assign.id_user}", json.dumps(response_data))
                                # redis.expire(f"{param_assign.country_code.lower()}:{param_assign.region.lower()}", SET_CACHE)
                                # raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{set_sts_nearest_order}")
                            elif durations[i][0] > 1800.0 and durations[i][0] <= 7200.0: # 30-120 minutes
                                # kirim ke order publik
                                print(f"mitra 30-120 minutes {param_assign}")
                                set_sts_nearest_order = set_status_nearest(param_assign, 4, db)
                                db.commit()
                                response_data = response_for_pickup_nearest_mitra(cursor[i], durations[i][0], cursor[i].waktu, cursor[i].jarak, 0, db)
                                results.append(response_data)
                                # send to redis for another mitra to pickup manually
                                # redis.hset(f"{param_assign.country_code.lower()}:{param_assign.region.lower()}", f"id_mitra:{cursor[i].id_mitra}:id_user:{param_assign.id_user}", json.dumps(response_data))
                                # redis.expire(f"{param_assign.country_code.lower()}:{param_assign.region.lower()}", SET_CACHE)
                                # raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{set_sts_nearest_order}")
                            else: # elif durations[i][0] > 7200.0: # diluar jangkauan mitra
                                # kirim ke order publik
                                print(f"mitra lebih dari 120 minutes {param_assign}")
                                set_sts_nearest_order = set_status_nearest(param_assign, 4, db)
                                db.commit()
                                response_data = response_for_pickup_nearest_mitra(cursor[i], durations[i][0], cursor[i].waktu, cursor[i].jarak, 0, db)
                                results.append(response_data)
                                # send to redis for another mitra to pickup manually
                                # redis.hset(f"{param_assign.country_code.lower()}:{param_assign.region.lower()}", f"id_mitra:{cursor[i].id_mitra}:id_user:{param_assign.id_user}", json.dumps(response_data))
                                # redis.expire(f"{param_assign.country_code.lower()}:{param_assign.region.lower()}", SET_CACHE)
                            # send to redis for another mitra to pickup manually
                            redis.hset(f"{param_assign.country_code.lower()}:{param_assign.region.lower()}", f"id_user:{param_assign.id_user}", json.dumps(results))
                            redis.expire(f"{param_assign.country_code.lower()}:{param_assign.region.lower()}", SET_CACHE)
                        # return {"status_code": status.HTTP_200_OK, "detail": "Successfully fetched data from OpenRouteService"}
                    else:
                        print(f"status param 5 ke 2 {param_assign}")
                        set_sts_nearest_order = set_status_nearest(param_assign, 5, db)
                        empty_assignment = empty_assignment_order(order_pickup, param_assign, db)
                        # response_data = response_for_pickup_nearest_mitra(cursor[i], 0.0, redis)
                        # db.commit()
                        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mitra route tidak tersedia")
                        # return {"status_code": response.status_code, "detail": "Error fetching data from OpenRouteService"}
            # create empty assignment order
            empty_assignment = empty_assignment_order(order_pickup, param_assign, db)
    except Exception as e:
        print(f"status param 5 ke 3 {e}")
        # set_sts_nearest_order = set_status_nearest(param_assign, 6, db)
        # empty_assignment = empty_assignment_order(order_pickup, param_assign, db)
        # db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Mitra tidak tersedia...")
        # raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{e} Proses assign sudah selesai, silahkan tunggu mitra datang menjemput anda")

@router.get("/", status_code=status.HTTP_200_OK, summary="Get all assigned orders")
def get_assign_order(db: Session = Depends(get_db)):
    try:
        assigned_orders = db.query(models.OrderAssigned).all()
        return assigned_orders
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/get-assign-order-mitra/{id_mitra}/", status_code=status.HTTP_200_OK, summary="Get all assigned orders for a specific mitra, trigered by mitra")
def get_assign_order_mitra(id_mitra: int, db: Session = Depends(get_db)):
    try:
        assigned_orders = db.execute(
            f"""SELECT OP.*, OA.waktu_jemput, OA.waktu_antar, OP.lon user_lon, OP.lat user_lat  
                FROM order_assigned OA
                JOIN order_pickup OP
                ON OA.id_order_pickup = OP.id
                WHERE OA.status=1 AND OA.is_active=1
                AND OA.id_mitra={id_mitra}"""
        ).first()
        if not assigned_orders:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No assigned orders found for this order pickup")
        else:
            return assigned_orders
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get("/get-assigned-mitra/{id_user}/", status_code=status.HTTP_200_OK, summary="get the mitra assigned to the order, trigered by user")
def get_assigned_mitra(id_user: int, db: Session = Depends(get_db), redis: Redis = Depends(get_redis)):
    try:
        assigned_orders = db.execute(
            f"""SELECT DC.*, OA.id id_assigned, OA.id_order_pickup id_order, OA.id_user, OA.waiting_time, OA.waktu_jemput, OA.jarak_antar, OA.waktu_antar, OP.status_nearest, 
            OP.lon user_lon, OP.lat user_lat     
                FROM order_assigned OA
                JOIN mitra_coords DC
                ON OA.id_mitra = DC.id_mitra
                JOIN order_pickup OP
                ON OA.id_order_pickup = OP.id
                WHERE OA.status=1 AND OA.is_active=1 AND DC.progress_order = 1 AND DC.id_layanan = 1 
                AND OA.id_user={id_user}"""
        ).first()
        if not assigned_orders:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No assigned orders found for this mitra")
        else:
            # user_trip = db.execute(
            #     f"""SELECT DC.*, OA.waiting_time, OA.waktu_jemput, OA.waktu_antar
            #         FROM order_assigned OA
            #         JOIN mitra_coords DC
            #         ON OA.id_mitra = DC.id_mitra
            #         WHERE OA.status=1 AND OA.is_active=1
            #         AND OA.id_user={id_user}"""
            # ).all()
            results = response_for_pickup_nearest_mitra(assigned_orders, assigned_orders.waktu_jemput, assigned_orders.waktu_antar, assigned_orders.jarak_antar, assigned_orders.id_assigned, db)
            return results
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    
@router.post("/empty_assign_order/", status_code=status.HTTP_200_OK, summary="get the mitra assigned to the order, trigered by user")
def empty_assign_order(request: schemas.EmptyAssignOrder, db: Session = Depends(get_db), payload=Depends(jwt_auth_wrapper)):
    try:
        if(request.lat and request.lon):
            empty_order = db.execute(
            f"""SELECT OP.*  
                FROM order_pickup OP 
                WHERE OP.id_user = {request.id_user}
                AND ROUND(OP.lat, 5) = ROUND({request.lat}, 5)
                AND ROUND(OP.lon, 5) = ROUND({request.lon} ,5)"""
            ).first()
            return empty_order
        else:
            empty_order = db.execute(
            f"""SELECT OP.*  
                FROM order_pickup OP 
                WHERE OP.id_user = {request.id_user}"""
            ).first()
            return empty_order
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    

@router.delete("/{id_user}/", status_code=status.HTTP_202_ACCEPTED, summary="Delete all order by id_user")
def delete_assign_order(id_user: int, db: Session = Depends(get_db)):
    try:
        # delete order_pickup by id_user
        order_pickup = db.query(models.OrderPickup).filter(models.OrderPickup.id_user == id_user).first()
        if not order_pickup:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order pickup not found")
        else:
            # delete order_assigned
            assigned_orders = db.query(models.OrderAssigned).filter(models.OrderAssigned.id_user == id_user).all()
            if assigned_orders:
                for assigneds in assigned_orders:
                    # db.delete(assigneds)
                    # nonaktifkan assigned orders
                    assigneds.status = 0
                    assigneds.is_active = 0
                    assigneds.updated_on = datetime.now()
                db.commit()
            else:
                print(f"assigned order is empty")

            # delete all orders
            orders = db.query(models.Order).filter(models.Order.id_user == id_user).all()
            for order in orders:
                db.delete(order)

            # set status mitra_coords
            mitra_sts = db.query(models.MitraCoords).filter(
                models.MitraCoords.id_mitra == order_pickup.id_mitra,
                models.MitraCoords.vehicle_type == order_pickup.vehicle_type_ordered
                ).first()
            if mitra_sts:
                mitra_sts.progress_order = 0
            
            # delete order_pickup
            db.delete(order_pickup)
        db.commit()
        return {"status_code": status.HTTP_202_ACCEPTED, "detail": "Successfully deleted all orders by id_user"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))