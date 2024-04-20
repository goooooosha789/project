from data import db_session
import logging
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ConversationHandler
from data.users import User

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)
db_session.global_init("db/users.db")
db_sess = db_session.create_session()

start_scheme = [['Файл'], ['Текст']]
start_keyboard = ReplyKeyboardMarkup(start_scheme, resize_keyboard=True)
final_scheme = [['Назад'], ['Добавить в избранное']]
final_keyboard = ReplyKeyboardMarkup(final_scheme, resize_keyboard=True)


async def start(update, context):
    """Отправляет сообщение когда получена команда /start"""
    user = update.effective_user
    id = user.id
    db_users = db_sess.query(User).all()
    users_id = []
    for i in db_users:
        users_id.append(i.id)
    if id in users_id:
        await update.message.reply_html(rf"[rso {user.mention_html()}! Это музыКАЛьный бот",
                                        reply_markup=start_keyboard)
    else:
        new_user = User()
        new_user.id = user.id
        db_sess.add(new_user)
        db_sess.commit()
        await update.message.reply_html(rf"Привет {user.mention_html()}! Это музыКАЛьный бот",
                                        reply_markup=start_keyboard)


async def active_text(update, context):
    await update.message.reply_text('Ввод', reply_markup=ReplyKeyboardRemove())

    return 1


async def found_text(update, context):
    await update.message.reply_text(update.message.text, reply_markup=final_keyboard)

    return 69


async def active_audio(update, context):
    await update.message.reply_text('Ввод', reply_markup=ReplyKeyboardRemove())

    return 2


async def find_audio(update, context):
    await update.message.reply_text('нашел', reply_markup=final_keyboard)

    return 69


async def final(update, context):
    await update.message.reply_text('Добавить в избранное', reply_markup=start_keyboard)
    return ConversationHandler.END


async def back(update, context):
    await update.message.reply_text(update.message.text, reply_markup=start_keyboard)
    return ConversationHandler.END


def main():
    application = Application.builder().token('6789438153:AAGGlePMgoZs_77sU0t0pogs4tK3XwsOVEE').build()
    application.add_handler(CommandHandler("start", start))
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Text(['Текст']), active_text),
                      MessageHandler(filters.Text(['Файл']), active_audio)],
        states={
            1: [MessageHandler(filters.TEXT, found_text)],
            2: [MessageHandler(filters.AUDIO, find_audio)],
            69: [MessageHandler(filters.Text(['Добавить в избранное']), final)]
        },
        fallbacks=[MessageHandler(filters.Text(['Назад']), back)]
    )
    application.add_handler(conv_handler)
    application.run_polling()


if __name__ == '__main__':
    main()
