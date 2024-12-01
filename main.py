import os
from dotenv import load_dotenv
from extractors.python_extractor import process_python_files

# Загрузка конфигурации
load_dotenv()
SOURCE_DIR = os.getenv("SOURCE_DIR")
OUTPUT_DIR = os.getenv("OUTPUT_DIR")
EXCLUDED_DIRS = os.getenv("EXCLUDED_DIRS", "").split(",")
PROJECT_PREFIX = os.getenv("PROJECT_PREFIX", "project")

def main():
    # Проверка и создание выходной директории
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Генерация имени выходного файла
    output_file = os.path.join(OUTPUT_DIR, f"{PROJECT_PREFIX}_backend_python.jsonl")

    # Обработка Python файлов
    process_python_files(SOURCE_DIR, EXCLUDED_DIRS, output_file)

    print(f"Processing completed. Results saved to {output_file}")

if __name__ == "__main__":
    main()
