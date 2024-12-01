import ast
import os
import uuid
from datetime import datetime

def generate_id():
    """Генерирует уникальный идентификатор."""
    return str(uuid.uuid4())

def parse_python_code(file_path, source_dir):
    """
    Парсит Python-файл и извлекает классы, функции, глобальные переменные.

    :param file_path: Путь к файлу, который нужно разобрать.
    :param source_dir: Корень проекта, относительно которого формируется путь.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    tree = ast.parse(content)
    chunks = []
    # Получение текущего времени в часовом поясе ОС
    timestamp = datetime.now().isoformat()

    # Формирование относительного пути
    relative_path = os.path.relpath(file_path, start=source_dir)
    file_name, file_extension = os.path.splitext(os.path.basename(file_path))

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) or isinstance(node, ast.FunctionDef):
            chunk_type = "class" if isinstance(node, ast.ClassDef) else "function"
            chunks.append({
                "id": generate_id(),
                "type": chunk_type,
                "name": node.name,
                "start_line": node.lineno,
                "end_line": getattr(node, 'end_lineno', None),
                "description": f"{chunk_type.capitalize()} definition: {node.name}",
                "code": ast.get_source_segment(content, node),
                "metadata": {
                    "source": relative_path,
                    "file_name": file_name,
                    "file_extension": file_extension,
                    "file_type": "python",
                    "timestamp": timestamp
                }
            })

    return chunks
