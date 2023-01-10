

from sqlalchemy import Column, DateTime, Integer, String,TIMESTAMP
from sqlalchemy.sql import func

from db_conf import Base

class User(Base):
    __tablename__ = "Profile"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80),nullable=True)
    email = Column(String(30), unique=True)
    password = Column(String(255))
    last_login = Column(TIMESTAMP, nullable=True)
    created_on = Column(DateTime(timezone=True), server_default=func.now())

