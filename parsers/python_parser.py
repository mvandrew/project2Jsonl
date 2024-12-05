import ast
import os
from utils.common import generate_id
from datetime import datetime


def parse_python_code(file_path, source_dir):
    """
    Парсит Python-файл, извлекая классы, функции, глобальные переменные, импортируемые модули.

    :param file_path: Путь к файлу, который нужно разобрать.
    :param source_dir: Корень проекта, относительно которого формируется путь.
    :return: Список извлеченных данных в виде чанков.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    tree = ast.parse(content)
    timestamp = datetime.now().isoformat()  # Временная метка
    relative_path = os.path.relpath(file_path, start=source_dir)  # Относительный путь
    file_name, file_extension = os.path.splitext(os.path.basename(file_path))

    # Инициализация списка чанков
    chunks = []

    # Хранилище классов, функций и импортов
    imports = []
    functions = []
    classes = []

    for node in ast.walk(tree):
        # Обработка импортов (import / from ... import ...)
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            import_data = {
                "id": generate_id(),
                "type": "import",
                "name": None,
                "description": "Import statement",
                "modules": [],
                "line": node.lineno,
            }
            if isinstance(node, ast.Import):
                import_data["modules"] = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                import_data["name"] = node.module
                import_data["modules"] = [alias.name for alias in node.names]

            imports.append(import_data)

        # Обработка глобальных функций
        elif isinstance(node, ast.FunctionDef):
            function_data = {
                "id": generate_id(),
                "type": "function",
                "name": node.name,
                "description": f"Function definition: {node.name}",
                "code": ast.get_source_segment(content, node),
                "start_line": node.lineno,
                "end_line": getattr(node, "end_lineno", None),
            }
            functions.append(function_data)

        # Обработка классов
        elif isinstance(node, ast.ClassDef):
            class_data = {
                "id": generate_id(),
                "type": "class",
                "name": node.name,
                "description": f"Class definition: {node.name}",
                "code": ast.get_source_segment(content, node),
                "start_line": node.lineno,
                "end_line": getattr(node, "end_lineno", None),
                "methods": [],
                "attributes": [],
            }

            # Извлечение методов и атрибутов класса
            for class_node in node.body:
                if isinstance(class_node, ast.FunctionDef):
                    method_data = {
                        "id": generate_id(),
                        "type": "method",
                        "name": class_node.name,
                        "description": f"Method {class_node.name} in class {node.name}",
                        "code": ast.get_source_segment(content, class_node),
                        "start_line": class_node.lineno,
                        "end_line": getattr(class_node, "end_lineno", None),
                    }
                    class_data["methods"].append(method_data)

                elif isinstance(class_node, ast.Assign):
                    # Обработка атрибутов класса (глобальные переменные в теле класса)
                    for target in class_node.targets:
                        if isinstance(target, ast.Name):
                            attribute_data = {
                                "id": generate_id(),
                                "type": "attribute",
                                "name": target.id,
                                "description": f"Attribute {target.id} in class {node.name}",
                                "value": ast.get_source_segment(content, class_node.value),
                                "line": class_node.lineno,
                            }
                            class_data["attributes"].append(attribute_data)

            classes.append(class_data)

    # Добавление всех данных в общий список чанков
    if imports:
        chunks.append({
            "id": generate_id(),
            "type": "imports",
            "description": "List of import statements",
            "items": imports,
        })

    chunks.extend(functions)
    chunks.extend(classes)

    # Финальная структура файла
    file_metadata = {
        "id": generate_id(),
        "type": "file",
        "name": file_name,
        "description": f"Python file: {file_name}",
        "code": None,  # При необходимости можно включить весь исходный код
        "metadata": {
            "source": relative_path,
            "file_name": file_name,
            "file_extension": file_extension,
            "file_type": "python",
            "timestamp": timestamp
        },
        "chunks": chunks
    }

    return [file_metadata]
