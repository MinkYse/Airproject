import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import F
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from re import Match
from datetime import datetime

from db import get_data

# Замените 'YOUR_BOT_TOKEN' на ваш токен Telegram бота
API_TOKEN = '6644534760:AAGNW1Wkjw5kw9fDjn68WdHZAvYKj50sPWM'

messages = {
    'ru': ['Язык успешно изменён',
           'Я не понимаю. Пожалуйста, используйте меню',
           'Введите номер вашего билета',
           'Найдена информация о рейсе',
           'Вылет',
           'Прибытие',
           'За неделю до вылета мы пришлем вам уведомление',
           'Информация о рейсе не найдена',
           'До вылета осталось 7 дней'],
    'en': ['Language change successfully',
           "I don't understand. Please use the menu",
           'Enter your ticket number',
           'Flight information received',
           'Departure',
           'Arrival',
           'We will send it to you a week before departure',
           'Flight information not found',
           '7 days left before departure']
}

menu = {
    'ru': ['✈ Информация о полёте ✈', '🛠 Смена языка 🛠'],
    'en': ['✈ Flight information ✈', '🛠 Switch language 🛠']
}

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN, parse_mode='HTML')
dp = Dispatcher()
scheduler = AsyncIOScheduler(timezone='Europe/Moscow')
logging.basicConfig(level=logging.INFO)


def get_menu_keyboard(lang_code):
    kb = [
        [
            types.KeyboardButton(text=menu[lang_code][0]),
            types.KeyboardButton(text=menu[lang_code][1])
        ],
    ]
    menu_keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, selective=True)
    return menu_keyboard

language_keyboard = InlineKeyboardBuilder()
language_keyboard.row(types.InlineKeyboardButton(text='🇺🇸 English', callback_data='en'))
language_keyboard.row(types.InlineKeyboardButton(text='🇷🇺 Русский', callback_data='ru'))

# Словарь для хранения выбранного языка
user_language = {}
user_notion = {}


@dp.message(Command('start'))
async def on_start(message: types.Message):
    user_id = message.from_user.id
    user_language[user_id] = message.from_user.language_code
    await message.answer("AirProject приветствует вас", reply_markup=get_menu_keyboard(user_language[user_id]))


@dp.callback_query(F.data.in_({'ru', 'en'}))
async def choose_language(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_language[user_id] = callback.data
    await callback.message.answer(messages[callback.data][0], reply_markup=get_menu_keyboard(user_language[user_id]))


@dp.message((F.text == menu['ru'][0]) | (F.text == menu['en'][0]))
async def show_ticket_info(message: types.Message):
    user_id = message.from_user.id
    language = user_language.get(user_id)
    await message.answer(messages[language][2])


@dp.message(F.text.regexp(r"^(\d{13})$").as_("ticket_no"))
async def ticketx_handler(message: types.Message, ticket_no: Match[str]):
    user_id = message.from_user.id
    language = user_language.get(user_id)
    try:
        data = get_data(ticket_no.string, language)
        await message.answer(f"""<b>{messages[language][3]}</b>
    🛫 {messages[language][4]}: {data[0].strftime('%d.%m.%Y %H:%M')} | {data[2]}
    🛬 {messages[language][5]}: {data[1].strftime('%d.%m.%Y %H:%M')} | {data[3]}
<b>{messages[language][6]}</b>""")
        user_notion[user_id] = ticket_no.string
    except:
        await message.answer(f'<b>{messages[language][7]}!</b>')


@dp.message((F.text == menu['ru'][1]) | (F.text == menu['en'][1]))
async def show_settings(message: types.Message):
    user_id = message.from_user.id
    await message.answer("Выберите язык / Choose your language:", reply_markup=language_keyboard.as_markup())


@dp.message()
async def echo(message: types.Message):
    user_id = message.from_user.id
    language = user_language.get(user_id)
    await message.answer(messages[language][1], reply_markup=get_menu_keyboard(language))


async def send_message(bot: Bot):
    for user_id, ticket_no in user_notion.items():
        language = user_language.get(user_id)
        data = get_data(ticket_no, language)
        if (data[0].replace(tzinfo=None) - datetime.now().replace(tzinfo=None)).days < 7:
            await bot.send_message(user_id, f"""⚠️<b>{messages[language][8]} ⚠️</b>
        🛫 {messages[language][4]}: {data[0].strftime('%d.%m.%Y %H:%M')} | {data[2]}
        🛬 {messages[language][5]}: {data[1].strftime('%d.%m.%Y %H:%M')} | {data[3]}""")




async def main():
    scheduler.add_job(send_message, trigger='interval', hours=2, kwargs={'bot': bot})
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())