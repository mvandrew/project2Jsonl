import subprocess
import json
import os
from utils.common import generate_id
from datetime import datetime


def parse_ts_code(file_path, source_dir, ts_parser_script="ts_parser.js"):
    """
    Парсит TS/TSX-файл, вызывая Node.js-скрипт, и возвращает извлеченные данные.

    :param file_path: Путь к файлу, который нужно разобрать.
    :param source_dir: Корень проекта, относительно которого формируется путь.
    :param ts_parser_script: Путь к TS/TSX парсеру на Node.js.
    :return: Список чанков, извлеченных из TS/TSX файла.
    """
    # Преобразуем путь к TS парсеру в абсолютный
    ts_parser_script = os.path.abspath(ts_parser_script)

    # Определяем корневую директорию для ts_parser.js
    parser_dir = os.path.dirname(ts_parser_script)

    # Проверяем наличие TS парсера
    if not os.path.exists(ts_parser_script):
        raise FileNotFoundError(f"TS parser script not found at: {ts_parser_script}")

    # Вызываем TS парсер для анализа файла
    try:
        result = subprocess.run(
            ["node", ts_parser_script, file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=parser_dir  # Устанавливаем рабочую директорию как каталог ts_parser.js
        )

        # Проверяем на ошибки выполнения
        if result.returncode != 0:
            raise RuntimeError(f"Error in TS parser script: {result.stderr.strip()}")

        # Парсим результат работы TS парсера
        parsed_data = json.loads(result.stdout)
    except Exception as e:
        raise RuntimeError(f"Error while executing TS parser: {e}")

    # Проверяем наличие ошибок в результате
    if "error" in parsed_data:
        raise ValueError(f"TS parser error: {parsed_data['error']}")

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
            "name": class_data["name"],
            "description": f"Class definition: {class_data['name']}",
            "code": class_data.get("code"),
            "methods": [],
            "properties": []
        }

        # Обрабатываем свойства класса
        for property_data in class_data.get("properties", []):
            property_chunk = {
                "id": generate_id(),
                "type": "property",
                "name": property_data["name"],
                "description": f"Property {property_data['name']} in class {class_data['name']}",
                "type": property_data.get("type"),
                "default_value": property_data.get("default_value"),
                "modifiers": property_data.get("static", False)
            }
            class_chunk["properties"].append(property_chunk)

        # Обрабатываем методы класса
        for method_data in class_data.get("methods", []):
            method_chunk = {
                "id": generate_id(),
                "type": "method",
                "name": method_data["name"],
                "description": f"Method {method_data['name']} in class {class_data['name']}",
                "code": method_data.get("code"),
                "start_line": method_data.get("start_line"),
                "end_line": method_data.get("end_line"),
                "modifiers": method_data.get("kind")
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

    # Формируем данные о React компонентах
    for component_data in parsed_data.get("react_components", []):
        component_chunk = {
            "id": generate_id(),
            "type": "react_component",
            "name": component_data["name"],
            "description": f"React component: {component_data['name']}",
            "code": component_data.get("code"),
            "props": component_data.get("props", [])
        }
        chunks.append(component_chunk)

    # Формируем данные о типах
    for type_data in parsed_data.get("types", []):
        type_chunk = {
            "id": generate_id(),
            "type": "type",
            "name": type_data["name"],
            "description": f"Type {type_data['name']} ({type_data['kind']})",
            "code": type_data.get("code"),
        }
        chunks.append(type_chunk)

    # Формируем данные о зависимостях
    imports = parsed_data.get("imports", [])
    if imports:
        imports_chunk = {
            "id": generate_id(),
            "type": "dependencies",
            "description": "List of imports",
            "dependencies": imports,
        }
        chunks.append(imports_chunk)

    # Формируем данные об экспортах
    for export_data in parsed_data.get("exports", []):
        export_chunk = {
            "id": generate_id(),
            "type": "export",
            "name": export_data["name"],
            "description": f"Export {export_data['name']}",
            "code": export_data.get("code"),
        }
        chunks.append(export_chunk)

    # Формируем итоговую структуру для файла
    file_metadata = {
        "id": generate_id(),
        "type": "file",
        "name": file_name,
        "description": f"TS/TSX file: {file_name}",
        "code": None,
        "metadata": {
            "source": relative_path,
            "file_name": file_name,
            "file_extension": file_extension,
            "file_type": "tsx" if file_extension == ".tsx" else "ts",
            "timestamp": timestamp
        },
        "chunks": chunks
    }

    return [file_metadata]
