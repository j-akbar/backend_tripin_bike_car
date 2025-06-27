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

@router.get("/{id_assigned}/", status_code=status.HTTP_200_OK, summary="Get the list of all chat mitra")
async def get_chat_mitra(id_assigned: int, db: Session = Depends(get_db)):
    chat_mitra = db.query(models.ChatMitra).filter(models.ChatMitra.id_assigned == id_assigned).all()
    return chat_mitra