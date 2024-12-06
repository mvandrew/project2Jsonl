import subprocess
import json
import os
from utils.common import generate_id
from datetime import datetime


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
    for class_data in parsed_data.get("classes", []):
        class_chunk = {
            "id": generate_id(),
            "type": "class",
            "name": class_data["name"],  # Имя класса
            "description": f"Class definition: {class_data['name']}",
            "code": class_data.get("code"),  # Исходный код класса
            "methods": [],
            "properties": []
        }

        # Обрабатываем свойства класса, если они есть
        for property_data in class_data.get("properties", []):
            property_chunk = {
                "id": generate_id(),
                "type": "property",
                "name": property_data["name"],
                "description": f"Property {property_data['name']} in class {class_data['name']}",
                "type": property_data.get("type"),
                "modifiers": property_data.get("modifiers", []),
                "default_value": property_data.get("default_value"),
            }
            class_chunk["properties"].append(property_chunk)

        # Обрабатываем методы класса, если они есть
        for method_data in class_data.get("methods", []):
            method_chunk = {
                "id": generate_id(),
                "type": "method",
                "name": method_data["name"],
                "description": f"Method {method_data['name']} in class {class_data['name']}",
                "code": method_data.get("code"),
                "start_line": method_data.get("start_line"),
                "end_line": method_data.get("end_line"),
                "modifiers": method_data.get("modifiers", [])
            }
            class_chunk["methods"].append(method_chunk)

        chunks.append(class_chunk)

    # Формируем данные о функциях
    for function_data in parsed_data.get("functions", []):
        function_chunk = {
            "id": generate_id(),
            "type": "function",
            "name": function_data["name"],
            "description": f"Global function {function_data['name']}",
            "code": function_data.get("code"),
            "start_line": function_data.get("start_line"),
            "end_line": function_data.get("end_line"),
        }
        chunks.append(function_chunk)

    # Формируем данные о зависимостях (use statements)
    dependencies = parsed_data.get("dependencies", [])
    if dependencies:
        dependency_chunk = {
            "id": generate_id(),
            "type": "dependencies",
            "description": "List of dependencies",
            "dependencies": dependencies,
        }
        chunks.append(dependency_chunk)

    # Формируем данные о пространстве имен
    if parsed_data.get("namespace"):
        namespace_chunk = {
            "id": generate_id(),
            "type": "namespace",
            "name": parsed_data["namespace"],
            "description": f"Namespace: {parsed_data['namespace']}",
        }
        chunks.append(namespace_chunk)

    # Формируем итоговую структуру для файла
    file_metadata = {
        "id": generate_id(),
        "type": "file",
        "name": file_name,
        "description": f"PHP file: {file_name}",
        "code": None,  # По умолчанию None, добавим полный код, если chunks пуст
        "metadata": {
            "source": relative_path,
            "file_name": file_name,
            "file_extension": file_extension,
            "file_type": "php",
            "timestamp": timestamp
        },
        "chunks": chunks
    }

    # Если chunks пусты, добавляем полный исходный код файла
    if not chunks:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                file_metadata["code"] = file.read()
        except Exception as e:
            raise RuntimeError(f"Unable to read the file {file_path}: {e}")

    return [file_metadata]
