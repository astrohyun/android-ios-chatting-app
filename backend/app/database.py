from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base
from sqlalchemy.orm import Session

# ✅ MySQL 데이터베이스 연결 정보
DATABASE_URL = "mysql+pymysql://user:test@localhost:3306/chat_app"

# ✅ 데이터베이스 엔진 생성
engine = create_engine(DATABASE_URL, echo=True)

# ✅ 세션 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def initialize_db():
    """ 데이터베이스 테이블 생성 및 기본 채널 추가 """
    Base.metadata.create_all(bind=engine)  # 테이블 생성

    from .models import Channel
    db = SessionLocal()
    try:
        # ✅ default 채널이 존재하는지 확인
        default_channel = db.query(Channel).filter(Channel.name == "default").first()
        if not default_channel:
            print("🔹 Default 채널이 존재하지 않아 생성합니다.")
            new_channel = Channel(name="default", password=None)  # 비밀번호 없음
            db.add(new_channel)
            db.commit()
    finally:
        db.close()