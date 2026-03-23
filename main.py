import logging
import datetime
import csv
import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# ===== Настройки =====
TOKEN = os.getenv("BOT_TOKEN")
ADMINS = [123456789]  # ВСТАВЬ СВОЙ TELEGRAM ID
CSV_FILE = "registrations.csv"

logging.basicConfig(level=logging.INFO)

# ===== Создаём CSV =====
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "username", "telegram_id", "date"])

# ===== Обработчики =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Зарегистрироваться", callback_data="register")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Привет! Это проект Призма!\n\nХочешь зарегистрироваться на нашу лекцию?",
        reply_markup=reply_markup
    )

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    name = user.first_name
    username = user.username or ""
    user_id = user.id
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    # Проверка дубликатов
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if str(row["telegram_id"]) == str(user_id):
                await query.edit_message_text("Ты уже зарегистрирован!")
                return

    # Запись
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([name, username, user_id, date])

    await query.edit_message_text(
        "Ты успешно зарегистрирован!\n\nЛекция пройдет 17 апреля\nв 414 аудитории\nна Чапаева 16."
    )

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        return await update.message.reply_text("Нет доступа")

    users = []
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            users.append(f"{row['name']} (@{row['username']})")

    await update.message.reply_text("\n".join(users) or "Нет данных")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        return await update.message.reply_text("Нет доступа")

    with open(CSV_FILE, "r", encoding="utf-8") as f:
        users = list(csv.DictReader(f))

    await update.message.reply_text(f"Всего регистраций: {len(users)}")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        return await update.message.reply_text("Нет доступа")

    if not context.args:
        return await update.message.reply_text("Напиши текст")

    message = " ".join(context.args)

    with open(CSV_FILE, "r", encoding="utf-8") as f:
        users = list(csv.DictReader(f))

    sent = 0
    for user in users:
        try:
            await context.bot.send_message(chat_id=int(user["telegram_id"]), text=message)
            sent += 1
        except:
            pass

    await update.message.reply_text(f"Отправлено: {sent}")

# ===== Запуск =====
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(register))
app.add_handler(CommandHandler("list", list_users))
app.add_handler(CommandHandler("stats", stats))
app.add_handler(CommandHandler("broadcast", broadcast))

print("Бот запущен ✅")

app.run_polling()