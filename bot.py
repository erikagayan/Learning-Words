import logging
import os
from random import random
import random
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Router
from dotenv import load_dotenv
from aiogram import Router, F

API_URL = "http://127.0.0.1:8000"
load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")
if not API_TOKEN:
    raise ValueError("API token not found! Check the .env file")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

router = Router()

users_learning = {}


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    """Отправляет сообщение, когда команда /start вызвана."""
    user = message.from_user
    await message.answer(
        f"Привет, {user.first_name}! Я помогу тебе учить немецкие слова. Используй /add для добавления нового слова, /words для просмотра своих слов, и /delete для удаления слова."
    )
    # Создаем пользователя в API
    telegram_id = user.id
    response = requests.post(f"{API_URL}/users/", json={"telegram_id": telegram_id})
    if response.status_code == 200:
        await message.answer("Ваш аккаунт создан!")
    else:
        await message.answer("Ваш аккаунт уже существует.")


@router.message(Command("add"))
async def cmd_add(message: types.Message):
    """Добавляет новое слово."""
    user = message.from_user
    words = message.text.split()[1:]
    if len(words) != 2:
        await message.answer('Использование: /add <немецкое слово> <русский перевод>')
        return

    german, russian = words
    user_id = user.id
    response = requests.post(f"{API_URL}/words/", json={"german": german, "russian": russian, "user_id": user_id})
    if response.status_code == 200:
        await message.answer(f"Слово '{german}' добавлено с переводом '{russian}'")
    else:
        await message.answer("Произошла ошибка при добавлении слова.")


@router.message(Command("words"))
async def cmd_words(message: types.Message):
    """Выводит список слов пользователя."""
    user = message.from_user
    user_id = user.id
    response = requests.get(f"{API_URL}/users/{user_id}/words")
    if response.status_code == 200:
        words_list = response.json()
        if not words_list:
            await message.answer("У вас еще нет добавленных слов.")
        else:
            words_str = "\n".join([f"{word['user_word_id']}: {word['german']} - {word['russian']}" for word in words_list])
            await message.answer(f"Ваши слова:\n{words_str}")
    else:
        await message.answer("Произошла ошибка при получении списка слов.")


@router.message(Command("learn"))
async def cmd_learn(message: types.Message):
    """Выдает случайное слово для изучения."""
    user = message.from_user
    user_id = user.id
    response = requests.get(f"{API_URL}/users/{user_id}/words")
    if response.status_code == 200:
        words_list = response.json()
        if not words_list:
            await message.answer("У вас еще нет добавленных слов.")
        else:
            word = random.choice(words_list)
            if random.choice([True, False]):
                users_learning[user_id] = (word['german'], word['russian'], 'russian')
                await message.answer(f"Переведите слово на русский: {word['german']}")
            else:
                users_learning[user_id] = (word['russian'], word['german'], 'german')
                await message.answer(f"Переведите слово на немецкий: {word['russian']}")
    else:
        await message.answer("Произошла ошибка при получении списка слов.")


@router.message(Command("delete"))
async def cmd_delete(message: types.Message):
    """Удаляет слово из словаря пользователя."""
    user = message.from_user
    words = message.text.split()[1:]
    if len(words) != 1:
        await message.answer('Использование: /delete <ID слова>')
        return

    user_word_id = words[0]
    try:
        user_word_id = int(user_word_id)
    except ValueError:
        await message.answer('ID слова должен быть числом.')
        return

    user_id = user.id
    response = requests.get(f"{API_URL}/users/{user_id}/words")
    if response.status_code == 200:
        words_list = response.json()
        word_to_delete = next((word for word in words_list if word['user_word_id'] == user_word_id), None)
        if word_to_delete:
            word_id = word_to_delete['id']
            response = requests.delete(f"{API_URL}/words/{word_id}")
            if response.status_code == 200:
                await message.answer(f"Слово с ID {user_word_id} удалено.")
            else:
                await message.answer("Произошла ошибка при удалении слова.")
        else:
            await message.answer(f"Слово с ID {user_word_id} не найдено.")
    else:
        await message.answer("Произошла ошибка при получении списка слов.")



@router.message(F.text)
async def check_translation(message: types.Message):
    """Проверяет перевод слова."""
    user = message.from_user
    user_id = user.id
    if user_id in users_learning:
        original, translation, lang = users_learning[user_id]
        user_translation = message.text.strip().lower()
        correct_translation = translation.strip().lower()
        if user_translation == correct_translation:
            await message.answer("Правильно!")
        else:
            await message.answer(f"Неправильно. Правильный перевод: {translation}")
        del users_learning[user_id]


dp.include_router(router)


async def main():
    """Запускает бота."""
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
