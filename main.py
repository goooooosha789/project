from data import db_session
import logging
import telegram
from telegram.ext import Application, MessageHandler, filters, CommandHandler
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)
db_session.global_init("db/blogs.db")


async def start(update, context):
    """Отправляет сообщение когда получена команда /start"""
    user = update.effective_user
    new_user = User()
    await update.message.reply_html(rf"Привет {user.mention_html()}! Это музыКАЛьный бот")


def main():
    application = Application.builder().token('6789438153:AAGGlePMgoZs_77sU0t0pogs4tK3XwsOVEE').build()
    application.add_handler(CommandHandler("start", start))

    application.run_polling()


if __name__ == '__main__':
    main()
