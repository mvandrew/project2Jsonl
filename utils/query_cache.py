import json
import sqlite3
import hashlib
import os

# Путь к файлу базы данных в корне проекта
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '../cache.db')

# Подключение к базе данных SQLite
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Создание таблицы, если её нет
c.execute('''CREATE TABLE IF NOT EXISTS cache
             (key TEXT PRIMARY KEY, value TEXT)''')

def get_cached_response(query):
    """
    Получает кэшированный ответ по запросу.
    :param query: Исходный текст запроса.
    :return: Распарсенный JSON-ответ или None, если записи нет.
    """
    key = hashlib.md5(query.encode('utf-8')).hexdigest()  # Генерация ключа
    c.execute('SELECT value FROM cache WHERE key = ?', (key,))
    row = c.fetchone()
    return json.loads(row[0]) if row else None

def save_response(query, response):
    """
    Сохраняет ответ в кэш.
    :param query: Исходный текст запроса.
    :param response: Ответ для сохранения (объект Python).
    """
    key = hashlib.md5(query.encode('utf-8')).hexdigest()  # Генерация ключа
    c.execute('INSERT OR REPLACE INTO cache (key, value) VALUES (?, ?)', (key, json.dumps(response)))
    conn.commit()
