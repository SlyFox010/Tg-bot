import asyncio
import os
import json
import gspread
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram import F
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv
from pathlib import Path

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)

# Загружаем .env файл
env_path = Path("C:/python_projects/.env")  # Указываем полный путь
load_dotenv(dotenv_path=env_path)

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("Ошибка: переменная окружения TOKEN не задана!")

# Получаем путь к текущему скрипту и загружаем фото.json
script_dir = os.path.dirname(os.path.abspath(__file__))  # Путь к текущей директории
with open(os.path.join(script_dir, 'foto.json'), 'rt') as jsonfile:
    credentials_data = json.load(jsonfile)

# Подключение к Google Sheets с данными из файла
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = creds = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
client = gspread.authorize(creds)
spreadsheet = client.open("Проект фото")
sheet = spreadsheet.worksheet("Проект фото")

# Инициализация бота
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Клавиатуры
start_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Начать задание")]],
    resize_keyboard=True
)

def get_category_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Качество")],
            [KeyboardButton(text="Ракурс")],
            [KeyboardButton(text="Рулетка")],
            [KeyboardButton(text="Валидно")],
            [KeyboardButton(text="Фото между ног")],  # Новый вариант ответа
            [KeyboardButton(text="Завершить работу")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer("Привет! Нажми 'Начать задание', чтобы получить фото.", reply_markup=start_keyboard)

async def get_unprocessed_photo():
    """Ищет первую строку с 'Не обработано' и возвращает её индекс и ссылку."""
    data = sheet.get_all_values()
    for i, row in enumerate(data[1:], start=2):
        if len(row) > 1 and row[1].strip().lower() == "не обработано" and row[0].startswith("http"):
            return i, row[0]
    return None, None

@dp.message(F.text == "Начать задание")
async def send_photo(message: Message):
    index, photo_url = await get_unprocessed_photo()  # Исправлено!

    if index:
        if not photo_url:
            await message.answer("Ошибка: ссылка на фото отсутствует.")
            return

        await message.answer_photo(photo_url, caption="Выберите категорию", reply_markup=get_category_keyboard())

        await asyncio.to_thread(sheet.batch_update, [
            {"range": f"B{index}", "values": [["В процессе"]] }
        ])
    else:
        await message.answer("Все фотографии обработаны!")

@dp.message(F.text.in_(["Качество", "Ракурс", "Рулетка", "Валидно", "Фото между ног"]))
async def handle_category_selection(message: Message):
    category = message.text

    data = sheet.get_all_values()
    for i, row in enumerate(data[1:], start=2):
        if row[1].strip().lower() == "в процессе":
            await asyncio.to_thread(sheet.batch_update, [
                {"range": f"B{i}", "values": [["Готово"]] },
                {"range": f"C{i}", "values": [[category]]}
            ])
            await message.answer(f"Фотография записана в категорию: {category}")
            await asyncio.sleep(1)
            await send_photo(message)
            return

    await message.answer("Ошибка: Не найдено фото в процессе обработки.")

@dp.message(F.text == "Завершить работу")
async def finish_task(message: Message):
    data = sheet.get_all_values()

    updates = [{"range": f"B{i}", "values": [["Не обработано"]]} for i, row in enumerate(data[1:], start=2) if row[1].strip().lower() == "в процессе"]

    if updates:
        await asyncio.to_thread(sheet.batch_update, updates)

    await message.answer(
        "Вы молодец, работа завершена! Вы сможете снова приступить к заданию, нажав кнопку 'Начать задание'.",
        reply_markup=start_keyboard
    )

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
