#websocket.py
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from typing import Dict, List
from .config import SECRET_KEY
from .database import SessionLocal
from .models import ChatMessage
from datetime import datetime

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[dict]] = {}

    async def send_user_list(self, channel: str):
        """현재 채널에 접속한 사용자 목록을 모든 클라이언트에 브로드캐스트"""
        if channel in self.active_connections:
            users = [conn["username"] for conn in self.active_connections[channel]]
            user_list_message = f"USER_LIST:{','.join(users)}"
            for connection in self.active_connections[channel]:
                await connection["websocket"].send_text(user_list_message)

    async def connect(self, websocket: WebSocket, channel: str, username: str):
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = []
        self.active_connections[channel].append({"websocket": websocket, "username": username})
        print(f"{username} joined channel {channel}")
        # 유저 목록 업데이트 브로드캐스트
        await self.send_user_list(channel)

    def disconnect(self, websocket: WebSocket, channel: str):
        if channel in self.active_connections:
            self.active_connections[channel] = [
                conn for conn in self.active_connections[channel]
                if conn["websocket"] != websocket
            ]
            if not self.active_connections[channel]:
                del self.active_connections[channel]
            else:
                asyncio.create_task(self.send_user_list(channel))


    async def broadcast(self, message: str, channel: str, sender: str):
        """ 메시지를 모든 사용자에게 브로드캐스트하며 DB에도 저장 """
        db = SessionLocal()
        chat_message = ChatMessage(sender=sender, message=message, channel=channel)
        db.add(chat_message)
        db.commit()
        db.close()

        if channel in self.active_connections:
            current_time = datetime.now()
            formatted_message = f"{sender}: {message} ({current_time})"
            for connection in self.active_connections[channel]:
                await connection["websocket"].send_text(formatted_message)

manager = ConnectionManager()

@router.websocket("/ws/chat")   # 채널 내 사용자들과 계속 연결을 위해 socket 통신
async def chat_websocket(websocket: WebSocket):
    token = websocket.query_params.get("token") # 사용자가 누구인지 구분하기 위해서
    channel = websocket.query_params.get("channel", "default")  # 사용자가 지금 사용하는 채널을 확인하기 위해서

    if token is None:
        await websocket.close(code=1008)
        return

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        username = payload.get("sub")
        if username is None:
            await websocket.close(code=1008)
            return
    except JWTError:
        await websocket.close(code=1008)
        return

    await manager.connect(websocket, channel, username)

    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(data, channel, username)
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)
