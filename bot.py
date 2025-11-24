import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

# === ТВОЙ ТОКЕН ПРЯМО ТУТ ===
BOT_TOKEN = "8221702811:AAFZDdlxEFt486b5n-HSEZKMTpH5IiftqDE"

# === ПОСТОЯННАЯ ССЫЛКА НА ФРОНТ ===
FRONT_URL = "https://luchwallet-frontend.vercel.app/?v=2"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# === КНОПКА WEBAPP ===
wallet_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Открыть кошелёк сотрудника",
                web_app=WebAppInfo(url=FRONT_URL)
            )
        ]
    ]
)

# === START ===
@dp.message(F.text == "/start")
async def start(message: types.Message):
    await message.answer(
        "Добро пожаловать!\n\nНажмите кнопку ниже, чтобы открыть кошелёк сотрудника.",
        reply_markup=wallet_keyboard
    )

# === ЛЮБОЕ ДРУГОЕ СООБЩЕНИЕ ===
@dp.message()
async def any_message(message: types.Message):
    await message.answer(
        "Нажмите кнопку ниже, чтобы открыть кошелёк.",
        reply_markup=wallet_keyboard
    )

async def main():
    print("Bot is running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
