import logging
import os

from database import create_schema

from telegram import Update, BotCommand
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from handlers import (
    handle_start,
    help_command,
    about_us,
    unknown_command,
    handle_rating,
    handle_photo,
    handle_non_photo_message,
)

# -------------------- LOGGING --------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("PixNameBot")

# -------------------- ENV --------------------

token = os.getenv("BOT_TOKEN")

if not token:
    logger.error("BOT_TOKEN environment variable is missing")
    raise RuntimeError("BOT_TOKEN is required")

# -------------------- BOT COMMANDS --------------------

async def setup_bot_commands(application):
    commands = [
        BotCommand("start", "Регистрация и приветствие"),
        BotCommand("help", "Список команд"),
        BotCommand("about_us", "Информация о боте"),
    ]
    await application.bot.set_my_commands(commands)

# -------------------- MAIN --------------------

def main():
    application = ApplicationBuilder().token(token).build()

    # handlers: commands
    application.add_handler(CommandHandler("start", handle_start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about_us", about_us))

    # handlers: photos
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # handlers: rating buttons
    application.add_handler(
        CallbackQueryHandler(handle_rating, pattern=r"^rate:\d+:\d+$")
    )

    # handlers: unknown commands
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    # handlers: plain text
    application.add_handler(
        MessageHandler(~filters.PHOTO & ~filters.COMMAND, handle_non_photo_message)
    )

    # database init
    create_schema()

    # async post-init hook
    application.post_init = setup_bot_commands

    logger.info("Bot started successfully")

    application.run_polling()

# --------------------

if __name__ == "__main__":
    main()
