import os
from utils.file_utils import get_python_files
from parsers.python_parser import parse_python_code
from formatters.jsonl_formatter import save_to_jsonl
from formatters.json_formatter import jsonl_to_human_readable_json

def process_python_files(source_dir, excluded_dirs, output_file, human_readable_file):
    """
    Основной обработчик для Python-кода.
    """
    # Получить все Python файлы
    python_files = get_python_files(source_dir, excluded_dirs)

    all_chunks = []
    for file_path in python_files:
        # Парсинг Python файла на чанки
        chunks = parse_python_code(file_path)
        for chunk in chunks:
            # Добавить путь к файлу относительно корня проекта
            relative_path = os.path.relpath(file_path, start=source_dir)
            chunk["file_path"] = relative_path
        all_chunks.extend(chunks)

    # Сохранить результат в JSONL
    save_to_jsonl(all_chunks, output_file)

    # Преобразовать JSONL в человекопонятный JSON
    jsonl_to_human_readable_json(output_file, human_readable_file)
