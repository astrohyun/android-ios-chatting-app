from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .chat import router as chat_router  # chat.py의 router 가져오기
from .models import Base, Channel
from .database import engine, SessionLocal, initialize_db
from .auth import router as auth_router
from .config import SECRET_KEY
from .websocket import router as websocket_router  # ✅ WebSocket 라우터 포함

app = FastAPI()
initialize_db()  # ✅ 데이터베이스 초기화

# ✅ 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

# ✅ CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 단계에서는 모든 출처 허용 (운영시 적절히 변경)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ 기본 채널이 존재하는지 확인하는 함수
def ensure_default_channel(db: Session):
    default_channel = db.query(Channel).filter(Channel.name == "default").first()
    if not default_channel:
        new_channel = Channel(name="default", password=None)  # 공개 채널
        db.add(new_channel)
        db.commit()
        print("✅ Default channel created")

# ✅ DB 초기화 시 기본 채널 생성
with SessionLocal() as db:
    ensure_default_channel(db)

# ✅ 채널 생성 API
@app.post("/channels/create")
def create_channel(name: str, password: str = None, db: Session = Depends(SessionLocal)):
    """ 새 채널을 생성하는 API """
    if db.query(Channel).filter(Channel.name == name).first():
        raise HTTPException(status_code=400, detail="Channel already exists")

    new_channel = Channel(name=name, password=password)
    db.add(new_channel)
    db.commit()

    return {"message": "Channel created successfully"}

# ✅ 채널 목록 조회 API
@app.get("/channels/list")
def list_channels(db: Session = Depends(SessionLocal)):
    """ 채널 목록을 반환하는 API """
    channels = db.query(Channel).all()
    return [{"name": channel.name, "is_private": bool(channel.password)} for channel in channels]

# ✅ 기존 auth 및 websocket 라우터 포함
app.include_router(auth_router)
app.include_router(websocket_router)  # ✅ WebSocket 라우터 추가
app.include_router(chat_router, prefix="/chat")