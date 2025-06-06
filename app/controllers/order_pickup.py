from typing import List
from datetime import datetime
from sqlalchemy.orm import Session
from app.data.database import get_db
from app.data import schemas, models
from app.controllers.auth import PasswordHashing
from app.controllers.auth import jwt_auth_wrapper
from fastapi import APIRouter, HTTPException, status, Depends
import requests
# import json

router = APIRouter()

@router.post("/", status_code=status.HTTP_200_OK, summary="Create order pickup from user")
def create_order_pickup(request: schemas.OrderPickup, db: Session = Depends(get_db)):
    try:
        # check active order pickup
        active_order = db.query(models.OrderPickup).filter(
            models.OrderPickup.id_user == request.id_user,
            models.OrderPickup.status == 1,     # 0 = new, 1 = in progress, 2 = completed, 3 = cancelled
            models.OrderPickup.id_driver != 0,  # 0 = belum ada driver yang assigned, >0 = sudah ada driver yang assigned
        ).first()
        if active_order:
            return active_order
        else:   # jika tidak ada order pickup yang sedang aktif, maka cek apakah ada order pickup baru
            check_order = db.query(models.OrderPickup).filter(
                models.OrderPickup.id_user == request.id_user,
                models.OrderPickup.status == 0,     # 0 = new, 1 = in progress, 2 = completed, 3 = cancelled
                models.OrderPickup.is_pickup == 0,  # 0 = belum pickup, 1 = sudah di pickup oleh driver
                models.OrderPickup.running == 0,    # 0 = belum jalan, 1 = sudah jalan
                models.OrderPickup.finished == 0,    # 0 = belum selesai, 1 = sudah selesai
            ).first()
            if check_order:
                check_order.updated_on = datetime.now()
                db.commit()
                return check_order  # "Successfully updated order pickup"
            else:
                new_order_pickup = models.OrderPickup(**request.model_dump(), created_on=datetime.now())
                db.add(new_order_pickup)
                db.commit()
                return new_order_pickup  # "Successfully created an order pickup"
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{e}")
    
@router.get("/", status_code=status.HTTP_200_OK, summary="Get the list of all order pickups")
def get_order_pickups(db: Session = Depends(get_db)):
    order_pickups = db.query(models.OrderPickup).all()
    if order_pickups:
        return order_pickups
    else:
        return ({ "status_code": status.HTTP_404_NOT_FOUND, "detail": f"Not found order pickup information" })
    # raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found order pickup information")

@router.get("/{id_user}/", status_code=status.HTTP_200_OK, summary="Get order pickup by user ID")
def get_order_pickup_by_user_id(id_user: int, db: Session = Depends(get_db)):
    order_pickup = db.query(models.OrderPickup).filter(models.OrderPickup.id_user == id_user).all()
    if order_pickup:
        return order_pickup
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order pickup not found")

@router.delete("/{id_user}/", status_code=status.HTTP_202_ACCEPTED)
def delete_order_pickup(id_user: int, db: Session = Depends(get_db)):
    try:
        order_pickup = db.query(models.OrderPickup).filter(models.OrderPickup.id_user == id_user).all()
        if not order_pickup:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order pickup not found")
        for o in order_pickup:
            db.delete(o)
        db.commit()
        return {"detail": "Successfully deleted all order pickup by id_user"}
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{e}")