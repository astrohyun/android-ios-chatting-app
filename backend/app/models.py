from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
#from .database import Base

# ✅ Base 클래스 정의
Base = declarative_base()

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sender = Column(String(255), nullable=False)
    message = Column(String(1000), nullable=False)
    channel = Column(String(255), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ChatMessage(sender={self.sender}, channel={self.channel}, message={self.message[:20]})>"

# ✅ 사용자 모델 (기존 유지)
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    nickname = Column(String(50), unique=True, nullable=True)

    # ✅ WebSocket 상태 추적 (추가)
#    is_online = Column(Integer, default=0)  # 0 = 오프라인, 1 = 온라인

    # ✅ 사용자가 참여한 채널 관계
    channels = relationship("ChannelParticipant", back_populates="user")


# ✅ 채널 모델 (새롭게 추가)
class Channel(Base):
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)  # 채널 이름
    password = Column(String(255), nullable=True)  # 비밀 채널 여부 (Optional)
    created_at = Column(DateTime, default=datetime.utcnow)  # 생성 시간

    # ✅ 채널에 속한 사용자 관계
    participants = relationship("ChannelParticipant", back_populates="channel")


# ✅ 사용자-채널 관계 모델 (채널 내 사용자 관리)
class ChannelParticipant(Base):
    __tablename__ = "channel_participants"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False)

    user = relationship("User", back_populates="channels")
    channel = relationship("Channel", back_populates="participants")
