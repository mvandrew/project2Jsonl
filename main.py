import os
from dotenv import load_dotenv
from extractors.python_extractor import process_python_files
from extractors.yii2_extractor import Yii2Extractor

# Загрузка конфигурации
load_dotenv()
SOURCE_DIR = os.getenv("SOURCE_DIR")
OUTPUT_DIR = os.getenv("OUTPUT_DIR")
EXCLUDED_DIRS = os.getenv("EXCLUDED_DIRS", "").split(",")
PROJECT_PREFIX = os.getenv("PROJECT_PREFIX", "project")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "5000"))  # Лимит размера чанков (по умолчанию 5000 символов)

def main():
    # Проверка и создание выходной директории
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Генерация имен выходных файлов для Python
    python_output_file = os.path.join(OUTPUT_DIR, f"{PROJECT_PREFIX}_backend_python.jsonl")
    human_readable_python_file = os.path.join(OUTPUT_DIR, f"human_readable/{PROJECT_PREFIX}_backend_python.json")

    # Создать директорию для человекопонятных файлов
    os.makedirs(os.path.dirname(human_readable_python_file), exist_ok=True)

    # Обработка Python файлов
    process_python_files(SOURCE_DIR, EXCLUDED_DIRS, python_output_file, human_readable_python_file)

    # Обработка Yii2 файлов
    print("Starting Yii2 project extraction...")
    yii2_extractor = Yii2Extractor(SOURCE_DIR, OUTPUT_DIR, PROJECT_PREFIX, CHUNK_SIZE)
    yii2_extractor.extract()

    # Итоговый вывод
    print(f"Processing completed. Results saved to:")
    print(f" - Python JSONL: {python_output_file}")
    print(f" - Python Human-readable JSON: {human_readable_python_file}")
    print(f" - Yii2 JSONL: Files generated with prefix '{PROJECT_PREFIX}_yii2_' in {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
