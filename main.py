import os
from dotenv import load_dotenv
from utils.logger import setup_global_logger
from extractors.python_extractor import process_python_files
from extractors.yii2_extractor import Yii2Extractor

# Загрузка конфигурации
load_dotenv()
SOURCE_DIR = os.getenv("SOURCE_DIR")
OUTPUT_DIR = os.getenv("OUTPUT_DIR")
EXCLUDED_DIRS = os.getenv("EXCLUDED_DIRS", "").split(",")
PROJECT_PREFIX = os.getenv("PROJECT_PREFIX", "project")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "5000"))  # Лимит размера чанков (по умолчанию 5000 символов)

# Настройка глобального логгера с использованием PROJECT_PREFIX
logger = setup_global_logger(PROJECT_PREFIX)


def main():
    logger.info("Starting project processing...")

    # Проверка и создание выходной директории
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Генерация имен выходных файлов для Python
    python_output_file = os.path.join(OUTPUT_DIR, f"{PROJECT_PREFIX}_backend_python.jsonl")
    human_readable_python_file = os.path.join(OUTPUT_DIR, f"human_readable/{PROJECT_PREFIX}_backend_python.json")

    # Создать директорию для человекопонятных файлов
    os.makedirs(os.path.dirname(human_readable_python_file), exist_ok=True)

    try:
        # Обработка Python файлов
        logger.info("Processing Python files...")
        process_python_files(SOURCE_DIR, EXCLUDED_DIRS, python_output_file, human_readable_python_file)
        logger.info(f"Python processing completed. Results saved to:")
        logger.info(f" - JSONL: {python_output_file}")
        logger.info(f" - Human-readable JSON: {human_readable_python_file}")

        # Обработка Yii2 файлов
        logger.info("Processing Yii2 project files...")
        yii2_extractor = Yii2Extractor(SOURCE_DIR, OUTPUT_DIR, PROJECT_PREFIX, CHUNK_SIZE, EXCLUDED_DIRS)
        yii2_extractor.extract()
        logger.info(f"Yii2 processing completed. Files generated with prefix '{PROJECT_PREFIX}_yii2_' in {OUTPUT_DIR}")

    except Exception as e:
        logger.error(f"An error occurred during processing: {e}")
        raise

    logger.info("Project processing completed successfully.")


if __name__ == "__main__":
    main()
