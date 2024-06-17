from database.engine import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, ForeignKey, BigInteger


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True)

    words = relationship("Word", back_populates="owner")


class Word(Base):
    __tablename__ = "words"
    id = Column(Integer, primary_key=True, index=True)
    german = Column(String, index=True)
    russian = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    user_word_id = Column(Integer)

    owner = relationship("User", back_populates="words")
