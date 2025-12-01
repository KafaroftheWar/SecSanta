import telebot
import logging
import random
import sqlite3
from datetime import datetime

arr = []



logging.basicConfig(level=logging.INFO)


def log(message: str):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'[{timestamp}] {message}')


API_TOKEN = '8264647370:AAGB6K-2Rn0xGKZT--fI5deD-7XlxDlhaCk'
bot = telebot.TeleBot(API_TOKEN)


conn = sqlite3.connect('numbers.db', check_same_thread=False)
cursor = conn.cursor()


cursor.execute('''
CREATE TABLE IF NOT EXISTS numbers (
    number INTEGER PRIMARY KEY,
    tg_id INTEGER
)
''')

try:
    cursor.execute('ALTER TABLE numbers ADD COLUMN tg_id INTEGER')
except sqlite3.OperationalError:
    pass


cursor.execute('SELECT COUNT(*) FROM numbers')
if cursor.fetchone()[0] == 0:
    cursor.executemany(
        'INSERT INTO numbers (number, tg_id) VALUES (?, ?)',
        [(i, None) for i in range(1, 27)]
    )
    conn.commit()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    tg_id = message.from_user.id
    log(f'Пользователь с {tg_id} использовал команду /start')
    bot.reply_to(message, "Добро пожаловать! Напишите /getnumber, чтобы получить случайное число из списка.")
    bot.reply_to(message, 'В данном боте Вам будет отправлено лишь число. Число соответствует номеру в списке.')
    bot.reply_to(message, 'Нужно учесть 2 условия: \n1. Никому не сообщать выпавший номер, ведь это может разрушить всё мероприятие.\n\n2. Подарок должен стоить в районе 300 рублей. ( либо в районе оговоренной суммы )')

@bot.message_handler(commands=['getnumber'])
def get_number(message):
    tg_id = message.from_user.id
    log(f'Пользователь с {tg_id} использовал команду /getnumber')
    cursor.execute('SELECT number FROM numbers WHERE tg_id = ? LIMIT 1', (tg_id,))
    assigned = cursor.fetchone()

    if assigned:
        bot.reply_to(message, 'Нельзя получить больше 1 числа')
        return

    cursor.execute('SELECT number FROM numbers WHERE tg_id IS NULL ORDER BY RANDOM() LIMIT 1')
    result = cursor.fetchone()
    
    if result:
        number = result[0]
        cursor.execute('UPDATE numbers SET tg_id = ? WHERE number = ?', (tg_id, number))
        conn.commit()
        bot.reply_to(message, f'Вы получили число: {number}')
        bot.reply_to(message, 'Если у Вас возникли проблемы или вопросы, большая просьба написать в личку создателю Telegram бота — @PorodkoI. ВАЖНО!!! Это число остаётся до сброса БД. В случае повторной работы команды /getnumber. Вам будет выдана ошибка!!!')
    else:
        bot.reply_to(message, 'Все числа уже были использованы!')

@bot.message_handler(commands=['reset_adminapproved'])
def reset_numbers(message):
    tg_id = message.from_user.id
    if tg_id not in (814668182, 1187267919):
        bot.reply_to(message, 'Отказано в доступе.')
        log(f'Пользователь с {tg_id} безуспешно использовал команду reset')
    else:
        cursor.execute('DELETE FROM numbers')
        cursor.executemany(
            'INSERT INTO numbers (number, tg_id) VALUES (?, ?)',
            [(i, None) for i in range(1, 27)]
        )
        conn.commit()
        bot.reply_to(message, "Список чисел был сброшен.")
        log(f'Администратор с tg_id {tg_id} успешно использовал команду reset')

if __name__ == '__main__':
    bot.polling(none_stop=True)

conn.close()
