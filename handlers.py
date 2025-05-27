import logging
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from database import (
    add_birthday, get_birthdays, delete_birthday, edit_birthday,
    set_user_locale, get_user_locale
)
from reminder import set_reminder
from vcf_parser import parse_vcf
from i18n import _
from config import ADMIN_IDS

from aiogram.dispatcher.middlewares.base import BaseMiddleware
from typing import Callable, Awaitable, Dict, Any
from contextlib import contextmanager 

from aiogram.utils.i18n import I18n
from pathlib import Path
from config import I18N_DOMAIN
# Путь к папке с переводами


# FSM-сценарий для добавления дня рождения
class AddBirthday(StatesGroup):
    waiting_for_name = State()
    waiting_for_date = State()

# Универсальные локализованные подписи для главного меню
def MENU_KEYS():
    return {
        "list": f"📅 {_('Список')}",
        "add": f"➕ {_('Добавить')}",
        "broadcast": f"📢 {_('Рассылка')}",
        "settings": f"⚙️ {_('Настройки')}",
    }

# Генерация главного меню в текущей локали
def get_main_menu():
    keys = MENU_KEYS()
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=keys["list"]), KeyboardButton(text=keys["add"])],
            [KeyboardButton(text=keys["broadcast"]), KeyboardButton(text=keys["settings"])]
        ],
        resize_keyboard=True
    )

# Middleware для автоприменения языка пользователя
class LocaleMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable[[types.Message, Dict[str, Any]], Awaitable[Any]], event: types.Message, data: Dict[str, Any]) -> Any:
        user_id = event.from_user.id
        event._locale = get_user_locale(user_id)
        return await handler(event, data)

router = Router()
router.message.middleware(LocaleMiddleware())

# Обработка /start
@router.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(_("Добро пожаловать! Выберите действие в меню."), reply_markup=get_main_menu())

# Смена языка
@router.message(F.text.func(lambda t: t and any(lang in t for lang in ["Русский", "English", "Українська", "Português"])))
async def set_language(message: types.Message):
    text = message.text.strip()
    user_id = message.from_user.id
    new_locale = None
    logging.info(f"Установка языка для пользователя {user_id}: {text}")
    logging.info(f"Проверка переменных new_locale {new_locale} и текст {text}")
    # Устанавливаем язык в базе данных и в контексте сообщения
    if "Русский" in text:
        set_user_locale(user_id, 'ru')
        await message.answer("Язык установлен: 🇷🇺 Русский")
        new_locale = 'ru'
    elif "English" in text:
        set_user_locale(user_id, 'en')
        await message.answer("Language set to: 🇺🇸 English")
        new_locale = 'en'
    elif "Українська" in text:
        set_user_locale(user_id, 'uk')
        await message.answer("Мову встановлено: 🇺🇦 Українська")
        new_locale = 'uk'
    elif "Português" in text:
        set_user_locale(user_id, 'pt')
        await message.answer("Idioma definido: 🇵🇹 Português")
        new_locale = 'pt'
    logging.info(f"Проверка переменных new_locale {new_locale} и текст {text}")
    if new_locale:
        # Используем временный переводчик с новым языком
        LOCALES_DIR = Path(__file__).parent / "locales"
        temp_i18n = I18n(path=LOCALES_DIR, default_locale=new_locale, domain=I18N_DOMAIN)
        _t = temp_i18n.gettext  # функция перевода для нового языка
        # Генерируем главное меню сразу на нужном языке
        def temp_menu():
            return ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text=f"📅 {_t('Список')}"), KeyboardButton(text=f"➕ {_t('Добавить')}")],
                    [KeyboardButton(text=f"📢 {_t('Рассылка')}"), KeyboardButton(text=f"⚙️ {_t('Настройки')}")]
                ],
                resize_keyboard=True
            )
        
    await message.answer(_t("Добро пожаловать! Выберите действие в меню."), reply_markup=get_main_menu())

@contextmanager
def force_locale(locale_code):
    import builtins
    old_gettext = _
    from i18n import i18n
    i18n.set_locale(locale_code)
    yield
    i18n.set_locale(locale_code)  # вернём обратно

# УНИВЕРСАЛЬНЫЙ обработчик для всех кнопок главного меню
@router.message()
async def main_menu_handler(message: types.Message, state: FSMContext):
    keys = MENU_KEYS()
    text = message.text

    if text == keys["list"]:
        user_id = message.from_user.id
        bdays = get_birthdays(user_id)
        if not bdays:
            await message.answer(_("Список пуст."))
        else:
            reply = "\n".join([f"{b['name']}: {b['date']}" for b in bdays])
            await message.answer(reply)

    elif text == keys["add"]:
        await message.answer(_("Введите имя:"))
        await state.set_state(AddBirthday.waiting_for_name)
        await state.update_data(user_id=message.from_user.id)

    elif text == keys["broadcast"]:
        await message.answer(_("Чтобы воспользоваться рассылкой, используйте /broadcast текст_сообщения"))

    elif text == keys["settings"]:
        buttons = [
            [KeyboardButton(text="🇷🇺 Русский"), KeyboardButton(text="🇺🇸 English")],
            [KeyboardButton(text="🇺🇦 Українська"), KeyboardButton(text="🇵🇹 Português")]
        ]
        lang_menu = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=buttons)
        await message.answer(_("Выберите язык:"), reply_markup=lang_menu)

# FSM: ждём имя
@router.message(AddBirthday.waiting_for_name)
async def add_birthday_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(_("Введите дату рождения (дд.мм):"))
    await state.set_state(AddBirthday.waiting_for_date)

# FSM: ждём дату
@router.message(AddBirthday.waiting_for_date)
async def add_birthday_date(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get('user_id') or message.from_user.id
    name = data.get('name')
    date = message.text
    add_birthday(user_id, name, date)
    await message.answer(_("День рождения добавлен!"), reply_markup=get_main_menu())
    await state.clear()

# Обработка ручных слэш-команд (на случай, если пользователь ими пользуется)
@router.message(Command("list"))
async def list_cmd(message: types.Message):
    user_id = message.from_user.id
    bdays = get_birthdays(user_id)
    if not bdays:
        await message.answer(_("Список пуст."))
    else:
        reply = "\n".join([f"{b['name']}: {b['date']}" for b in bdays])
        await message.answer(reply)

@router.message(Command("delete"))
async def delete_cmd(message: types.Message):
    user_id = message.from_user.id
    name = message.text.replace("/delete", "").strip()
    if delete_birthday(user_id, name):
        await message.answer(_("Удалено."))
    else:
        await message.answer(_("Не найдено."))

@router.message(Command("edit"))
async def edit_cmd(message: types.Message):
    user_id = message.from_user.id
    args = message.text.replace("/edit", "").strip().split()
    if len(args) >= 2:
        name, new_date = args[0], args[1]
        if edit_birthday(user_id, name, new_date):
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
        [KeyboardButton(text="🇺🇦 Українська"), KeyboardButton(text="🇵🇹 Português")]
    ]
    lang_menu = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=buttons)
    await message.answer(_("Выберите язык:"), reply_markup=lang_menu)


def register_handlers(dp):
    dp.include_router(router)
# Регистрация обработчиков в диспетчере
