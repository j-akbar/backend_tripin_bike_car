from typing import List
from datetime import datetime
from sqlalchemy.orm import Session
from app.data.database import get_db
from app.data import schemas, models
from app.controllers.auth import PasswordHashing
from app.controllers.auth import jwt_auth_wrapper
from fastapi import APIRouter, HTTPException, status, Depends
import requests

router = APIRouter()

@router.post("/", status_code =status.HTTP_201_CREATED, summary="Create driver coordinates")
def create_driver_coords(driver_coords: schemas.DriverCoords, db: Session = Depends(get_db)):
    try:
        check_driver_coords = db.query(models.DriverCoords).filter(
            models.DriverCoords.id_driver == driver_coords.id_driver,
            models.DriverCoords.status == 0
        ).first()
        if check_driver_coords:
            for key, value in driver_coords.model_dump().items():
                setattr(check_driver_coords, key, value)
            db.commit()
            return "Successfully updated driver coordinates"
        else:
            new_driver_coords = models.DriverCoords(**driver_coords.model_dump(), created_on=datetime.now())
            db.add(new_driver_coords)
            db.commit()
            return "Successfully created driver coordinates"
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{e}")

@router.get("/", status_code=status.HTTP_200_OK, summary="Get all driver coordinates")
def get_driver_coords(db: Session = Depends(get_db)):
    driver_coords = db.query(models.DriverCoords).all()
    if driver_coords:
        return driver_coords
    else:
        return ({ "status_code": status.HTTP_404_NOT_FOUND, "detail": f"Not found driver coordinates information" })

@router.get("/{country_code}/{region}/", status_code=status.HTTP_200_OK, summary="Get driver coordinates by location")
def get_driver_coords_by_location(country_code: str, region: str, db: Session = Depends(get_db)):
    driver_coords = db.query(models.DriverCoords).filter(
        models.DriverCoords.country_code == country_code,
        models.DriverCoords.region == region
    ).all()
    if not driver_coords:
        return ({ "status_code": status.HTTP_404_NOT_FOUND, "detail": f"Driver coordinates not found" })
    return driver_coords

@router.post("/process-pickup-nearest-driver/", status_code=status.HTTP_200_OK, summary="Process get all nearest  driver for pickup triggered by user")
def get_driver_coords_by_pickup(request: schemas.DriverCoordsOut, db: Session = Depends(get_db)):
    try:
        cursor = db.execute(
            f"""SELECT DC.*, 
                OP.id_user, OP.id_order, 
                OP.phone user_phone, OP.name user_name, OP.address user_address, OP.description user_description, OP.lon user_lon, OP.lat user_lat 
                FROM order_pickup OP 
                JOIN driver_coords DC 
                ON OP.vehicle_type_ordered = DC.vehicle_type AND OP.country_code = DC.country_code AND OP.region = DC.region 
                WHERE OP.id_user = {request.id_user} AND OP.vehicle_type_ordered = {request.vehicle_type} AND 
                DC.status = 1 AND DC.active = 1 AND DC.progress_order = 0 AND 
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
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver coordinates not found")
            cursor.close()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{e}")

@router.delete("/{driver_id}/", status_code=status.HTTP_204_NO_CONTENT, summary="Delete driver coordinates")
def delete_driver_coords(driver_id: int, db: Session = Depends(get_db)):
    db_driver_coords = db.query(models.DriverCoords).filter(models.DriverCoords.id_driver == driver_id).first()
    if not db_driver_coords:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver coordinates not found")
    
    db.delete(db_driver_coords)
    db.commit()
    return {"detail": "Driver coordinates deleted successfully"}