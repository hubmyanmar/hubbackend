from sqlalchemy import Column, BigInteger, Boolean, String, Text, DateTime, func
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=True)
    position = Column(String(100), nullable=True)
    role = Column(String(50), nullable=False, server_default="member")
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    
    image = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    meetings_created = relationship("Meeting", back_populates="creator")