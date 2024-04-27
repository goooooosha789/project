from data import db_session
import logging
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ConversationHandler
from data.users import User
import os
from yandex_music import Client

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

client = Client().init()
logger = logging.getLogger(__name__)
db_session.global_init("db/users.db")
db_sess = db_session.create_session()
file = 'db/Заполнитель, удалить после скачивания.odt'
if os.path.exists(file):
    os.remove(file)

start_scheme = [['Файл'], ['Текст'], ['Список избранных']]
start_keyboard = ReplyKeyboardMarkup(start_scheme, resize_keyboard=True)
final_scheme = [['Назад'], ['Добавить в избранное']]
final_keyboard = ReplyKeyboardMarkup(final_scheme, resize_keyboard=True)
favorites_scheme = [['Назад'], ['Удалить']]
favorites_keyboard = ReplyKeyboardMarkup(favorites_scheme, resize_keyboard=True)


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
    input_text = update.message.text
    search_result = client.search(input_text)

    text = [f'Результаты по запросу "{input_text}":', '']

    best_result_text = ''
    if search_result.best:
        type_ = search_result.best.type
        best = search_result.best.result
        if type_ == 'track':
            artists = ''
            if best.artists:
                artists = ' - ' + ', '.join(artist.name for artist in best.artists)
            best_result_text = best.title + artists

        text.append(f'Лучший результат: {best_result_text}\n')
        user_id = update.effective_user.id
        user = db_sess.query(User).filter(User.id == user_id).first()
        im = search_result.best.result.cover_uri
        im = im[:-2] + '200x200'
        user.last_search = f'{best_result_text}___{im}'
        db_sess.commit()
        await context.bot.send_photo(chat_id=update.message.chat_id,
                                     photo=f'https://{im}')
        await update.message.reply_text('\n'.join(text) + user.last_search, reply_markup=final_keyboard)

        return 3
    else:
        await update.message.reply_text('Не найденно, введите другой текст')
        return 1


async def active_audio(update, context):
    await update.message.reply_text('Извините, функция не доступна в данный момент', reply_markup=start_keyboard)

    return ConversationHandler.END


async def find_audio(update, context):
    await update.message.reply_text('нашел', reply_markup=final_keyboard)

    return 3


async def final(update, context):
    user_id = update.effective_user.id
    user = db_sess.query(User).filter(User.id == user_id).first()
    if not user.favorites:
        user.favorites = user.last_search
    else:
        if user.last_search not in user.favorites:
            user.favorites = f'{user.favorites}, {user.last_search}'
        else:
            await update.message.reply_text(f'Уже есть в избранных', reply_markup=start_keyboard)
            return ConversationHandler.END
    user.last_search = None
    db_sess.commit()
    await update.message.reply_text(f'Добавлено в избранное', reply_markup=start_keyboard)
    return ConversationHandler.END


async def back(update, context):
    await update.message.reply_text(update.message.text, reply_markup=start_keyboard)
    return ConversationHandler.END


async def favorites(update, context):
    user_id = update.effective_user.id
    user = db_sess.query(User).filter(User.id == user_id).first()
    if not user.favorites:
        await update.message.reply_text('В избранном ничего нет', reply_markup=start_keyboard)
        return ConversationHandler.END
    else:
        sp = user.favorites.split(', ')
        for i in range(len(sp)):
            j = sp[i].split('___')
            await update.message.reply_text(f'{i + 1} {j[0]}', reply_markup=start_keyboard)
            await context.bot.send_photo(chat_id=update.message.chat_id,
                                         photo=j[1], reply_markup=favorites_keyboard)
        return 4


async def delete_active(update, context):
    await update.message.reply_text(text='Введите номера для удаления через ", " для удаления',
                                    reply_markup=ReplyKeyboardRemove())
    return 5


async def delete(update, context):
    user_id = update.effective_user.id
    user = db_sess.query(User).filter(User.id == user_id).first()
    input_text = update.message.text
    sp = user.favorites
    sp = sp.split(',')
    input_text = input_text.split(',')
    new_input = []
    try:
        for i in input_text:
            new_input.append(int(i))
    except ValueError:
        await update.message.reply_text('Неверный ввод')
        return 5
    await update.message.reply_text(new_input)
    new_input.sort(reverse=True)
    try:
        for i in new_input:
            sp.pop(i - 1)
    except IndexError:
        await update.message.reply_text('Неверный номер')
        return 5
    user.favorites = ', '.join(sp)
    db_sess.commit()
    await update.message.reply_text('Удалено', reply_markup=start_keyboard)
    return ConversationHandler.END


with open('TOKEN') as f:
    TOKEN = f.read()


def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Text(['Текст']), active_text),
                      MessageHandler(filters.Text(['Файл']), active_audio),
                      MessageHandler(filters.Text(['Список избранных']), favorites)],
        states={
            1: [MessageHandler(filters.TEXT, found_text)],
            2: [MessageHandler(filters.AUDIO, find_audio)],
            3: [MessageHandler(filters.Text(['Добавить в избранное']), final)],
            4: [MessageHandler(filters.Text(['Удалить']), delete_active)],
            5: [MessageHandler(filters.TEXT, delete)]
        },
        fallbacks=[MessageHandler(filters.Text(['Назад']), back)]
    )
    application.add_handler(conv_handler)
    application.run_polling()


if __name__ == '__main__':
    main()
