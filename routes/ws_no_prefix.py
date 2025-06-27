import socketio
from core.socket_io import sio
import redis

from datetime import datetime
from sqlalchemy.orm import Session
from app.data.database import get_db
from app.data import schemas, models
from fastapi import APIRouter, HTTPException, status, Depends
import requests
import json
import sqlite3
import os
from dotenv import load_dotenv
load_dotenv()


# Database setup
SQLALCHEMY_DATABASE_URL = os.environ["DATABASE_URL"]
conn = sqlite3.connect('sql_app.db')
cursor = conn.cursor()
# connet to redis
REDIS_URI = os.getenv("REDIS_URI", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "123456")
SET_CACHE = os.getenv("SET_CACHE")
r = redis.StrictRedis(host=REDIS_URI, port=REDIS_PORT, db=0)

class NoPrefixNamespace(socketio.AsyncNamespace):

    def on_connect(self, sid, environ):
        print("connect ", sid)

    async def on_message(self, sid, data):
        print("message ", data)
        await sio.emit("response", "hi " + data)

    def on_disconnect(self, sid):
        print("disconnect ", sid)

    # switch aktif atau tidak aktif driver (trigger manual dari aplikasi driver)
    async def on_switch_driver_active(self, sid, data):
        json_data = json.dumps(data)
        json_load = json.loads(json_data)
        id_driver = json_load["id_driver"]
        switch_sts = json_load["switch"]
        update_values = (switch_sts,id_driver)
        # ubah switch status active atau tidak
        cursor.execute(
            f"""UPDATE driver_coords SET 
                active = ?
            WHERE id_driver = ? """, update_values)
        conn.commit()
        driver_status = cursor.execute(
            f"""SELECT *
                FROM driver_coords dc
                WHERE dc.id_driver = {id_driver} """
        ).fetchone()
        conn.commit()
        # print("switch driver ", driver_status, sid)
        await sio.emit("switch_driver", driver_status, sid)





    # simpan data koordinat driver realtime
    async def on_send_driver_coord(self, sid, data):
        json_data = json.dumps(data)
        json_load = json.loads(json_data)
        id_driver = json_load["id_driver"]
        # value insert
        insert_values = (id_driver,json_load["phone"],json_load["name"],json_load["place_id"],json_load["place_type"],json_load["place_key"],json_load["place_value"],json_load["lat"],json_load["lon"],json_load["country_code"],json_load["country_name"],json_load["region"],json_load["province"],json_load["city"],json_load["label"],json_load["sublabel"],json_load["postcode"],json_load["district"],json_load["locality"],json_load["place"],json_load["neighborhood"],json_load["address"],json_load["vehicle_type"],json_load["vehicle_number"],json_load["priority"],json_load["status"],json_load["is_active"],datetime.now())
        # value update
        update_values = (json_load["phone"],json_load["name"],json_load["place_id"],json_load["place_type"],json_load["place_key"],json_load["place_value"],json_load["lat"],json_load["lon"],json_load["country_code"],json_load["country_name"],json_load["region"],json_load["province"],json_load["city"],json_load["label"],json_load["sublabel"],json_load["postcode"],json_load["district"],json_load["locality"],json_load["place"],json_load["neighborhood"],json_load["address"],json_load["vehicle_type"],json_load["vehicle_number"],json_load["priority"],json_load["status"],json_load["is_active"],datetime.now(),id_driver)
        # print(f"Received message from {id_driver}: {data}")
        driver_coord = cursor.execute(
            f"""SELECT *
                FROM driver_coords dc
                WHERE dc.id_driver = {id_driver} AND dc.status = 1"""
        ).fetchone()
        conn.commit()
        if driver_coord:
            # update posisi driver
            cursor.execute(
                f"""UPDATE driver_coords SET 
                    phone = ?,
                    name = ?,
                    place_id = ?,
                    place_type = ?,
                    place_key = ?,
                    place_value = ?,
                    lat = ?,
                    lon = ?,
                    country_code = ?,
                    country_name = ?,
                    region = ?,
                    province = ?,
                    city = ?,
                    label = ?,
                    sublabel = ?,
                    postcode = ?,
                    district = ?,
                    locality = ?,
                    place = ?,
                    neighborhood = ?,
                    address = ?,
                    vehicle_type = ?,
                    vehicle_number = ?,
                    priority = ?,
                    status = ?,
                    is_active = ?,
                    updated_on = ?
                WHERE id_driver = ? """, update_values)
            conn.commit()
        else:
            # simpan posisi driver jika tidak ada data
            cursor.execute(
                f"""INSERT INTO driver_coords (
                    id_driver,
                    phone,
                    name,
                    place_id,
                    place_type,
                    place_key,
                    place_value,
                    lat,
                    lon,
                    country_code,
                    country_name,
                    region,
                    province,
                    city,
                    label,
                    sublabel,
                    postcode,
                    district,
                    locality,
                    place,
                    neighborhood,
                    address,
                    vehicle_type,
                    vehicle_number,
                    priority,
                    status,
                    is_active,
                    created_on
                )
                VALUES (
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ? ) """, insert_values)
            conn.commit()
            # print(insert_values)
        # print("send_driver_coord ", driver_coord, sid)
        await sio.emit("driver_coord", driver_coord, sid)
            

        # item = json.dumps(f"{process_message}")
        # print(item)
        # await sio.emit("driver_coord", item, sid)

    # send driver coordinate
    # async def on_senddriver_coord(self, sid, data: schemas.DriverCoords):
    #     # Retrieve the database session using Depends correctly
    #     async def process_message(db: Session = Depends(get_db)):
    #         try:
    #             print("driver_coord ", data)
    #             check_driver_coords = db.query(models.DriverCoords).filter(
    #                 models.DriverCoords.id_driver == data.id_driver,
    #                 models.DriverCoords.status == 0
    #             ).first()
    #             if check_driver_coords:
    #                 for key, value in data.model_dump().items():
    #                     setattr(check_driver_coords, key, value)
    #                 db.commit()
    #                 # return "Successfully updated driver coordinates"
    #                 # return await sio.emit("drivercoord", data)
    #                 # return check_driver_coords
    #                 print("driver_coord ", check_driver_coords, sid)
    #                 await sio.emit('driver_coord', check_driver_coords, room=sid)
    #             else:
    #                 new_driver_coords = models.DriverCoords(**data.model_dump(), created_on=datetime.now())
    #                 db.add(new_driver_coords)
    #                 db.commit()
    #                 # return "Successfully created driver coordinates"
    #                 # return await sio.emit("drivercoord", data)
    #                 # return new_driver_coords
    #                 print("driver_coord ", new_driver_coords, sid)
    #                 await sio.emit('driver_coord', new_driver_coords, room=sid)
    #         except requests.exceptions.RequestException as e:
    #             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="error data")

    #     # Using the FastAPI app to get the dependency
    #     # item = process_message
    #     # await sio.emit('driver_coord', item, room=sid)

    # # async def on_senddriver_coord(self, sid, data):
    # #     print("driver_coord ", data, sid)
    # #     await sio.emit("driver_coord", data, room=sid)
    
    
    
    # chat data dictionary to store user and driver chat messages
    # async def on_reconnect_user_mitra(self, sid, id_assigned):
    #     id_assigned = id_assigned
    #     results = []
    #     chats = cursor.execute(
    #         f"""SELECT *
    #             FROM chat_mitra cm
    #             WHERE cm.id_assigned = {id_assigned} ORDER BY created_on ASC """
    #     ).fetchall()
    #     conn.commit()
    #     for msg in chats:
    #         results.append({
    #             "id_assigned": msg[1],
    #             "person_id": msg[2],
    #             "image": msg[4],
    #             "type": msg[5],
    #             "message": msg[6],
    #             "file_name": msg[7],
    #             "file_size": msg[8],
    #             "class_name": msg[9],
    #             "time": msg[10],
    #             "is_read": msg[11],
    #             "created_on": msg[12]
    #         })
    #     await sio.emit("reconnect_user_mitra", results, sid)


    # chat user mitra
    async def on_chat_user_mitra(self, sid, data):
        json_data = json.dumps(data)
        json_load = json.loads(json_data)
        id_assigned = json_load["id_assigned"]
        person_id = json_load["person_id"]
        image = json_load["image"]
        type = json_load["type"]
        message = json_load["message"]
        file_name = json_load["file_name"]
        file_size = json_load["file_size"]
        class_name = json_load["class_name"]
        time = json_load["time"]
        update_values = (id_assigned, person_id, image, type, message, file_name, file_size, class_name, time, True, datetime.now())
        cursor.execute(
            f"""INSERT INTO chat_mitra(id_assigned, person_id, image, type, message, file_name, file_size, class_name, time, is_read, created_on) VALUES (?,?,?,?,?,?,?,?,?,?,?) """, update_values)
        conn.commit()
        results = []
        chats = cursor.execute(
            f"""SELECT *
                FROM chat_mitra cm
                WHERE cm.id_assigned = {id_assigned} ORDER BY created_on ASC """
        ).fetchall()
        conn.commit()
        for msg in chats:
            results.append({
                "id_assigned": msg[1],
                "person_id": msg[2],
                "image": msg[3],
                "type": msg[4],
                "message": msg[5],
                "file_name": msg[6],
                "file_size": msg[7],
                "class_name": msg[8],
                "time": msg[9],
                "is_read": msg[10],
                "created_on": msg[11]
            })
        await sio.emit("chat_user_mitra", results, sid)
        
    # disconect user mitra
    # async def on_disconnect_user_mitra(self, sid, data):
    #     json_data = json.dumps(data)
    #     json_load = json.loads(json_data)
    #     user_id = json_load["id"]
    #     if user_id in self.chat_data:
    #         del self.chat_data[user_id]
    #     print("disconnect_user_mitra ", user_id, sid)
    #     await sio.emit("disconnect_user_mitra", {"status": "success", "id": user_id}, room=sid)