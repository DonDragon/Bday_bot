# handlers.py
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from database import add_birthday, get_birthdays, delete_birthday, edit_birthday
from reminder import set_reminder
from vcf_parser import parse_vcf
from i18n import _
from config import ADMIN_IDS

from database import set_user_locale, get_user_locale

user_languages = {}
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from typing import Callable, Awaitable, Dict, Any

class LocaleMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable[[types.Message, Dict[str, Any]], Awaitable[Any]], event: types.Message, data: Dict[str, Any]) -> Any:
        user_id = event.from_user.id
        event._locale = get_user_locale(user_id)
        return await handler(event, data)

router = Router()
router.message.middleware(LocaleMiddleware())

def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=f"📅 {_('Список')}"), KeyboardButton(text=f"➕ {_('Добавить')}")],
            [KeyboardButton(text=f"📢 {_('Рассылка')}"), KeyboardButton(text=f"⚙️ {_('Настройки')}")]
        ],
        resize_keyboard=True
    )

@router.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(_("Добро пожаловать! Выберите действие в меню."), reply_markup=get_main_menu())

@router.message(Command("list"))
async def list_cmd(message: types.Message):
    bdays = get_birthdays()
    if not bdays:
        await message.answer(_("Список пуст."))
    else:
        reply = "\n".join([f"{b['name']}: {b['date']}" for b in bdays])
        await message.answer(reply)

@router.message(Command("delete"))
async def delete_cmd(message: types.Message):
    name = message.text.replace("/delete", "").strip()
    if delete_birthday(name):
        await message.answer(_("Удалено."))
    else:
        await message.answer(_("Не найдено."))

@router.message(Command("edit"))
async def edit_cmd(message: types.Message):
    args = message.text.replace("/edit", "").strip().split()
    if len(args) >= 2:
        name, new_date = args[0], args[1]
        if edit_birthday(name, new_date):
            await message.answer(_("Обновлено."))
            await set_reminder(name, new_date)
        else:
            await message.answer(_("Ошибка обновления."))
    else:
        await message.answer(_("Неверный формат. Пример: /edit Иван 13.07"))

@router.message(Command("broadcast"))
async def broadcast_cmd(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return await message.answer(_("Нет доступа."))
    text = message.text.replace("/broadcast", "").strip()
    if not text:
        return await message.answer(_("Введите текст рассылки."))
    await message.answer(_("Рассылка отправлена: \n") + text)

@router.message(Command("settings"))
async def settings_cmd(message: types.Message):
    buttons = [
        [KeyboardButton(text="🇷🇺 Русский"), KeyboardButton(text="🇺🇸 English")],
        [KeyboardButton(text="ua Українська"), KeyboardButton(text="pt Português")]
    ]
    lang_menu = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=buttons)
    await message.answer(_("Выберите язык:"), reply_markup=lang_menu)

@router.message(F.text.in_(["🇷🇺 Русский", "🇺🇸 English", "ua Українська", "pt Português"]))
async def set_language(message: types.Message):
    text = message.text
    user_id = message.from_user.id
    if text == "🇷🇺 Русский":
        user_languages[user_id] = 'ru'
        await message.answer("Язык установлен: Русский")
        set_user_locale(user_id, 'ru')
        message._locale = 'ru'
    elif text == "🇺🇸 English":
        user_languages[user_id] = 'en'
        await message.answer("Language set to: English")
        set_user_locale(user_id, 'en')
        message._locale = 'en'
    elif text == "ua Українська":
        user_languages[user_id] = 'uk'
        await message.answer("Мову встановлено: Українська")
        set_user_locale(user_id, 'uk')
        message._locale = 'uk'
    elif text == "pt Português":
        user_languages[user_id] = 'pt'
        await message.answer("Idioma definido: Português")
        set_user_locale(user_id, 'pt')
        message._locale = 'pt'

def register_handlers(dp):
    dp.include_router(router)
