from typing import List
from datetime import datetime
from sqlalchemy.orm import Session
from app.data.database import get_db
from app.data import schemas, models
from app.controllers.auth import PasswordHashing
from app.controllers.auth import jwt_auth_wrapper
from fastapi import APIRouter, HTTPException, status, Depends
# import json
import requests


router = APIRouter()

@router.post("/", status_code =status.HTTP_201_CREATED, summary="Create currency price from user")
async def create_currency_price(request: schemas.CountryPrice, db: Session = Depends(get_db), payload=Depends(jwt_auth_wrapper)):
    try:
        check_country_code = db.query(models.CountryPrice).filter(models.CountryPrice.country_code == request.country_code).first() is not None
        if check_country_code:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Country code is already exist")
        
        new_currency_price = models.CountryPrice(**request.model_dump(), created_on=datetime.now())
        db.add(new_currency_price)
        db.commit()
        return "Successfully created a currency price"
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{e}")

@router.get("/", status_code=status.HTTP_200_OK, response_model = List[schemas.CountryPrice], summary="Get the list of all currency prices")
async def get_currency_prices(db: Session = Depends(get_db)):
    try:
        currency_prices = db.query(models.CountryPrice).all()
        return currency_prices
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bad Request")

@router.put("/{country_code}/", status_code=status.HTTP_202_ACCEPTED, summary="Update currency price")
async def update_currency_price(country_code: str, request: schemas.CountryPrice, db: Session = Depends(get_db), payload=Depends(jwt_auth_wrapper)):
    try:
        currency_price = db.query(models.CountryPrice).filter(models.CountryPrice.country_code == country_code).first()
        if currency_price:
            for key, value in request.model_dump().items():
                setattr(currency_price, key, value)
            db.commit()
            return "Successfully updated currency price"
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found currency price")
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bad Request")

@router.get("/{country_code}/", status_code=status.HTTP_200_OK, response_model=schemas.CountryPrice, summary="Get currency price by ID")
async def get_currency_price(country_code: str, db: Session = Depends(get_db)):
    try:
        currency_price = db.query(models.CountryPrice).filter(models.CountryPrice.country_code == country_code).first()
        if currency_price:
            return currency_price
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found currency price")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{e}")

@router.delete("/{country_code}/", status_code=status.HTTP_204_NO_CONTENT, summary="Delete currency price")
async def delete_currency_price(country_code: str, db: Session = Depends(get_db), payload=Depends(jwt_auth_wrapper)):
    try:
        currency_price = db.query(models.CountryPrice).filter(models.CountryPrice.country_code == country_code).first()
        if currency_price:
            db.delete(currency_price)
            db.commit()
            return
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found currency code price")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{e}")