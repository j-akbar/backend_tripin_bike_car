from typing import List
from datetime import datetime
from sqlalchemy.orm import Session
from app.data.database import get_db
from app.data import schemas, models
from app.controllers.auth import PasswordHashing, authenticate_mitra
from app.controllers.auth import jwt_auth_wrapper, generate_jwt_access_token, authenticate_mitra
from fastapi import APIRouter, HTTPException, status, Depends

router = APIRouter()

@router.post("/byphone/", status_code =status.HTTP_201_CREATED, summary="Create the mitra by phone")
async def create_mitra(request: schemas.Phone, db: Session = Depends(get_db)):
    try:
        check_mitra_phone = db.query(models.Mitra).filter(models.Mitra.email == request.phone).first() is not None
        if check_mitra_phone:
            return check_mitra_phone
            # raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Phone is already exist")
 
        password_hashing = PasswordHashing()
        hashed_password = password_hashing.hash_password(password=request.password)
        new_mitra = models.Mitra(id_mitra = request.id_from, name = request.name, email = request.phone, password = hashed_password, added_on = datetime.now())
        print(f"new new_mitra: {new_mitra}")
        db.add(new_mitra)
        db.commit()
        return "Successfully created a mitra"
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bad Request")
    
@router.post("/authenticate/", status_code=status.HTTP_200_OK, response_model=schemas.Token)
async def login(request: schemas.LoginPhone, db:Session= Depends(get_db)):
    mitra = authenticate_mitra(db, username = request.phone, password= request.password)
    if not mitra:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid credentials")

    access_token = generate_jwt_access_token(name=mitra.name, email=mitra.email)
    return {"access_token":access_token, "token_type":"bearer"}