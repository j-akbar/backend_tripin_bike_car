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
redis_order = redis.StrictRedis(host=REDIS_URI, port=REDIS_PORT, db=2, decode_responses=True)


class ReverseTools:
    def reverse_name_words(name):
        words = name.split()  # Split the name into a list of words
        reversed_words = words[::-1]  # Reverse the list of words
        return " ".join(reversed_words) # Join the reversed words back into a string

class TranslateTools:
    ########################################### start tools utk lokasi
    def get_region(region):
        if(region):
            region_name = region.replace('Java', 'Jawa').replace('North', 'Utara').replace('South', 'Selatan').replace('East', 'Timur').replace('West', 'Barat')
            # reversed_region_name = reverse_name_words(region_name)
            return region_name
        else: return ''
    
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
            reversed_state_name = ReverseTools.reverse_name_words(state_name)
            return reversed_state_name
        else: return ''
        
    def get_province(province):
        if(province):
            province_name = province.replace('Java', 'Jawa').replace('North', 'Utara').replace('South', 'Selatan').replace('East', 'Timur').replace('West', 'Barat')
            # reversed_province_name = reverse_name_words(province_name)
            return province_name
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
            reversed_city_name = ReverseTools.reverse_name_words(city_name)
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
        

class NoPrefixNamespace(socketio.AsyncNamespace):
    
    def on_connect(self, sid, environ):
        print("connect ", sid)

    async def on_message(self, sid, data):
        print("message ", data)
        await sio.emit("response", "hi " + data)

    def on_disconnect(self, sid):
        print("disconnect ", sid)

    # switch aktif atau tidak aktif mitra (trigger manual dari aplikasi mitra)
    async def on_switch_mitra_active(self, sid, data):
        json_data = json.dumps(data)
        json_load = json.loads(json_data)
        id_mitra = json_load["id_mitra"]
        switch_sts = json_load["switch"]
        update_values = (switch_sts,id_mitra)
        # ubah switch status active atau tidak
        cursor.execute(
            f"""UPDATE mitra_coords SET 
                active = ?
            WHERE id_mitra = ? """, update_values)
        conn.commit()
        mitra_status = cursor.execute(
            f"""SELECT *
                FROM mitra_coords dc
                WHERE dc.id_mitra = {id_mitra} """
        ).fetchone()
        conn.commit()
        # print("switch mitra ", mitra_status, sid)
        await sio.emit("switch_mitra", mitra_status, sid)


    # simpan data koordinat mitra realtime
    async def on_send_mitra_coord(self, sid, data):
        json_data = json.dumps(data)
        json_load = json.loads(json_data)
        id_mitra = json_load["id_mitra"]
        # translate component needed
        region_indo_lang = TranslateTools.get_region(json_load["region"])
        state_indo_lang = TranslateTools.get_state(json_load["state"])
        province_indo_lang = TranslateTools.get_province(json_load["province"])
        city_indo_lang = TranslateTools.get_city(json_load["city"])
        name_indo_lang = TranslateTools.get_name(json_load["name"])
        # value insert
        insert_values = (id_mitra,json_load["id_layanan"],json_load["phone"],name_indo_lang,json_load["place_id"],json_load["place_type"],json_load["place_key"],json_load["place_value"],json_load["lat"],json_load["lon"],json_load["country_code"],json_load["country_name"],region_indo_lang,state_indo_lang,province_indo_lang,city_indo_lang,json_load["label"],json_load["sublabel"],json_load["postcode"],json_load["district"],json_load["locality"],json_load["place"],json_load["neighborhood"],json_load["address"],json_load["vehicle_type"],json_load["vehicle_number"],json_load["priority"],0,1,datetime.now(),0,0,0,json_load["status"],json_load["is_active"],datetime.now())
        # value update
        update_values = (json_load["id_layanan"],json_load["phone"],name_indo_lang,json_load["place_id"],json_load["place_type"],json_load["place_key"],json_load["place_value"],json_load["lat"],json_load["lon"],json_load["country_code"],json_load["country_name"],region_indo_lang,state_indo_lang,province_indo_lang,city_indo_lang,json_load["label"],json_load["sublabel"],json_load["postcode"],json_load["district"],json_load["locality"],json_load["place"],json_load["neighborhood"],json_load["address"],json_load["vehicle_type"],json_load["vehicle_number"],json_load["priority"],datetime.now(),json_load["status"],json_load["is_active"],datetime.now(),id_mitra)
        # print(f"Received message from {id_mitra}: {data}")
        mitra_coord = cursor.execute(
            f"""SELECT dc.*, dc.progress_order process_order 
                FROM mitra_coords dc 
                WHERE dc.id_mitra = {id_mitra} """
        ).fetchone()
        conn.commit()
        if mitra_coord:
            # update posisi mitra
            cursor.execute(
                f"""UPDATE mitra_coords SET 
                    id_layanan = ?,
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
                    state = ?,
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
                    last_active = ?,
                    status = ?,
                    is_active = ?,
                    updated_on = ?
                WHERE id_mitra = ? """, update_values)
            conn.commit()
        else:
            # simpan posisi mitra jika tidak ada data
            cursor.execute(
                f"""INSERT INTO mitra_coords (
                    id_mitra,
                    id_layanan,
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
                    state,
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
                    progress_order,
                    active,
                    last_active,
                    daily_order_count,
                    daily_completed_count,
                    daily_cancelled_count,
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
        # print("send_mitra_coord ", mitra_coord, sid)
        await sio.emit("mitra_coord", mitra_coord, sid)
        

    async def on_get_mitra_position(self, sid, data):
        json_data = json.dumps(data)
        json_load = json.loads(json_data)
        id_mitra = json_load["id_mitra"]
        latitude = json_load["latitude"]
        longitude = json_load["longitude"]
        mitra_position = {
            "id_mitra": id_mitra,
            "latitude": latitude,
            "longitude": longitude,
        }
        await sio.emit("mitra_position", mitra_position, sid)
            

        # item = json.dumps(f"{process_message}")
        # print(item)
        # await sio.emit("mitra_coord", item, sid)

    # send mitra coordinate
    # async def on_sendmitra_coord(self, sid, data: schemas.MitraCoords):
    #     # Retrieve the database session using Depends correctly
    #     async def process_message(db: Session = Depends(get_db)):
    #         try:
    #             print("mitra_coord ", data)
    #             check_mitra_coords = db.query(models.MitraCoords).filter(
    #                 models.MitraCoords.id_mitra == data.id_mitra,
    #                 models.MitraCoords.status == 0
    #             ).first()
    #             if check_mitra_coords:
    #                 for key, value in data.model_dump().items():
    #                     setattr(check_mitra_coords, key, value)
    #                 db.commit()
    #                 # return "Successfully updated mitra coordinates"
    #                 # return await sio.emit("mitracoord", data)
    #                 # return check_mitra_coords
    #                 print("mitra_coord ", check_mitra_coords, sid)
    #                 await sio.emit('mitra_coord', check_mitra_coords, room=sid)
    #             else:
    #                 new_mitra_coords = models.MitraCoords(**data.model_dump(), created_on=datetime.now())
    #                 db.add(new_mitra_coords)
    #                 db.commit()
    #                 # return "Successfully created mitra coordinates"
    #                 # return await sio.emit("mitracoord", data)
    #                 # return new_mitra_coords
    #                 print("mitra_coord ", new_mitra_coords, sid)
    #                 await sio.emit('mitra_coord', new_mitra_coords, room=sid)
    #         except requests.exceptions.RequestException as e:
    #             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="error data")

    #     # Using the FastAPI app to get the dependency
    #     # item = process_message
    #     # await sio.emit('mitra_coord', item, room=sid)

    # # async def on_sendmitra_coord(self, sid, data):
    # #     print("mitra_coord ", data, sid)
    # #     await sio.emit("mitra_coord", data, room=sid)



    # chat data dictionary to store user and mitra chat messages
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


    # check mitra assigned
    async def on_process_assigned_mitra(self, sid, data):
        json_data = json.dumps(data)
        json_load = json.loads(json_data)
        id_user = json_load['id_user']
        assigned_orders = cursor.execute(
            f"""SELECT DC.*, OA.id id_assigned, OA.id_order_pickup id_order, OA.id_user, OA.waiting_time, OA.waktu_jemput, OA.jarak_antar, OA.waktu_antar, OP.status_nearest    
                FROM order_assigned OA
                JOIN mitra_coords DC
                ON OA.id_mitra = DC.id_mitra
                JOIN order_pickup OP
                ON OA.id_order_pickup = OP.id
                WHERE OA.status=1 AND OA.is_active=1 AND DC.progress_order = 1
                AND OA.id_user={id_user}"""
        ).first()
        conn.commit()
        await sio.emit("process_assigned_mitra", assigned_orders, sid)


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
            f"""INSERT INTO chat_mitra(id_assigned, person_id, image, type, message, file_name, file_size, class_name, time, is_active, is_read, created_on) VALUES (?,?,?,?,?,?,?,?,?,1,?,?) """, update_values)
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
        
    # read 1 chat for notification
    async def on_get_chat_notification(self, sid, data):
        json_data = json.dumps(data)
        json_load = json.loads(json_data)
        id_user = json_load["user_id"]
        msg = cursor.execute(
            f"""SELECT CM.*, OA.vehicle_type, OA.id_user, OA.id_mitra, OA.id id_assigned 
            FROM order_assigned OA 
            JOIN chat_mitra CM 
            ON OA.id = CM.id_assigned 
            WHERE CM.is_active = 1 AND OA.id_user={id_user} ORDER BY CM.id DESC LIMIT 1  """
        ).fetchone()
        if msg:
            result = {
                "id": msg[0],
                "icon": {
                    "name": "chat",
                    "color": "primary",
                },
                "timestamp": msg[9],
                "title": msg[5],
                "subtitle": msg[5],
                "path": msg[1],
                "person_id": msg[2],
                "image": msg[3],
                "type": msg[4],
                "message": msg[5],
                "file_name": msg[6],
                "file_size": msg[7],
                "class_name": msg[8],
                "time": msg[9],
                "is_read": msg[13],
                "created_on": msg[14],
                "vehicle_type": msg[16],
                "id_user": msg[17],
                "id_mitra": msg[18],
                "id_assigned": msg[19]
            }
            conn.commit()
            await sio.emit("read_chat_notification", result, sid)
        else:
            await sio.emit("read_chat_notification", {}, sid)
            
            
    async def on_get_hanging_order(self, sid, data):
        try:
            json_data = json.dumps(data)
            json_load = json.loads(json_data)
            country_code = json_load["country_code"]
            region = json_load["region"]
            cached_item = redis_order.hgetall(f"{country_code.lower()}:{region.lower()}")
            # cached_item = redis_order.hget(f"{country_code.lower()}:{region.lower()}", "id_user:66")
            if not cached_item:
                await sio.emit("hanging_order", [], sid)
            else:
                result = []
                data_dump = json.dumps(cached_item)
                data_load = json.loads(data_dump)
                for key, value  in data_load.items():
                    if key.startswith("id_user:"):
                        value_load = json.loads(value)
                        result.append(value_load)
                # print(f"data result: {result}")
                await sio.emit("hanging_order", result, sid)
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="error data")
            

        
    # disconect user mitra
    # async def on_disconnect_user_mitra(self, sid, data):
    #     json_data = json.dumps(data)
    #     json_load = json.loads(json_data)
    #     user_id = json_load["id"]
    #     if user_id in self.chat_data:
    #         del self.chat_data[user_id]
    #     print("disconnect_user_mitra ", user_id, sid)
    #     await sio.emit("disconnect_user_mitra", {"status": "success", "id": user_id}, room=sid)


