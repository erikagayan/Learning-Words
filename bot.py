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
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

API_URL = "http://127.0.0.1:8000"
load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")
if not API_TOKEN:
    raise ValueError("API token not found! Check the .env file")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

router = Router()

users_learning = {}


def get_main_keyboard():
    buttons = [
        [KeyboardButton(text="/add"), KeyboardButton(text="/words")],
        [KeyboardButton(text="/change"), KeyboardButton(text="/delete")],
        [KeyboardButton(text="/learn"),]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    """Отправляет сообщение, когда команда /start вызвана."""
    user = message.from_user
    await message.answer(
        f"Привет, {user.first_name}! Я помогу тебе учить немецкие слова. Используй кнопки ниже для управления.",
        reply_markup=get_main_keyboard()
    )
    # Создаем пользователя в API
    telegram_id = user.id
    response = requests.post(f"{API_URL}/users/", json={"telegram_id": telegram_id})
    if response.status_code == 200:
        await message.answer("Ваш аккаунт создан!")
    else:
        await message.answer("Ваш аккаунт уже существует.")

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    """Отправляет список доступных команд."""
    help_text = (
        "Доступные команды:\n"
        "/start - Начать использование бота\n"
        "/add <немецкое слово> <русский перевод> - Добавить новое слово\n"
        "/words - Показать список ваших слов\n"
        "/delete <ID слова> - Удалить слово\n"
        "/change <ID слова> <новое немецкое слово> <новый русский перевод> - Изменить слово\n"
        "/learn - Начать обучение, бот задаст случайное слово для перевода\n"
        "/help - Показать список команд"
    )
    await message.answer(help_text, reply_markup=get_main_keyboard())

@router.message(Command("add"))
async def cmd_add(message: types.Message):
    """Добавляет новое слово."""
    user = message.from_user
    words = message.text.split()[1:]
    if len(words) != 2:
        await message.answer('Использование: /add <немецкое слово> <русский перевод>', reply_markup=get_main_keyboard())
        return

    german, russian = words
    user_id = user.id
    response = requests.post(f"{API_URL}/words/", json={"german": german, "russian": russian, "user_id": user_id})
    if response.status_code == 200:
        await message.answer(f"Слово '{german}' добавлено с переводом '{russian}'", reply_markup=get_main_keyboard())
    else:
        await message.answer("Произошла ошибка при добавлении слова.", reply_markup=get_main_keyboard())

@router.message(Command("words"))
async def cmd_words(message: types.Message):
    """Выводит список слов пользователя."""
    user = message.from_user
    user_id = user.id
    response = requests.get(f"{API_URL}/users/{user_id}/words")
    if response.status_code == 200:
        words_list = response.json()
        if not words_list:
            await message.answer("У вас еще нет добавленных слов.", reply_markup=get_main_keyboard())
        else:
            words_str = "\n".join([f"{word['user_word_id']}: {word['german']} - {word['russian']}" for word in words_list])
            await message.answer(f"Ваши слова:\n{words_str}", reply_markup=get_main_keyboard())
    else:
        await message.answer("Произошла ошибка при получении списка слов.", reply_markup=get_main_keyboard())

@router.message(Command("change"))
async def cmd_change(message: types.Message):
    """Редактирует слово."""
    user = message.from_user
    args = message.text.split(maxsplit=3)
    if len(args) != 4:
        await message.answer('Использование: /change <ID слова> <новое немецкое слово> <новый русский перевод>', reply_markup=get_main_keyboard())
        return

    try:
        user_word_id = int(args[1])
    except ValueError:
        await message.answer('ID слова должен быть числом.', reply_markup=get_main_keyboard())
        return

    new_german = args[2]
    new_russian = args[3]
    user_id = user.id

    # Получаем список слов пользователя для поиска слова по user_word_id
    response = requests.get(f"{API_URL}/users/{user_id}/words")
    if response.status_code == 200:
        words_list = response.json()
        word_to_edit = next((word for word in words_list if word['user_word_id'] == user_word_id), None)
        if word_to_edit:
            word_id = word_to_edit['id']
            update_response = requests.put(
                f"{API_URL}/words/{word_id}",
                json={"german": new_german, "russian": new_russian, "user_id": user_id}
            )
            if update_response.status_code == 200:
                await message.answer(f"Слово с ID {user_word_id} обновлено. Новое значение: {new_german} - {new_russian}", reply_markup=get_main_keyboard())
            else:
                await message.answer("Произошла ошибка при обновлении слова.", reply_markup=get_main_keyboard())
        else:
            await message.answer(f"Слово с ID {user_word_id} не найдено.", reply_markup=get_main_keyboard())
    else:
        await message.answer("Произошла ошибка при получении списка слов.", reply_markup=get_main_keyboard())

@router.message(Command("learn"))
async def cmd_learn(message: types.Message):
    """Выдает случайное слово для изучения."""
    user = message.from_user
    user_id = user.id

    # Получаем список слов пользователя
    response = requests.get(f"{API_URL}/users/{user_id}/words")
    if response.status_code == 200:
        words_list = response.json()
        if not words_list:
            await message.answer("У вас еще нет добавленных слов.", reply_markup=get_main_keyboard())
        else:
            word = random.choice(words_list)
            if random.choice([True, False]):
                # Немецкое слово, перевод на русский
                users_learning[user_id] = (word['german'], word['russian'], 'russian')
                await message.answer(f"Переведите слово на русский: {word['german']}", reply_markup=get_main_keyboard())
            else:
                # Русское слово, перевод на немецкий
                users_learning[user_id] = (word['russian'], word['german'], 'german')
                await message.answer(f"Переведите слово на немецкий: {word['russian']}", reply_markup=get_main_keyboard())
    else:
        await message.answer("Произошла ошибка при получении списка слов.", reply_markup=get_main_keyboard())

@router.message(Command("delete"))
async def cmd_delete(message: types.Message):
    """Удаляет слово из словаря пользователя."""
    user = message.from_user
    words = message.text.split()[1:]
    if len(words) != 1:
        await message.answer('Использование: /delete <ID слова>', reply_markup=get_main_keyboard())
        return

    user_word_id = words[0]
    try:
        user_word_id = int(user_word_id)
    except ValueError:
        await message.answer('ID слова должен быть числом.', reply_markup=get_main_keyboard())
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
                await message.answer(f"Слово с ID {user_word_id} удалено.", reply_markup=get_main_keyboard())
            else:
                await message.answer("Произошла ошибка при удалении слова.", reply_markup=get_main_keyboard())
        else:
            await message.answer(f"Слово с ID {user_word_id} не найдено.", reply_markup=get_main_keyboard())
    else:
        await message.answer("Произошла ошибка при получении списка слов.", reply_markup=get_main_keyboard())

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
            await message.answer("Правильно!", reply_markup=get_main_keyboard())
        else:
            await message.answer(f"Неправильно. Правильный перевод: {translation}", reply_markup=get_main_keyboard())
        del users_learning[user_id]

dp.include_router(router)

async def main():
    """Запускает бота."""
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
