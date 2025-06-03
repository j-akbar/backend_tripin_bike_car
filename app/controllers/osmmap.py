from typing import List
from datetime import datetime
from sqlalchemy.orm import Session
from app.data.database import get_db
from app.data import schemas, models
from app.controllers.auth import PasswordHashing
from app.controllers.auth import jwt_auth_wrapper
from fastapi import APIRouter, HTTPException, status, Depends
# import json


router = APIRouter()

@router.get("/", status_code=status.HTTP_200_OK, response_model = List[schemas.Order], summary="Get the list of all orders")
async def get_orders(db: Session = Depends(get_db)):
    try:
        orders = db.query(models.Order).all()
        if orders:
            return orders
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found order information")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bad Request")

@router.post("/", status_code =status.HTTP_201_CREATED, summary="Create order from user")
async def create_order(request: schemas.Order, db: Session = Depends(get_db)):
    try:
        new_order = models.Order(**request.model_dump(), created_on=datetime.now())
        db.add(new_order)
        db.commit()
        cursor = db.execute(
            f"SELECT id from orders WHERE id_user = {request.id_user} ORDER BY id ASC LIMIT 1")
        return ({ "id": cursor.fetchone()[0], "status": status.HTTP_201_CREATED }) # "Successfully created an order"
        # return json.dumps({ "id": cursor.fetchone()[0], "status": status.HTTP_201_CREATED })
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bad Request")

@router.get("/get-order-user/{user_id}/", status_code=status.HTTP_200_OK, response_model = List[schemas.Order], summary="Get the list of all orders by user")
async def get_orders_by_user(user_id: int, db: Session = Depends(get_db)):
    try:
        orders = db.query(models.Order).filter(models.Order.id_user == user_id).all()
        if orders:
            return orders
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found order information")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bad Request")
    
@router.delete("/{order_id}/", status_code =status.HTTP_202_ACCEPTED)
async def delete_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if order:
        db.delete(order)
        db.commit()
        return "Successfully deleted order"
    raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = f"Not found order information for order_id {order_id}")

@router.delete("/delete-order-user/{user_id}/", status_code =status.HTTP_202_ACCEPTED)
async def delete_order(user_id: int, db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.id_user == user_id).all()
    if order:
        for o in order:
            db.delete(o)
        db.commit()
        return "Successfully deleted order by user"
    raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = f"Not found order information for user_id {user_id}")
