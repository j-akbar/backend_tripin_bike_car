import os
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

# REDIS
REDIS_URI = os.getenv("REDIS_URI", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "123456")
SET_CACHE = os.getenv("SET_CACHE")

router = APIRouter()

# REDIS ACTION
def get_redis():
    return Redis(host=REDIS_URI, port=REDIS_PORT, db=2, decode_responses=True)


@router.post("/", status_code =status.HTTP_201_CREATED, summary="Create mitra coordinates")
def create_mitra_jasa_coords(mitra_jasa_coords: schemas.MitraJasaCoords, db: Session = Depends(get_db), payload=Depends(jwt_auth_wrapper)):
    try:
        check_mitra_jasa_coords = db.query(models.MitraJasaCoords).filter(
            models.MitraJasaCoords.id_mitra == mitra_jasa_coords.id_mitra,
            models.MitraJasaCoords.status == 0
        ).first()
        if check_mitra_jasa_coords:
            for key, value in mitra_jasa_coords.model_dump().items():
                setattr(check_mitra_jasa_coords, key, value)
            db.commit()
            return "Successfully updated mitra coordinates"
        else:
            new_mitra_jasa_coords = models.MitraJasaCoords(**mitra_jasa_coords.model_dump(), created_on=datetime.now())
            db.add(new_mitra_jasa_coords)
            db.commit()
            return "Successfully created mitra coordinates"
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{e}")

@router.get("/", status_code=status.HTTP_200_OK, summary="Get all mitra coordinates")
def get_mitra_jasa_coords(db: Session = Depends(get_db)):
    mitra_jasa_coords = db.query(models.MitraJasaCoords).all()
    if mitra_jasa_coords:
        return mitra_jasa_coords
    else:
        return ({ "status_code": status.HTTP_404_NOT_FOUND, "detail": f"Not found mitra coordinates information" })

@router.get("/{country_code}/{region}/", status_code=status.HTTP_200_OK, summary="Get mitra coordinates by location")
def get_mitra_jasa_coords_by_location(country_code: str, region: str, db: Session = Depends(get_db)):
    mitra_jasa_coords = db.query(models.MitraJasaCoords).filter(
        models.MitraJasaCoords.country_code == country_code,
        models.MitraJasaCoords.region == region
    ).all()
    if not mitra_jasa_coords:
        return ({ "status_code": status.HTTP_404_NOT_FOUND, "detail": f"Mitra coordinates not found" })
    return mitra_jasa_coords

@router.post("/process-pickup-nearest-mitra/", status_code=status.HTTP_200_OK, summary="Process get all nearest  mitra for pickup triggered by user")
def get_mitra_jasa_coords_by_pickup(request: schemas.MitraJasaCoordsOut, db: Session = Depends(get_db), payload=Depends(jwt_auth_wrapper)):
    try:
        cursor = db.execute(
            f"""SELECT DC.*, 
                OP.id_user, OP.id_order, 
                OP.phone user_phone, OP.name user_name, OP.address user_address, OP.description user_description, OP.lon user_lon, OP.lat user_lat 
                FROM order_pickup OP 
                JOIN mitra_jasa_coords DC 
                ON OP.vehicle_type_ordered = DC.vehicle_type AND OP.country_code = DC.country_code AND OP.region = DC.region 
                WHERE OP.id_user = {request.id_user} AND OP.vehicle_type_ordered = {request.vehicle_type} AND 
                DC.status = 1 AND DC.active = 1 AND DC.is_active = 1 AND DC.progress_order = 0 AND 
                OP.country_code = '{request.country_code}' AND OP.region = '{request.region}' AND 
                OP.province = '{request.province}' AND 
                ( OP.postcode = '{request.postcode}' OR OP.city = '{request.city}' OR 
                OP.district = '{request.district}' OR OP.address = '{request.address}' OR 
                OP.neighborhood = '{request.neighborhood}' OR OP.locality = '{request.locality}' OR 
                OP.label = '{request.label}' OR OP.sublabel = '{request.sublabel}') 
                ORDER BY DC.priority, DC.daily_order_count ASC LIMIT 100""").all()
        if cursor:
            return cursor
        if not cursor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mitra coordinates not found")
            cursor.close()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{e}")

@router.delete("/{mitra_id}/", status_code=status.HTTP_204_NO_CONTENT, summary="Delete mitra coordinates")
def delete_mitra_jasa_coords(mitra_id: int, db: Session = Depends(get_db), payload=Depends(jwt_auth_wrapper)):
    db_mitra_jasa_coords = db.query(models.MitraJasaCoords).filter(models.MitraJasaCoords.id_mitra == mitra_id).first()
    if not db_mitra_jasa_coords:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mitra coordinates not found")
    
    db.delete(db_mitra_jasa_coords)
    db.commit()
    return {"detail": "Mitra coordinates deleted successfully"}