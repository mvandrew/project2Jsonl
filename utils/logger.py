import logging
import os
from datetime import datetime

def setup_global_logger(name, log_dir="logs", level=logging.INFO):
    """
    Настраивает глобальный логгер с сохранением в файл.

    :param name: Имя логгера.
    :param log_dir: Каталог для хранения лог-файлов.
    :param level: Уровень логирования (по умолчанию logging.INFO).
    :return: Глобальный логгер.
    """
    # Убедимся, что каталог для логов существует
    os.makedirs(log_dir, exist_ok=True)

    # Имя файла лога с временной меткой
    log_file = os.path.join(log_dir, f"{name}_{datetime.now().strftime('%Y%m%d')}.log")

    # Создаем логгер
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Проверяем, добавлены ли уже обработчики
    if not logger.handlers:
        # Форматирование сообщений лога
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Обработчик для записи в файл
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# Глобальный логгер
global_logger = setup_global_logger("project_logger")
