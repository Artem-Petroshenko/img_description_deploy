import time

from telegram.ext import ContextTypes
from database import get_db, create_request, create_rating, create_user, is_user_exist
import logging
import os
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from RedisCache import get_cached_data, cache_data

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("PixNameBot")
ML_SERVICE_URL = os.getenv("ML_SERVICE_URL", "http://ml-cose-service:8001/api")


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    logger.info(f"New start message from {update.message.from_user.username}")

    db = next(get_db())

    create_user(db=db,
                chat_id=update.message.chat_id,
                first_name=update.message.from_user.first_name,
                last_name=update.message.from_user.last_name,
                link=update.message.from_user.link,
                username=update.message.from_user.username,
                registered_at=update.message.date)

    await update.message.reply_text(
        "Добро пожаловать! Вы успешно зарегистрированы.\n"
        "Используйте меню или команды: /help, /about_us"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start - регистрация и приветствие\n"
        "/help - список всех команд\n"
        "/about_us - информация о боте"
    )


async def about_us(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Я бот, который распознаёт объекты на изображениях при помощи AI.\n"
        "Загрузи картинку, и я опишу, что на ней!"
    )


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Извините, я не знаю такую команду. Попробуйте /help.")


async def ask_for_rating(update: Update, context: ContextTypes.DEFAULT_TYPE, request_id: int):
    keyboard = [[
        InlineKeyboardButton("1", callback_data=f"rate:{request_id}:1"),
        InlineKeyboardButton("2", callback_data=f"rate:{request_id}:2"),
        InlineKeyboardButton("3", callback_data=f"rate:{request_id}:3"),
        InlineKeyboardButton("4", callback_data=f"rate:{request_id}:4"),
        InlineKeyboardButton("5", callback_data=f"rate:{request_id}:5"),
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Оцените, насколько точным был результат:", reply_markup=reply_markup)


async def handle_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = next(get_db())
    query = update.callback_query
    await query.answer()

    try:
        _, request_id, rating = query.data.split(":")
        request_id = int(request_id)
        rating = int(rating)

        create_rating(db=db,
                      request_id=request_id,
                      user_id=update.effective_user.id,
                      rating=rating)
        await query.edit_message_text(f"Спасибо за вашу оценку: {rating}!")
    except Exception as e:
        logger.error("Ошибка при обработке оценки:", e)
        await query.edit_message_text("Произошла ошибка при сохранении оценки.")

    db.close()


async def handle_non_photo_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Пожалуйста, отправьте изображение. Бот обрабатывает только картинки 📷.")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_time = time.time()
    db = next(get_db())
    photo_file = await update.message.photo[-1].get_file()
    file_url = photo_file.file_path

    logger.info(f"New request from {update.message.from_user.username} - {file_url} ")
    if not is_user_exist(db, update.message.chat_id):
        logger.error(f"Unknown user with chat_id: {update.message.chat_id}")
        await update.message.reply_text(f"Ошибка! Неизвестный пользователь...")
        return

    await update.message.reply_text(f"Картинку получил, Идет обработка...")

    try:
        cached_desc = await get_cached_data(file_url)

        if cached_desc is not None:
            await update.message.reply_text(str(cached_desc))

            execution_time = time.time() - start_time

            request_id = create_request(
                db=db,
                id=update.message.id,
                user_id=update.message.chat_id,
                photo_url=file_url,
                response=cached_desc,
                timestamp=update.message.date,
                execution_time=execution_time,
                success=True
            )

            await ask_for_rating(update, context, request_id=request_id)
            return

    except Exception as e:
        logger.error(f"Error with Redis: {e}")

    context.application.create_task(
        process_image_async(update, context, file_url, db)
    )

    db.close()


async def process_image_async(update: Update, context: ContextTypes.DEFAULT_TYPE, file_url: str, db):
    start_time = time.time()
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            response = await client.post(
                ML_SERVICE_URL + "/caption",
                json={"image_url": file_url}
            )

            if response.status_code != 200:
                await update.message.reply_text(f"Не удалось получить доступ к картинке",
                                                reply_to_message_id=update.message.message_id
                                                )
                return

            data = response.json()
            captions = data["captions"]

            if not captions:
                await update.message.reply_text("Не удалось сгенерировать описание.",
                                                reply_to_message_id=update.message.message_id)
                return

            result_text = "Вот возможные варианты описания:\n\n"
            for i, caption in enumerate(captions, 1):
                en = caption.get("en", "—")
                ru = caption.get("ru", "—")
                result_text += f"{i}. EN: {en}\n   RU: {ru}\n\n"

            execution_time = time.time() - start_time

            request_id = create_request(
                db=db,
                id=update.message.id,
                user_id=update.message.chat_id,
                photo_url=file_url,
                response=result_text.strip(),
                timestamp=update.message.date,
                execution_time=execution_time,
                success=True
            )

            await update.message.reply_text(
                result_text.strip(),
                reply_to_message_id=update.message.message_id
            )

            await cache_data(file_url, result_text.strip())

            await ask_for_rating(update, context, request_id=request_id)

        except Exception as e:

            create_request(db=db,
                           id=update.message.id,
                           user_id=update.message.chat_id,
                           photo_url=file_url,
                           response=result_text.strip(),
                           timestamp=update.message.date,
                           success=False
                           )
            logger.error(f"Произошла ошибка: {str(e)}")
            await update.message.reply_text(f"Не удалось сгенерировать описание.",
                                            reply_to_message_id=update.message.message_id)

            await ask_for_rating(update, context, request_id=123)

