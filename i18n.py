from pathlib import Path
from aiogram import types, Dispatcher
from aiogram.utils.i18n import I18n, I18nMiddleware
from aiogram.utils.i18n.middleware import I18nMiddleware
from config import I18N_DOMAIN
from database import get_user_locale, set_user_locale


# Путь к папке с переводами
LOCALES_DIR = Path(__file__).parent / "locales"

# Инициализация I18n
i18n = I18n(path=LOCALES_DIR, default_locale='ru', domain=I18N_DOMAIN)
_ = i18n.gettext  # Используется для перевода строк

# Кастомная middleware с реализацией get_locale
class CustomI18nMiddleware(I18nMiddleware):
    async def get_locale(self, event: types.TelegramObject, data: dict) -> str:
        if hasattr(event, 'from_user'):
            user_id = event.from_user.id
            db_locale = get_user_locale(user_id)
            if db_locale:  # если есть в базе
                return db_locale
            # если нет в базе, берём из Telegram
            tg_locale = getattr(event.from_user, 'language_code', 'ru')[:2]
            # приводим к нужному формату
            if tg_locale == 'en':
                set_user_locale(user_id, 'en')
                return 'en'
            elif tg_locale == 'uk':
                set_user_locale(user_id, 'uk')
                return 'uk'
            elif tg_locale == 'pt':
                set_user_locale(user_id, 'pt')
                return 'pt'
            else:
                set_user_locale(user_id, 'ru')
                return 'ru'
        return 'en' 

def setup_i18n(dp: Dispatcher):
    dp.update.outer_middleware(CustomI18nMiddleware(i18n))
