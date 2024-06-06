from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database.engine import *
from database.models import User, Word
from schemas import UserCreate, UserRead, WordCreate, WordRead

app = FastAPI()

# Создание всех таблиц
Base.metadata.create_all(bind=engine)


# Зависимость, которая создает сессию для работы с базой данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/users/", response_model=UserRead)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(telegram_id=user.telegram_id)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.post("/words/", response_model=WordRead)
def create_word(word: WordCreate, db: Session = Depends(get_db)):
    db_word = Word(german=word.german, russian=word.russian, user_id=word.user_id)
    db.add(db_word)
    db.commit()
    db.refresh(db_word)
    return db_word


@app.get("/users/{user_id}/words", response_model=List[WordRead])
def get_words(user_id: int, db: Session = Depends(get_db)):
    words = db.query(Word).filter(Word.user_id == user_id).all()
    return words


@app.delete("/words/{word_id}", response_model=WordRead)
def delete_word(word_id: int, db: Session = Depends(get_db)):
    word = db.query(Word).filter(Word.id == word_id).first()
    if word is None:
        raise HTTPException(status_code=404, detail="Word not found")
    db.delete(word)
    db.commit()
    return word
