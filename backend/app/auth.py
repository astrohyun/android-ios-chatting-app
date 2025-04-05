from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt, JWTError
from pydantic import BaseModel

from .database import SessionLocal
from .models import User, ChannelParticipant, Channel
from .config import SECRET_KEY

router = APIRouter(prefix="/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Pydantic 모델을 사용하여 요청 데이터 검증
class UserRegisterRequest(BaseModel):
    username: str
    password: str
    nickname: str = None

class UserLoginRequest(BaseModel):
    username: str
    password: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)

def create_token(data: dict, expires_delta: timedelta = timedelta(hours=1)) -> str:
    """JWT 토큰 생성"""
    data["exp"] = datetime.utcnow() + expires_delta
    return jwt.encode(data, SECRET_KEY, algorithm="HS256")

def verify_jwt(authorization: str = Header(None)) -> dict:
    """JWT 토큰을 검증하고 사용자 정보를 반환"""
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=403, detail="Invalid authentication credentials")

    token = authorization.split(" ")[1]  # "Bearer <TOKEN>"에서 TOKEN 추출
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=403, detail="Invalid authentication credentials")
        return {"username": username}  # 검증된 사용자 정보 반환
    except JWTError:
        raise HTTPException(status_code=403, detail="Invalid authentication credentials")


def add_user_to_default_channel(user_id: int, db: Session):
    """ 새 사용자가 기본 채널에 자동으로 추가되도록 설정 """
    default_channel = db.query(Channel).filter(Channel.name == "default").first()

    if default_channel:
        participation = ChannelParticipant(user_id=user_id, channel_id=default_channel.id)
        db.add(participation)
        db.commit()

@router.post("/register")
def register(user: UserRegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")

    # Pydantic 모델에서 받은 데이터를 기반으로 사용자 생성
    user_db = User(
        username=user.username,
        password_hash=hash_password(user.password),
        nickname=user.nickname,
        created_at=datetime.utcnow()  # created_at 필드에 현재 시간을 설정
    )
    db.add(user_db)
    db.commit()
    db.refresh(user_db)
    return {"message": "User registered successfully"}

@router.post("/login")
def login(user: UserLoginRequest, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}
