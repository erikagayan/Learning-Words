import logging
import os
from typing import List
from sqlalchemy.orm import Session
from database.models import User, Word
from fastapi import FastAPI, Depends, HTTPException
from database.engine import Base, engine, SessionLocal
from schemas import UserCreate, UserRead, WordCreate, WordRead

app = FastAPI()

Base.metadata.create_all(bind=engine)

logging.basicConfig(level=logging.INFO)


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
    logging.info(f"Adding word: {word.german} for user_id: {word.user_id}")

    # Проверка наличия пользователя по telegram_id
    user = db.query(User).filter(User.telegram_id == word.user_id).first()
    if not user:
        logging.info(f"User with id {word.user_id} does not exist. Creating new user.")
        new_user = User(telegram_id=word.user_id)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        user = new_user

    max_user_word_id = (db.query(Word).filter(Word.user_id == user.id).
                        order_by(Word.user_word_id.desc()).first())
    if max_user_word_id:
        user_word_id = max_user_word_id.user_word_id + 1
    else:
        user_word_id = 1

    db_word = Word(german=word.german, russian=word.russian,
                   user_id=user.id, user_word_id=user_word_id)
    db.add(db_word)
    db.commit()
    db.refresh(db_word)
    logging.info(f"Added word: {db_word.german} with id: {db_word.id}")
    return db_word


@app.get("/users/{user_id}/words", response_model=List[WordRead])
def get_words(user_id: int, db: Session = Depends(get_db)):
    logging.info(f"Fetching words for user_id: {user_id}")
    words = db.query(Word).filter(Word.user_id == user_id).all()
    logging.info(f"Fetched words: {words}")
    return words


@app.delete("/words/{word_id}", response_model=WordRead)
def delete_word(word_id: int, db: Session = Depends(get_db)):
    word = db.query(Word).filter(Word.id == word_id).first()
    if word is None:
        raise HTTPException(status_code=404, detail="Word not found")
    db.delete(word)
    db.commit()
    return word


@app.put("/words/{word_id}", response_model=WordRead)
def update_word(word_id: int, word: WordCreate, db: Session = Depends(get_db)):
    db_word = db.query(Word).filter(Word.id == word_id).first()
    if db_word is None:
        raise HTTPException(status_code=404, detail="Word not found")

    db_word.german = word.german
    db_word.russian = word.russian
    db.commit()
    db.refresh(db_word)
    return db_word
