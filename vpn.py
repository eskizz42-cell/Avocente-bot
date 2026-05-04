import logging
import sqlite3
import asyncio
import asyncio
import sys

# Костыль для Windows и новых версий Python
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from aiogram.client.default import DefaultBotProperties

# --- НАСТРОЙКИ ---
API_TOKEN = '8577327030:AAGzwot1PVY-rhSJ4qgjwq6RhC0njinS_Fs'
ADMIN_ID = 8623822141  # ТВОЙ ID
CHANNEL_ID = -1003940752977  # ID КАНАЛА
CHANNEL_URL = "https://t.me/AvocenteVPN"
ADMIN_USERNAME = "@avocenteVPNsupport"


# В 3-й версии настройки Parse Mode делаются так:
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# --- БАЗА ДАННЫХ ---
conn = sqlite3.connect("users.db")
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
conn.commit()

# --- КЛАВИАТУРЫ ---
def main_kb():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 КУПИТЬ ПОДПИСКУ", callback_data="catalog")],
        [InlineKeyboardButton(text="👤 ПРОФИЛЬ", callback_data="profile"),
         InlineKeyboardButton(text="⚙️ НАСТРОЙКА", callback_data="setup")],
        [InlineKeyboardButton(text="🛡 О НАС", callback_data="about"),
         InlineKeyboardButton(text="🤝 ПОДДЕРЖКА", url=f"https://t.me{ADMIN_USERNAME.replace('@', '')}")]
    ])
    return kb

def catalog_kb():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🥉 1 месяц — 150₽", callback_data="buy_150")],
        [InlineKeyboardButton(text="🥈 3 месяца — 390₽ 🔥", callback_data="buy_390")],
        [InlineKeyboardButton(text="🥇 6 месяцев — 690₽ 🚀", callback_data="buy_690")],
        [InlineKeyboardButton(text="⬅️ НАЗАД", callback_data="start")]
    ])
    return kb

# --- ФУНКЦИИ ---
async def check_sub(user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except: return False

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (message.from_user.id,))
    conn.commit()

    if not await check_sub(message.from_user.id):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ ПОДПИСАТЬСЯ", url=CHANNEL_URL)],
            [InlineKeyboardButton(text="🔄 Я ПОДПИСАЛСЯ", callback_data="start")]
        ])
        await message.answer("✋ Сначала подпишись на наш канал!", reply_markup=kb)
        return

    text = (f"<b>Avocete VPN приветствует вас! 👋</b>\n\n"
            f"Локация: 🇳🇱 Амстердам | Скорость: 1 Гбит/с")
    await message.answer_photo(MAIN_IMG, caption=text, reply_markup=main_kb())

@dp.callback_query(F.data == "start")
async def back_to_start(call: types.CallbackQuery):
    if not await check_sub(call.from_user.id):
        await call.answer("❌ Вы не подписаны!", show_alert=True)
        return
    await call.message.edit_media(
        InputMediaPhoto(media=MAIN_IMG, caption="<b>Главное меню:</b>"),
        reply_markup=main_kb()
    )

@dp.callback_query(F.data == "catalog")
async def show_catalog(call: types.CallbackQuery):
    await call.message.edit_media(
        InputMediaPhoto(media=TARIFF_IMG, caption="<b>💳 Выберите тариф:</b>"),
        reply_markup=catalog_kb()
    )

@dp.callback_query(F.data.startswith("buy_"))
async def process_buy(call: types.CallbackQuery):
    amount = call.data.split('_')[1]
    await call.message.answer(f"✅ Заявка на {amount}₽ принята! Напиши {ADMIN_USERNAME} для оплаты.")
    await bot.send_message(ADMIN_ID, f"🔔 Заявка от @{call.from_user.username} на {amount}₽\nКоманда: <code>/send {call.from_user.id} КЛЮЧ</code>")

@dp.message(Command("send"))
async def send_key(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    parts = message.text.split(maxsplit=2)
    if len(parts) == 3:
        user_id, key = parts[1], parts[2]
        await bot.send_message(user_id, f"<b>✨ Твой доступ готов!</b>\n\nКлюч: <code>{key}</code>")
        await message.answer("Отправлено!")

@dp.message(Command("admin"))
async def admin_menu(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📢 РАССЫЛКА", callback_data="broadcast")]])
        await message.answer("🛠 Админ-панель", reply_markup=kb)

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен")
