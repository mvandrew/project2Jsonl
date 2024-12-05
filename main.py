import os
from dotenv import load_dotenv
from utils.logger import setup_global_logger
from formatters.json_manager import JSONManager
from extractors.python_extractor import process_python_files
from extractors.yii2_extractor import Yii2Extractor
from extractors.react_extractor import ReactExtractor  # Импортируем ReactExtractor

# Загрузка конфигурации
load_dotenv()
SOURCE_DIR = os.getenv("SOURCE_DIR")
OUTPUT_DIR = os.getenv("OUTPUT_DIR")
EXCLUDED_DIRS = os.getenv("EXCLUDED_DIRS", "").split(",")
PROJECT_PREFIX = os.getenv("PROJECT_PREFIX", "project")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "5000"))
PROJECT_TYPES = os.getenv("PROJECT_TYPES", "").split(",")  # Список типов проектов
MAX_SUMMARY_FILE_SIZE = int(os.getenv("MAX_SUMMARY_FILE_SIZE", "1048576"))

# Настройка глобального логгера
logger = setup_global_logger(PROJECT_PREFIX)

# Создаем экземпляр JSONManager
json_manager = JSONManager(output_directory=OUTPUT_DIR, project_prefix=PROJECT_PREFIX)


def clear_output_directory(output_dir):
    """
    Удаляет все файлы с расширением .json и .jsonl в указанной директории.

    :param output_dir: Путь к директории для очистки.
    """
    logger.info(f"Очистка директории вывода: {output_dir}")
    for root, dirs, files in os.walk(output_dir):
        for file in files:
            if file.endswith(".json") or file.endswith(".jsonl"):
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                    logger.info(f"Удален файл: {file_path}")
                except Exception as e:
                    logger.error(f"Не удалось удалить файл {file_path}: {e}")


def process_project():
    """
    Выполняет обработку проекта, основываясь на типах проектов.
    """
    if "python" in PROJECT_TYPES:
        logger.info("Обработка Python файлов...")
        process_python_files(SOURCE_DIR, EXCLUDED_DIRS, json_manager, CHUNK_SIZE)
        logger.info("Обработка Python завершена.")

    if "yii2" in PROJECT_TYPES:
        logger.info("Обработка Yii2 файлов...")
        yii2_extractor = Yii2Extractor(SOURCE_DIR, OUTPUT_DIR, PROJECT_PREFIX, json_manager, CHUNK_SIZE, EXCLUDED_DIRS)
        yii2_extractor.extract()
        logger.info("Обработка Yii2 завершена.")

    if "react" in PROJECT_TYPES:
        logger.info("Обработка React файлов...")
        react_extractor = ReactExtractor(SOURCE_DIR, OUTPUT_DIR, PROJECT_PREFIX, json_manager, CHUNK_SIZE, EXCLUDED_DIRS)
        react_extractor.extract()
        logger.info("Обработка React завершена.")

    # Здесь можно добавить обработку других типов проектов:
    # if "laravel" in PROJECT_TYPES:
    #     logger.info("Обработка Laravel файлов...")
    #     laravel_extractor = LaravelExtractor(SOURCE_DIR, OUTPUT_DIR, PROJECT_PREFIX, json_manager, CHUNK_SIZE, EXCLUDED_DIRS)
    #     laravel_extractor.extract()
    #     logger.info("Обработка Laravel завершена.")


def main():
    logger.info("Начало обработки проекта...")
    try:
        # Очистка директории вывода
        clear_output_directory(OUTPUT_DIR)

        # Обработка проекта на основе типов
        process_project()

        # Сохранение всех данных
        logger.info("Сохранение всех данных...")
        json_manager.save_all(group_by="metadata.source", max_summary_file_size=MAX_SUMMARY_FILE_SIZE)
        logger.info("Все данные успешно сохранены.")

    except Exception as e:
        logger.error(f"Ошибка обработки: {e}")
        raise

    logger.info("Обработка завершена успешно.")


if __name__ == "__main__":
    main()
