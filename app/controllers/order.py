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
        check_order = db.query(models.Order).filter(
            models.Order.id_user == request.id_user,
            models.Order.coord_ke == request.coord_ke,
            models.Order.status == 0  # Assuming status 0 means 'new' or 'pending'
        ).first()
        if check_order:
            for key, value in request.model_dump().items():
                setattr(check_order, key, value)
            check_order.updated_on = datetime.now()
            db.commit()
            cursor = db.execute(
                f"SELECT id from orders WHERE id_user = {request.id_user} AND DATE(created_on) = DATE('now', 'localtime') ORDER BY id ASC LIMIT 1")
            for row in cursor.fetchall():
                cursor.close()
            return ({ "id": row[0], "status_code": status.HTTP_200_OK }) # "Successfully updated order"
        else:
            new_order = models.Order(**request.model_dump(), created_on=datetime.now())
            db.add(new_order)
            db.commit()
            cursor = db.execute(
                f"SELECT id from orders WHERE id_user = {request.id_user} AND DATE(created_on) = DATE('now', 'localtime') ORDER BY id ASC")
            for row in cursor.fetchall():
                cursor.close()
            return ({ "id": row[0], "status_code": status.HTTP_201_CREATED }) # "Successfully created an order"
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{e}")

@router.get("/get-order-user/{user_id}/", status_code=status.HTTP_200_OK, summary="Get the list of all orders by user")
def get_orders_by_user(user_id: int, db: Session = Depends(get_db)):
    orders = db.query(models.Order).filter(models.Order.id_user == user_id).all()
    if orders:
        return orders
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
