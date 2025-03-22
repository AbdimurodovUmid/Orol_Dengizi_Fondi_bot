import aiosqlite
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher.filters import Text

# 🔹 Bot ma'lumotlari
TOKEN = "7397862920:AAHwlNZv6HYDsOtfRBZg-4cSjLBPtGGjysY"  # Bot tokeningizni kiriting
ADMIN_ID = 6141812477  # O‘z ID raqamingizni kiriting
PUL_YECHISH_BOT = "@Orol_Dengizi_Fondi_Admin_Bot"  # ✅ Pul yechish uchun yangi manzil
BOT_USERNAME = "Orol_Dengizi_Fondi_bot"  # Bot username
MIN_WITHDRAW_AMOUNT = 6000  # ✅ Minimal pul yechish summasi 6000 so‘m

# 🔹 Bot va dispatcher
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# 🔹 Ma'lumotlar bazasi
db = None  # Global bazaga ulanish

async def on_startup(dp):
    global db
    db = await aiosqlite.connect("users.db")  # Baza ulanishi
    await db.execute(
        """CREATE TABLE IF NOT EXISTS users 
        (user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0, invited_by INTEGER)"""
    )
    await db.commit()

async def on_shutdown(dp):
    await db.close()  # Baza ulanishini yopish

# 📌 Foydalanuvchi tugmalari
user_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
user_keyboard.add(KeyboardButton("💰 Balansim"), KeyboardButton("📢 Referallarim"))
user_keyboard.add(KeyboardButton("💸 Pul yechish"))

# 📌 Admin tugmalari
admin_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
admin_keyboard.add(KeyboardButton("📊 Referallar ro‘yxati"))

# 📌 /start komandasi
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user_id = message.from_user.id
    args = message.text.split()
    referal_id = int(args[1]) if len(args) > 1 and args[1].isdigit() and int(args[1]) != user_id else None  # O‘zini o‘zi referal qila olmaydi

    async with db.execute("SELECT * FROM users WHERE user_id=?", (user_id,)) as cursor:
        user = await cursor.fetchone()

    if not user:
        await db.execute("INSERT INTO users (user_id, invited_by) VALUES (?, ?)", (user_id, referal_id))
        await db.commit()

        if referal_id:
            await db.execute("UPDATE users SET balance = balance + 3000 WHERE user_id=?", (referal_id,))
            await db.commit()

        ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
        await message.answer(
            f"👋 Assalomu alaykum! Orol Dengizi Fondi botiga xush kelibsiz!\n\n"
            f"✅ Sizning referal havolangiz:\n{ref_link}\n\n"
            f"📢 Har bir taklif qilgan foydalanuvchi uchun 3000 so‘m mukofot olasiz!",
            reply_markup=user_keyboard
        )
    else:
        await message.answer("Siz allaqachon botdan foydalanyapsiz!", reply_markup=user_keyboard)

# 📌 Balansni ko‘rsatish
@dp.message_handler(Text(equals="💰 Balansim"))
async def show_balance(message: types.Message):
    user_id = message.from_user.id
    async with db.execute("SELECT balance FROM users WHERE user_id=?", (user_id,)) as cursor:
        balance = await cursor.fetchone()

    balance = balance[0] if balance else 0
    await message.answer(f"💰 Sizning balansingiz: {balance} so‘m")

# 📌 Referallar ro‘yxatini ko‘rsatish
@dp.message_handler(Text(equals="📢 Referallarim"))
async def show_referrals(message: types.Message):
    user_id = message.from_user.id
    async with db.execute("SELECT user_id FROM users WHERE invited_by=?", (user_id,)) as cursor:
        referrals = await cursor.fetchall()

    referrals_list = "\n".join([f"👤 {r[0]}" for r in referrals]) if referrals else "Siz hali hech kimni taklif qilmagansiz."

    if len(referrals_list) > 4000:
        referrals_list = referrals_list[:4000] + "\n...\n📢 Ro‘yxat juda uzun!"

    await message.answer(f"📋 Siz taklif qilgan foydalanuvchilar:\n{referrals_list}")

# 📌 Pul yechish
@dp.message_handler(Text(equals="💸 Pul yechish"))
async def withdraw_request(message: types.Message):
    user_id = message.from_user.id
    async with db.execute("SELECT balance FROM users WHERE user_id=?", (user_id,)) as cursor:
        balance = await cursor.fetchone()

    balance = balance[0] if balance else 0

    if balance >= MIN_WITHDRAW_AMOUNT:  # ✅ Minimal limit 6000 so‘m
        await db.execute("UPDATE users SET balance = balance - ? WHERE user_id=? AND balance >= ?", (MIN_WITHDRAW_AMOUNT, user_id, MIN_WITHDRAW_AMOUNT))
        await db.commit()
        await message.answer(f"✅ Pul yechish so‘rovi yuborildi! Adminga yozing: {PUL_YECHISH_BOT}")
    else:
        await message.answer(f"❌ Pul yechish uchun kamida {MIN_WITHDRAW_AMOUNT} so‘m kerak!")

# 📌 Admin uchun referal tizimi
@dp.message_handler(Text(equals="📊 Referallar ro‘yxati"))
async def admin_referrals(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        async with db.execute("SELECT user_id, invited_by FROM users WHERE invited_by IS NOT NULL") as cursor:
            referrals = await cursor.fetchall()

        referral_list = "\n".join([f"👤 {r[0]} → Taklif qilgan: {r[1]}" for r in referrals]) if referrals else "Hali hech kim hech kimni taklif qilmagan."

        if len(referral_list) > 4000:
            referral_list = referral_list[:4000] + "\n...\n📢 Ro‘yxat juda uzun!"

        await message.answer(f"📊 Referallar ro‘yxati:\n{referral_list}", reply_markup=admin_keyboard)
    else:
        await message.answer("❌ Siz admin emassiz!")

# 🔹 Botni ishga tushirish
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown)