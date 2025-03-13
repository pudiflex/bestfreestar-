from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters
import json
import os

# Файл для хранения данных пользователей
USER_DATA_FILE = "user_data.json"

# Твой ID в Telegram для уведомлений
ADMIN_ID = "7863333069"  # Замени на свой ID

# Загрузка данных пользователей
def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as file:
            return json.load(file)
    return {}

# Сохранение данных пользователей
def save_user_data(data):
    with open(USER_DATA_FILE, "w") as file:
        json.dump(data, file)

# Создание клавиатуры с кнопками
def create_keyboard():
    keyboard = [
        [InlineKeyboardButton("📌 Заработать звёзды", callback_data='earn_stars')],
        [InlineKeyboardButton("📅 Вывести звёзды", callback_data='withdraw_stars')],
        [InlineKeyboardButton("📄 Задания", callback_data='tasks')],
        [InlineKeyboardButton("📅 Бонус", callback_data='bonus')],
        [InlineKeyboardButton("🔙 Назад", callback_data='back')]
    ]
    return InlineKeyboardMarkup(keyboard)

# Команда /start
def start(update: Update, context: CallbackContext) -> None:
    user_id = str(update.message.from_user.id)
    user_data = load_user_data()

    # Если пользователь новый, добавляем его в базу
    if user_id not in user_data:
        user_data[user_id] = {"stars": 0, "referrals": []}
        save_user_data(user_data)

    # Отправляем сообщение с кнопками
    update.message.reply_text(
        "Выберите действие:",
        reply_markup=create_keyboard()
    )

# Обработка нажатий на кнопки
def button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    user_id = str(query.from_user.id)
    user_data = load_user_data()

    if query.data == 'earn_stars':
        query.edit_message_text(
            text="📌 Вот способы заработать звёзды:\n\n"
                 "1. Пригласи друзей: +3 звезды за каждого.\n"
                 "2. Выполняй задания: смотри рекламу, проходи опросы.\n"
                 "3. Ежедневный бонус: +1 звезда каждый день.",
            reply_markup=create_keyboard()
        )
    elif query.data == 'withdraw_stars':
        if user_data[user_id]["stars"] >= 10:
            query.edit_message_text(
                text=f"📅 Твой баланс: {user_data[user_id]['stars']} звёзд.\n"
                      "Введите сумму для вывода (минимум 10 звёзд):"
            )
            context.user_data["awaiting_withdrawal"] = True
        else:
            query.edit_message_text(
                text="❌ Минимальная сумма для вывода — 10 звёзд. Продолжай зарабатывать!",
                reply_markup=create_keyboard()
            )
    elif query.data == 'tasks':
        query.edit_message_text(
            text="📄 Список заданий:\n\n"
                 "1. Пригласить друга: +3 звезды.\n"
                 "2. Смотреть рекламу: +3 звезды.\n"
                 "3. Пройти опрос: +2 звезды.",
            reply_markup=create_keyboard()
        )
    elif query.data == 'bonus':
        query.edit_message_text(
            text="🎉 Ты получил ежедневный бонус: +1 звезда!",
            reply_markup=create_keyboard()
        )
        user_data[user_id]["stars"] += 1
        save_user_data(user_data)
    elif query.data == 'back':
        query.edit_message_text(
            text="Главное меню:",
            reply_markup=create_keyboard()
        )

# Обработка текстовых сообщений (для вывода звёзд)
def handle_message(update: Update, context: CallbackContext) -> None:
    user_id = str(update.message.from_user.id)
    user_data = load_user_data()

    if context.user_data.get("awaiting_withdrawal"):
        try:
            amount = int(update.message.text)
            if amount < 10:
                update.message.reply_text("❌ Минимальная сумма для вывода — 10 звёзд.")
            elif amount > user_data[user_id]["stars"]:
                update.message.reply_text("❌ У тебя недостаточно звёзд.")
            else:
                # Отправляем заявку админу (тебе)
                context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=f"🚨 Новая заявка на вывод:\n\n"
                         f"ID пользователя: {user_id}\n"
                         f"Сумма: {amount} звёзд\n\n"
                         f"Подтверди или отклони заявку."
                )
                update.message.reply_text(
                    "✅ Заявка на вывод отправлена. Ожидай подтверждения.",
                    reply_markup=create_keyboard()
                )
                user_data[user_id]["stars"] -= amount
                save_user_data(user_data)
                context.user_data["awaiting_withdrawal"] = False
        except ValueError:
            update.message.reply_text("❌ Введите число.")
    else:
        update.message.reply_text("Используй кнопки для взаимодействия с ботом.")

def main() -> None:
    # Вставь сюда свой токен
    updater = Updater("YOUR_TELEGRAM_BOT_TOKEN")

    dispatcher = updater.dispatcher

    # Регистрация команд
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(button_handler))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Запуск бота
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()