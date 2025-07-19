import jwt
from fastapi import HTTPException, status
from datetime import datetime, timedelta
from passlib.context import CryptContext
from app.controllers import user
from app.data import models
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer
import os
from dotenv import load_dotenv
load_dotenv()


SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_DAYS = int(os.getenv("ACCESS_TOKEN_EXPIRE_DAYS")) if int(os.getenv("ACCESS_TOKEN_EXPIRE_DAYS")) else 360
security = HTTPBearer()


class PasswordHashing:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
    def hash_password(self,password):
        return self.pwd_context.hash(password)

    def verify_password(self,plain_password, hashed_password):
        return self.pwd_context.verify(plain_password, hashed_password)


def generate_jwt_access_token(name, email):
    payload={
            "name": name,
            "email": email,
            "disabled": False,
            # "exp" : datetime.utcnow()+ timedelta(minutes=ACCESS_TOKEN_EXPIRE_DAYS)
            "exp" : datetime.utcnow()+ timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    }
    access_token = jwt.encode(
        payload,
        key = SECRET_KEY,
        algorithm = ALGORITHM
    )
    return access_token

def get_user(db, username:str):
    user = db.query(models.User).filter(models.User.email == username).first()
    return user

def get_mitra(db, username:str):
    mitra = db.query(models.Mitra).filter(models.Mitra.email == username).first()
    return mitra
    
def authenticate_user(db, username: str, password: str):
    user = get_user(db, username=username)
    if not user:
        return False
    hasing_password = PasswordHashing()
    if not hasing_password.verify_password(password, user.password):
        return False
    return user

def authenticate_mitra(db, username: str, password: str):
    mitra = get_mitra(db, username=username)
    if not mitra:
        return False
    hasing_password = PasswordHashing()
    if not hasing_password.verify_password(password, mitra.password):
        return False
    return mitra


def get_access_token(request):
    if "Bearer" in request.scheme:
        return request.credentials
    return None


def get_access_token(request):
    if "Bearer" in request.scheme:
        return request.credentials
    return None


def jwt_auth_wrapper(request: HTTPBearer = Security(security)):
    try:
        token = get_access_token(request)
        if token:
            return jwt.decode(token, key=SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Signature expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def decode_auth_token(token):
    try:
        return jwt.decode(token, key=SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Signature expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


