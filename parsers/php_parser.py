import subprocess
import json
import os
import uuid
from datetime import datetime


def generate_id():
    """Генерирует уникальный идентификатор."""
    return str(uuid.uuid4())


def parse_php_code(file_path, source_dir, php_parser_script="php_parser.php"):
    """
    Парсит PHP-файл, вызывая PHP-скрипт, и возвращает извлеченные данные.

    :param file_path: Путь к файлу, который нужно разобрать.
    :param source_dir: Корень проекта, относительно которого формируется путь.
    :param php_parser_script: Путь к PHP-скрипту.
    :return: Список чанков, извлеченных из PHP-файла.
    """
    # Преобразуем путь к PHP-скрипту в абсолютный
    php_parser_script = os.path.abspath(php_parser_script)

    # Определяем корневую директорию для php_parser.php
    parser_dir = os.path.dirname(php_parser_script)

    # Проверяем наличие PHP-скрипта
    if not os.path.exists(php_parser_script):
        raise FileNotFoundError(f"PHP parser script not found at: {php_parser_script}")

    # Вызываем PHP-скрипт для анализа файла
    try:
        result = subprocess.run(
            ["php", php_parser_script, file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=parser_dir  # Устанавливаем рабочую директорию как каталог php_parser.php
        )

        # Проверяем на ошибки выполнения
        if result.returncode != 0:
            raise RuntimeError(f"Error in PHP parser script: {result.stderr.strip()}")

        # Парсим результат работы PHP-скрипта
        parsed_data = json.loads(result.stdout)
    except Exception as e:
        raise RuntimeError(f"Error while executing PHP parser: {e}")

    # Проверяем наличие ошибок в результате
    if "error" in parsed_data:
        raise ValueError(f"PHP parser error: {parsed_data['error']}")

    # Формирование чанков
    chunks = []
    timestamp = datetime.now().isoformat()  # Текущая временная метка
    relative_path = os.path.relpath(file_path, start=source_dir)  # Относительный путь
    file_name, file_extension = os.path.splitext(os.path.basename(file_path))

    # Формируем данные о классах
    for class_name in parsed_data.get("classes", []):
        chunks.append({
            "id": generate_id(),
            "type": "class",
            "name": class_name,
            "start_line": None,  # Данные о строках недоступны в парсере
            "end_line": None,
            "description": f"Class definition: {class_name}",
            "code": None,  # Исходный код недоступен в текущем парсере
            "metadata": {
                "source": relative_path,
                "file_name": file_name,
                "file_extension": file_extension,
                "file_type": "php",
                "timestamp": timestamp
            }
        })

    # Формируем данные о функциях
    for function_name in parsed_data.get("functions", []):
        chunks.append({
            "id": generate_id(),
            "type": "function",
            "name": function_name,
            "start_line": None,
            "end_line": None,
            "description": f"Function definition: {function_name}",
            "code": None,
            "metadata": {
                "source": relative_path,
                "file_name": file_name,
                "file_extension": file_extension,
                "file_type": "php",
                "timestamp": timestamp
            }
        })

    # Формируем данные о зависимостях (use statements)
    for dependency in parsed_data.get("dependencies", []):
        chunks.append({
            "id": generate_id(),
            "type": "dependency",
            "name": dependency,
            "start_line": None,
            "end_line": None,
            "description": f"Dependency: {dependency}",
            "code": None,
            "metadata": {
                "source": relative_path,
                "file_name": file_name,
                "file_extension": file_extension,
                "file_type": "php",
                "timestamp": timestamp
            }
        })

    # Формируем данные о пространстве имен
    if parsed_data.get("namespace"):
        chunks.append({
            "id": generate_id(),
            "type": "namespace",
            "name": parsed_data["namespace"],
            "start_line": None,
            "end_line": None,
            "description": f"Namespace: {parsed_data['namespace']}",
            "code": None,
            "metadata": {
                "source": relative_path,
                "file_name": file_name,
                "file_extension": file_extension,
                "file_type": "php",
                "timestamp": timestamp
            }
        })

    return chunks
