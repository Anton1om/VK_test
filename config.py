import os

from dotenv import load_dotenv

load_dotenv()

# --- Подключение к БД ----------------------------------------------------
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DATABASE_URL = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

# --- Доступ к ВКонтакте --------------------------------------------------
VK_GROUP_TOKEN = os.getenv("VK_GROUP_TOKEN")  # токен сообщества
VK_USER_TOKEN = os.getenv("VK_USER_TOKEN")    # пользовательский токен
VK_API_VERSION = 5.199 # Версия API ВКонтакте

# --- Параметры поиска ----------------------------------------------------
AGE_DELTA = 5           # +/- лет к возрасту
SEARCH_COUNT = 100  # сколько кандидатов брать
PHOTO_COUNT = 3      # сколько фото показывать
