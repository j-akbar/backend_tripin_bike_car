from typing import List
from datetime import datetime
from sqlalchemy.orm import Session
from app.data.database import get_db
from app.data import schemas, models
from app.controllers.auth import PasswordHashing
from app.controllers.auth import jwt_auth_wrapper, generate_jwt_access_token, authenticate_user
from fastapi import APIRouter, HTTPException, status, Depends


router = APIRouter()

@router.get("/", status_code=status.HTTP_200_OK, response_model = List[schemas.UserOut], summary="Get the list of all users")
async def get_users(db: Session = Depends(get_db), payload=Depends(jwt_auth_wrapper)):
    try:
        users = db.query(models.User).all()
        return users
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bad Request")
    


# create login using email dan password
# @router.post("/", status_code =status.HTTP_201_CREATED, summary="Create the user")
# async def create_user(request: schemas.User, db: Session = Depends(get_db)):
#     try:
#         check_user_email = db.query(models.User).filter(models.User.email == request.email).first() is not None
#         if check_user_email:
#             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email is already exist")
        
#         password_hashing = PasswordHashing()
#         hashed_password = password_hashing.hash_password(password=request.password)
#         new_user = models.User(name = request.name, email = request.email, password = hashed_password, added_on = datetime.now())
#         db.add(new_user)
#         db.commit()
#         return "Successfully created a user"
#     except:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bad Request")

# create login using phone and password
@router.post("/byphone/", status_code =status.HTTP_201_CREATED, summary="Create the user by phone")
async def create_user(request: schemas.Phone, db: Session = Depends(get_db)):
    try:
        check_user_phone = db.query(models.User).filter(models.User.email == request.phone).first() is not None
        if check_user_phone:
            return check_user_phone
            # raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Phone is already exist")
 
        password_hashing = PasswordHashing()
        hashed_password = password_hashing.hash_password(password=request.password)
        new_user = models.User(id_user = request.id_from, name = request.name, email = request.phone, password = hashed_password, added_on = datetime.now())
        db.add(new_user)
        db.commit()
        return "Successfully created a user"
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bad Request")
    
@router.post("/authenticate/", status_code=status.HTTP_200_OK, response_model=schemas.Token)
async def login(request: schemas.LoginPhone, db:Session= Depends(get_db)):
    user = authenticate_user(db, username = request.phone, password= request.password)
    print(f"User: {request}")
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid credentials")

    access_token = generate_jwt_access_token(name=user.name, email=user.email)
    return {"access_token":access_token, "token_type":"bearer"}

    
@router.put("/{user_id}/", status_code=status.HTTP_202_ACCEPTED)
async def update_user(user_id:int, request:schemas.UserUpdate, db:Session = Depends(get_db), payload=Depends(jwt_auth_wrapper)):
    user = db.query(models.User).filter(models.User.id == user_id)
    if user.first():
        user_update_dict = request.dict(exclude_none=True)
        user_update_dict['update_on'] = datetime.now()
        user.update(user_update_dict)
        db.commit()
        return "successfully updated the user data"
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Not found user information for user_id {user_id}")

@router.get("/{user_id}/", status_code=status.HTTP_200_OK, response_model = schemas.UserOut)
async def get_user(user_id: int, db: Session = Depends(get_db), payload=Depends(jwt_auth_wrapper)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        return user
    raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = f"Not found user information for user_id {user_id}")
    

@router.delete("/{user_id}/", status_code =status.HTTP_202_ACCEPTED)
async def delete_user(user_id: int, db: Session = Depends(get_db), payload=Depends(jwt_auth_wrapper)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
        return "Successfully deleted user"
    raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = f"Not found user information for user_id {user_id}")
    
@router.delete("/", status_code=status.HTTP_202_ACCEPTED)
async def delete_all_user(db: Session = Depends(get_db), payload=Depends(jwt_auth_wrapper)):
    try:
        db.query(models.User).delete()
        db.commit()
        return "Successfully flush all the user data"
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unable to delete the user data")