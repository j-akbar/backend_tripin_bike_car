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

@router.get("/", status_code=status.HTTP_200_OK, summary="Get the list of all orders")
def get_orders(db: Session = Depends(get_db)):
    orders = db.query(models.Order).all()
    if orders:
        return orders
    else:
        return ({ "status_code": status.HTTP_404_NOT_FOUND, "detail": "Not found order information" })

@router.post("/", status_code =status.HTTP_201_CREATED, summary="Create order from user")
def create_order(request: schemas.Order, db: Session = Depends(get_db)):
    try:
        # Check if an order already exists for the user with the same coordinates and status
        check_active_order = db.query(models.Order).filter(
            models.Order.id_user == request.id_user,
            models.Order.coord_ke == request.coord_ke,
            models.Order.status == 1  # 0 = new, 1 = in progress, 2 = completed, 3 = cancelled
        ).first()
        if check_active_order:
            return ({ "id": check_active_order.id, "status_code": status.HTTP_200_OK, "message": "There is an active order in progress for this user and coordinates." })
        else:
            check_order = db.query(models.Order).filter(
                models.Order.id_user == request.id_user,
                models.Order.coord_ke == request.coord_ke,
                models.Order.status == 0  # 0 = new, 1 = in progress, 2 = completed, 3 = cancelled
            ).first()
            if check_order:
                # hapus semua order yang ada
                db.delete(check_order)
                # create new order
                new_order = models.Order(**request.model_dump(), created_on=datetime.now())
                db.add(new_order)
                db.commit()
                return ({ "id": check_order.id, "status_code": status.HTTP_200_OK, "message": "Successfully delete and create orders" })
            else:
                new_order = models.Order(**request.model_dump(), created_on=datetime.now())
                db.add(new_order)
                db.commit()
                return ({ "id": new_order.id, "status_code": status.HTTP_201_CREATED, "message": "Successfully created an order" })
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{e}")

def reverse_name_words(name):
    words = name.split()  # Split the name into a list of words
    reversed_words = words[::-1]  # Reverse the list of words
    return " ".join(reversed_words) # Join the reversed words back into a string

def get_city(city):
    if(city):
        city_name = ""
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
        # reversed_city_name = reverse_name_words(city_name)
        return city_name
    else: return ''

def get_province(province):
    if(province):
        province_name = province.replace('Java', 'Jawa').replace('North', 'Utara').replace('South', 'Selatan').replace('East', 'Timur').replace('West', 'Barat')
        # reversed_province_name = reverse_name_words(province_name)
        return province_name
    else: return ''


@router.get("/get-order-user/{user_id}/", status_code=status.HTTP_200_OK, summary="Get the list of all orders by user")
def get_orders_by_user(user_id: int, db: Session = Depends(get_db)):
    orders = db.query(models.Order).filter(models.Order.id_user == user_id).all()
    if orders:
        result = []
        for order in orders:
            # The `city_name` variable in the code snippet is being used to convert the city name to a
            # standardized format. It checks the input city name and maps it to a specific format
            # based on predefined rules. If the input city matches one of the predefined mappings
            # (e.g., "North Jakarta" to "Jakarta Utara"), it assigns the corresponding standardized
            # city name to the `city_name` variable. If the input city does not match any predefined
            # mapping, it replaces certain substrings in the city name to adjust the format.
            city_name = get_city(order.city)

            # province_name = order.province.replace('Java', 'Jawa').replace('North', 'Utara').replace('South', 'Selatan').replace('East', 'Timur').replace('West', 'Barat')
            # reversed_province_name = reverse_name_words(province_name)
            province_name = get_province(order.province)

            result.append({
                "label": f"{order.label} ({order.district} {order.building})",
                "description": f"{order.address}, {order.locality} ({order.district}) {city_name} <b>{province_name}</b> {order.postcode}"
            })
        return result
    else:
        return ({ "status_code": status.HTTP_404_NOT_FOUND, "detail": f"Not found order information for user_id {user_id}" })
    # raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Not found order information for user_id {user_id}")

@router.delete("/{order_id}/", status_code =status.HTTP_202_ACCEPTED)
def delete_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if order:
        db.delete(order)
        db.commit()
        return "Successfully deleted order"
    raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = f"Not found order information for order_id {order_id}")

@router.delete("/delete-order-user/{user_id}/", status_code =status.HTTP_202_ACCEPTED)
def delete_order(user_id: int, db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.id_user == user_id).all()
    try:
        if order:
            for o in order:
                db.delete(o)
            db.commit()
            return "Successfully deleted order by user"
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error deleting order: {e}")
    # raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = f"Not found order information for user_id {user_id}")
