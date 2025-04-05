from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form #3.22.
from fastapi.responses import JSONResponse, FileResponse #3.22.
from pydantic import BaseModel
from sqlalchemy.orm import Session
from .database import get_db
from .models import Channel, ChatMessage    #3.1.
from typing import List    #3.1.
import os # 3.22.
from pathlib import Path # 3.22.

router = APIRouter()

UPLOAD_DIR = Path("upload")  # 업로드된 파일을 저장할 경로 3.22.
# 업로드 디렉토리가 없으면 생성
if not UPLOAD_DIR.exists():
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class ChannelRequest(BaseModel):
    title: str
    password: str = None  # 비밀번호는 선택 사항

#3.1.
class MessageResponse(BaseModel):
    sender: str
    message: str
    timestamp: str  # ISO 형식 문자열

def create_channel(name: str, password: str = None, db: Session = None):
    """ 채널을 데이터베이스에 추가하는 함수 """
    if db is None:
        raise HTTPException(status_code=500, detail="Database session not available")

    existing_channel = db.query(Channel).filter(Channel.name == name).first()
    if existing_channel:
        raise HTTPException(status_code=400, detail="Channel already exists")

    new_channel = Channel(name=name, password=password)
    db.add(new_channel)
    db.commit()
    db.refresh(new_channel)
    return new_channel

def get_channels(db: Session = None):
    """ 현재 존재하는 모든 채널을 반환하는 함수 """
    if db is None:
        raise HTTPException(status_code=500, detail="Database session not available")

    channels = db.query(Channel).all()
    return [{"name": ch.name} for ch in channels]

@router.post("/create_channel")
async def create_channel_endpoint(channel: ChannelRequest, db: Session = Depends(get_db)):
    """ 채널 생성 API """
    create_channel(channel.title, channel.password, db)
    return {"message": f"Channel '{channel.title}' created"}


@router.get("/channels")
async def list_channels(db: Session = Depends(get_db)):
    """ 채널 목록 가져오기 """
    return get_channels(db)

#3.1.
@router.get("/messages", response_model=List[MessageResponse])
def get_chat_messages(channel: str, db: Session = Depends(get_db)):
    """
    특정 채널의 이전 메시지를 가져오는 API
    """
    if not channel:
        raise HTTPException(status_code=400, detail="채널 이름이 필요합니다.")

    # 해당 채널이 존재하는지 확인
    existing_channel = db.query(Channel).filter(Channel.name == channel).first()
    if not existing_channel:
        raise HTTPException(status_code=404, detail="해당 채널이 존재하지 않습니다.")

    # 최근 메시지 가져오기 (최신순 → 오래된 순 정렬)
    messages = db.query(ChatMessage).filter(ChatMessage.channel == channel).order_by(ChatMessage.timestamp.desc()).all()

    # JSON 형태로 반환 (timestamp를 ISO 8601 형식으로 변환)
    return [
        MessageResponse(sender=msg.sender, message=msg.message, timestamp=msg.timestamp.isoformat())
        for msg in reversed(messages)
    ]


@router.post("/upload")
async def upload_file(file: UploadFile = File(...), channel: str = Form(...)):
    try:
        # 파일 저장 경로 설정 (채널 이름과 파일 이름을 기반으로 저장)
        file_path = UPLOAD_DIR / f"{channel}_{file.filename}"

        # 파일 저장
        with open(file_path, "wb") as f:
            f.write(await file.read())

        # 업로드 성공 후 파일 URL 반환
        file_url = f"http://127.0.0.1:8003/chat/upload/{file_path.name}"
        return JSONResponse(content={"file_url": file_url}, status_code=200)

    except Exception as e:
        return JSONResponse(content={"detail": str(e)}, status_code=400)

@router.get("/upload/{filename}")
async def get_file(filename: str):
    file_path = UPLOAD_DIR / filename
    if file_path.exists():
        return FileResponse(file_path)
    return JSONResponse(content={"detail": "File not found"}, status_code=404)