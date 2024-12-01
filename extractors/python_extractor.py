import os
from utils.file_utils import get_python_files
from parsers.python_parser import parse_python_code
from formatters.jsonl_formatter import save_to_jsonl

def process_python_files(source_dir, excluded_dirs, output_file):
    """Основной обработчик для Python-кода."""
    # Получить все Python файлы
    python_files = get_python_files(source_dir, excluded_dirs)

    all_chunks = []
    for file_path in python_files:
        chunks = parse_python_code(file_path)
        for chunk in chunks:
            chunk["file_path"] = file_path  # Добавить путь к файлу
        all_chunks.extend(chunks)

    # Сохранить результат в JSONL
    save_to_jsonl(all_chunks, output_file)
