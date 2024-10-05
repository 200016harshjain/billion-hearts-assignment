from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    images = relationship("Image", back_populates="user")

class Image(Base):
    __tablename__ = 'images'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    original_filename = Column(String)
    upload_date = Column(DateTime, default=func.now())
    width = Column(Integer)
    height = Column(Integer)
    file_size = Column(Integer)
    file_type = Column(String)
    storage_path = Column(String)


    user = relationship("User", back_populates="images")
