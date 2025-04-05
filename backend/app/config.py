import os

# 환경 변수 또는 기본값으로 MySQL 연결 설정
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://user:test@localhost:3306/chat_app"
)
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
