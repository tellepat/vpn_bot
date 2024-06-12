import logging
from datetime import datetime, timedelta, timezone, time

import requests
from telegram import Update, LabeledPrice, KeyboardButton, ReplyKeyboardMarkup, Bot
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, PreCheckoutQueryHandler,
    filters, CallbackContext
)
from dotenv import load_dotenv
from os import getenv
import json
import outline_api
from db import get_client, get_db, Client, init_db, save_client

load_dotenv()
init_db()

TOKEN = "2200439744:AAG6Aq2kye2fBVAfCc9Wg1g-bFFp5OwlyLY/test"  # getenv("BOT_TOKEN")

# Получение значений и разделение их на список, после преобразование их из str в int
admin_chat_ids = getenv('ADMIN_CHAT_ID').split(',')
admin_chat_ids = [int(chat_id) for chat_id in admin_chat_ids]

# map серверов
servers_api_url = json.loads(getenv('SERVERS_API_URL'))

# Глобальная переменная для хранения выбранных параметров
pay_chat_ids = []

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"Привет, {update.message.from_user.full_name}!\n"
                                    "Я бот для управления конфигурациями VPN. Вот список доступных команд:\n"
                                    "/start - запуск бота\n"
                                    "/help - справка по командам\n"
                                    "/buy - покупка конфигурации\n"
                                    "/support текст вашего обращения - связь с администратором")


async def help_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Я бот для управления конфигурациями VPN. Вот список доступных команд:\n"
                                    "/start - запуск бота\n"
                                    "/help - справка по командам\n"
                                    "/buy - покупка конфигурации\n"
                                    "/support текст вашего обращения - связь с администратором")


async def support(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    message_text = update.message.text.replace("/support", "").strip()

    if user_id not in admin_chat_ids:
        await context.bot.send_message(admin_chat_ids[0], f"{message_text} {user_id}")
    else:
        parts = message_text.split(maxsplit=1)
        print(parts)
        if len(parts) > 1:
            target_id = int(parts[0])
            response_text = parts[1]
            await context.bot.send_message(target_id, response_text)


# Функция для отправки клавиатуры с выбором сервера
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [[KeyboardButton(server)] for server in servers_api_url.keys()]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text("Выберите протокол и сервер:", reply_markup=reply_markup)


# Функция для обработки выбора сервера и инициирования платежа
async def server_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    server_choice = update.message.text

    try:
        with next(get_db()) as db:
            client = get_client(db, chat_id)

            if client:
                outline_key = client.outline_key.get(server_choice)
                wireguard_config = client.wireguard_config.get(server_choice)

                if outline_key:
                    await update.message.reply_text(
                        f"У вас уже куплен доступ к данному серверу! URL: `{outline_key}`",
                        parse_mode='Markdown'
                    )
                    return

                if wireguard_config:
                    # Сохранение конфигурации в файл
                    file_path = f"{chat_id}_{server_choice}_config.conf"
                    with open(file_path, 'w') as file:
                        file.write(wireguard_config)
                    # Отправка файла клиенту
                    await context.bot.send_document(chat_id, document=open(file_path, 'rb'))
                    await update.message.reply_text(
                        f"У вас уже куплен доступ к данному серверу!",
                        parse_mode='Markdown'
                    )
                    return
    except Exception as e:
        await context.bot.send_message(chat_id, f"Произошла ошибка при обработке вашего запроса: {e}")

    # Если ещё не прикупили сервер высылаем платёж
    pay_chat_ids.append(str(chat_id))

    await send_invoice(context.bot, chat_id, server_choice, False)


async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.pre_checkout_query
    if str(query.from_user.id) not in pay_chat_ids:
        await query.answer(ok=False, error_message="Something went wrong...")
        print(query.from_user.id)
        print(pay_chat_ids)
    else:
        await query.answer(ok=True)


# Функция для обработки успешного платежа
async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    invoice_payload = update.message.successful_payment.invoice_payload
    server, payment_type = invoice_payload.split(":")
    api_url = servers_api_url[server]

    print(f"Платеж успешен! Сервер: {server}, API URL: {api_url}, тип платежа {'Повторный' if payment_type == 'reneval' else payment_type}")
    await update.message.reply_text("Спасибо за ваш платеж!")

    with next(get_db()) as db:
        client = get_client(db, chat_id)
        if not client:
            client = Client(
                chat_id=chat_id,
                wireguard_config={},
                outline_key={},
                payment_dates={}
            )

        if payment_type == "renewal":
            next_payment_date = datetime.now(timezone.utc) + timedelta(days=1)
            client.payment_dates[server] = next_payment_date.isoformat()
            save_client(db, client)
            print(client.payment_dates)
            return

        if "Outline" in server:
            access_url = outline_api.add_access_url(str(chat_id), *servers_api_url[server].split("^"))
            await update.message.reply_text(
                f"Ваш URL для доступа к outline: `{access_url}`",
                parse_mode='Markdown'
            )
            client.outline_key[server] = access_url
        else:
            config = await handle_wireguard_payment(chat_id, server, context)
            # Сохранение конфигурации в файл
            file_path = f"{chat_id}_{server}_config.conf"
            with open(file_path, 'w') as file:
                file.write(config)
            # Отправка файла клиенту
            await context.bot.send_document(chat_id, document=open(file_path, 'rb'))
            client.wireguard_config[server] = config
        next_payment_date = datetime.now(timezone.utc) + timedelta(days=1)
        client.payment_dates[server] = next_payment_date.isoformat()
        save_client(db, client)
        print(client.payment_dates[server])


async def handle_wireguard_payment(chat_id: int, server: str, context: ContextTypes.DEFAULT_TYPE) -> str:
    url = servers_api_url[server]
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "name": str(chat_id)
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        await context.bot.send_message(chat_id, f"Ваш конфиг для доступа к wireguard: {response.text}")
        return response.text
    except requests.exceptions.HTTPError as http_err:
        await context.bot.send_message(admin_chat_ids[0], f"HTTP ошибка: {http_err}")
        return ""
    except requests.exceptions.RequestException as err:
        await context.bot.send_message(admin_chat_ids[0], f"Ошибка запроса: {err}")
        return ""


async def notify_users(context: CallbackContext) -> None:
    db = next(get_db())
    try:
        clients = db.query(Client).all()
        for client in clients:
            if not client.payment_dates:
                continue

            for server, payment_date in client.payment_dates.items():
                payment_date = datetime.fromisoformat(payment_date)

                if payment_date - timedelta(days=1) <= datetime.now(timezone.utc):
                    pay_chat_ids.append(str(client.chat_id))
                    await context.bot.send_message(client.chat_id,
                        f"Ваш платеж за {server} истекает завтра. Пожалуйста, оплатите для продолжения использования сервиса.")
                    await send_invoice(context.bot, client.chat_id, server, True)

                if payment_date <= datetime.now(timezone.utc):
                    await context.bot.send_message(client.chat_id,
                                                   f"Ваш платеж за {server} просрочен. Конфигурация удалена с сервера.")
                    if "Outline" in server:
                        client.outline_key.pop(server, None)
                        outline_api.delete_access_url(client.chat_id, *servers_api_url[server].split("^"))
                    else:
                        client.wireguard_config.pop(server, None)
                        # TODO: Добавить удаление конфигурации wireguard
                    client.payment_dates.pop(server, None)
                    db.commit()
                    db.refresh(client)
    finally:
        db.close()


async def send_invoice(bot: Bot, chat_id: int, server: str, is_renewal: bool = False):
    title = f"{server} Service {'Renewal' if is_renewal else 'Purchase'}"
    description = f"Пожалуйста, оплатите для продолжения использования {server} сервиса." if is_renewal else f"Пожалуйста, оплатите для использования {server} сервиса."
    payload = f"{server}:{'renewal' if is_renewal else 'new'}"
    provider_token = ""
    currency = "XTR"
    prices = [LabeledPrice(f"{server} Service {'Renewal' if is_renewal else 'Purchase'}", 75)]
    start_parameter = "renewal-payment" if is_renewal else "new-payment"

    await bot.send_invoice(
        chat_id, title, description, payload, provider_token, currency, prices, start_parameter
    )


def main() -> None:
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_message))
    application.add_handler(CommandHandler('buy', buy))
    application.add_handler(MessageHandler(filters.Regex('|'.join(servers_api_url.keys())), server_choice))
    application.add_handler(CommandHandler('support', support))
    application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))

    job_queue = application.job_queue
    time_to_run = time(hour=10, minute=0, second=0, tzinfo=timezone(timedelta(hours=3)))  # Устанавливаем время запуска
    job_queue.run_daily(notify_users, time_to_run)

    print("Scheduler set to run at 15:13 daily")  # Отладочное сообщение

    # Вывод текущих задач планировщика
    for job in job_queue.jobs():
        print(f"Job: {job.name}, next run: {job}")

    application.run_polling()


if __name__ == '__main__':
    main()
