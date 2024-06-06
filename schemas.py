from pydantic import BaseModel


class UserBase(BaseModel):
    telegram_id: int


class UserCreate(UserBase):
    pass


class UserRead(UserBase):
    id: int

    class Config:
        orm_mode = True


class WordBase(BaseModel):
    german: str
    russian: str
    user_id: int


class WordCreate(WordBase):
    pass


class WordRead(WordBase):
    id: int

    class Config:
        orm_mode = True
