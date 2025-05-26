import logging
from pathlib import Path
from aiogram import types, Dispatcher
from aiogram.types import Update
from aiogram.utils.i18n import I18n, I18nMiddleware
from aiogram.utils.i18n.middleware import I18nMiddleware
from aiogram.types import Message, CallbackQuery
from config import I18N_DOMAIN
from database import get_user_locale, set_user_locale


# Путь к папке с переводами
LOCALES_DIR = Path(__file__).parent / "locales"

# Инициализация I18n
i18n = I18n(path=LOCALES_DIR, default_locale='ru', domain=I18N_DOMAIN)
_ = i18n.gettext  # Используется для перевода строк

# Кастомная middleware с реализацией get_locale
class CustomI18nMiddleware(I18nMiddleware):
    async def get_locale(self, event, data: dict) -> str:
        user_id = None
        tg_locale = 'en'

        # Если это Update, достаём message или callback_query
        if isinstance(event, Update):
            if event.message and event.message.from_user:
                user_id = event.message.from_user.id
                tg_locale = getattr(event.message.from_user, 'language_code', 'en')[:2]
            elif event.callback_query and event.callback_query.from_user:
                user_id = event.callback_query.from_user.id
                tg_locale = getattr(event.callback_query.from_user, 'language_code', 'en')[:2]
        # Если это Message (редко, но вдруг)
        elif isinstance(event, Message) and event.from_user:
            user_id = event.from_user.id
            tg_locale = getattr(event.from_user, 'language_code', 'en')[:2]
        elif isinstance(event, CallbackQuery) and event.from_user:
            user_id = event.from_user.id
            tg_locale = getattr(event.from_user, 'language_code', 'en')[:2]
        # fallback на случай других типов событий
        elif hasattr(event, 'from_user') and event.from_user:
            user_id = event.from_user.id
            tg_locale = getattr(event.from_user, 'language_code', 'en')[:2]

        logging.info(f"Получение Id пользователя {user_id} с языком {tg_locale}")
        # Если user_id не None, пытаемся получить локаль из базы
        
        if user_id is not None:
            db_locale = get_user_locale(user_id)
            logging.info(f"Получение локали для пользователя {user_id}: {db_locale}")
            if db_locale:
                return db_locale
            # если нет в базе — записываем и возвращаем
            if tg_locale == 'ru':
                set_user_locale(user_id, 'ru')
                return 'ru'
            elif tg_locale in ['uk', 'ua']:
                set_user_locale(user_id, 'ua')
                return 'ua'
            elif tg_locale == 'pt':
                set_user_locale(user_id, 'pt')
                return 'pt'
            else:
                set_user_locale(user_id, 'en')
                return 'en'
        logging.info(f"Не удалось определить пользователя, возвращаем en")
        return 'en'


def setup_i18n(dp: Dispatcher):
    dp.update.outer_middleware(CustomI18nMiddleware(i18n))
