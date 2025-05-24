from pathlib import Path
from aiogram import types, Dispatcher
from aiogram.utils.i18n import I18n, I18nMiddleware
from aiogram.utils.i18n.middleware import I18nMiddleware
from config import I18N_DOMAIN

# Путь к папке с переводами
LOCALES_DIR = Path(__file__).parent / "locales"

# Инициализация I18n
i18n = I18n(path=LOCALES_DIR, default_locale='ru', domain=I18N_DOMAIN)
_ = i18n.gettext  # Используется для перевода строк

# Кастомная middleware с реализацией get_locale
class CustomI18nMiddleware(I18nMiddleware):
    async def get_locale(self, event: types.TelegramObject, data: dict) -> str:
        # Пример: можно доработать под хранение языка пользователя
        # Здесь можно использовать данные из `data`, если нужно
        return 'ru' # Или динамически вернуть язык пользователя

def setup_i18n(dp: Dispatcher):
    dp.update.outer_middleware(CustomI18nMiddleware(i18n))
