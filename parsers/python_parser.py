import ast
import os
from utils.common import generate_id
from datetime import datetime
from utils.llm_assist import LLMAssist


def set_parents(tree):
    """
    Рекурсивно добавляет атрибут parent для каждого узла в дереве AST.

    :param tree: Корневой узел дерева AST.
    """
    for node in ast.walk(tree):  # Проходим по всем узлам дерева
        for child in ast.iter_child_nodes(node):  # Для каждого дочернего узла
            child.parent = node  # Устанавливаем ссылку на родительский узел


def parse_python_code(file_path, source_dir, project_type=None):
    """
    Парсит Python-файл, извлекая классы, функции, глобальные переменные, импортируемые модули.

    :param project_type: Тип проекта (например, "django").
    :param file_path: Путь к файлу, который нужно разобрать.
    :param source_dir: Корень проекта, относительно которого формируется путь.
    :return: Список извлеченных данных в виде чанков.
    """
    # Инициализируем помощника для анализа с использованием LLM
    llm_assist = LLMAssist(project_type)

    # Открываем и читаем содержимое файла
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Парсим содержимое файла в абстрактное синтаксическое дерево (AST)
    tree = ast.parse(content)
    set_parents(tree)  # Устанавливаем родительские узлы для всех элементов дерева

    # Метаданные файла
    timestamp = datetime.now().isoformat()  # Временная метка обработки
    relative_path = os.path.relpath(file_path, start=source_dir)  # Относительный путь к файлу
    file_name, file_extension = os.path.splitext(os.path.basename(file_path))  # Имя и расширение файла

    # Инициализируем списки для хранения извлечённой информации
    chunks = []  # Основной список для всех элементов файла
    imports = []  # Список для импортов
    functions = []  # Список для глобальных функций
    classes = []  # Список для классов

    # Обход всех узлов AST
    for node in ast.walk(tree):
        # Обработка импортов (import и from ... import ...)
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            import_data = {
                "id": generate_id(),  # Генерация уникального идентификатора
                "type": "import",  # Тип узла
                "name": None,  # Имя модуля (для import from)
                "description": "Import statement",  # Описание узла
                "modules": [],  # Импортируемые модули
                "line": node.lineno,  # Номер строки, где находится импорт
            }
            if isinstance(node, ast.Import):
                import_data["modules"] = [alias.name for alias in node.names]  # Список модулей
            elif isinstance(node, ast.ImportFrom):
                import_data["name"] = node.module  # Имя модуля
                import_data["modules"] = [alias.name for alias in node.names]  # Список модулей

            imports.append(import_data)  # Добавляем в список импортов

        # Обработка глобальных функций
        elif isinstance(node, ast.FunctionDef) and isinstance(node.parent, ast.Module):
            function_data = {
                "id": generate_id(),
                "type": "function",  # Тип узла
                "name": node.name,  # Имя функции
                "description": f"Function definition: {node.name}",  # Описание функции
                "code": ast.get_source_segment(content, node),  # Исходный код функции
                "start_line": node.lineno,  # Начальная строка
                "end_line": getattr(node, "end_lineno", None),  # Конечная строка (если поддерживается)
            }
            functions.append(function_data)  # Добавляем в список функций

        # Обработка классов
        elif isinstance(node, ast.ClassDef):
            class_data = {
                "id": generate_id(),
                "type": "class",  # Тип узла
                "name": node.name,  # Имя класса
                "description": f"Class definition: {node.name}",  # Описание класса
                "code": ast.get_source_segment(content, node),  # Исходный код класса
                "start_line": node.lineno,  # Начальная строка
                "end_line": getattr(node, "end_lineno", None),  # Конечная строка
                "methods": [],  # Методы класса
                "attributes": [],  # Атрибуты класса
            }

            # Обработка содержимого класса
            for class_node in node.body:
                # Извлечение методов
                if isinstance(class_node, ast.FunctionDef):
                    method_data = {
                        "id": generate_id(),
                        "type": "method",  # Тип узла
                        "name": class_node.name,  # Имя метода
                        "description": f"Method {class_node.name} in class {node.name}",  # Описание метода
                        "code": ast.get_source_segment(content, class_node),  # Исходный код метода
                        "start_line": class_node.lineno,  # Начальная строка метода
                        "end_line": getattr(class_node, "end_lineno", None),  # Конечная строка метода
                    }
                    class_data["methods"].append(method_data)  # Добавляем метод в список методов класса

                # Извлечение атрибутов (глобальных переменных в теле класса)
                elif isinstance(class_node, ast.Assign):
                    for target in class_node.targets:
                        if isinstance(target, ast.Name):  # Проверка, является ли целевой объект именем
                            attribute_data = {
                                "id": generate_id(),
                                "type": "attribute",  # Тип узла
                                "name": target.id,  # Имя атрибута
                                "description": f"Attribute {target.id} in class {node.name}",  # Описание атрибута
                                "value": ast.get_source_segment(content, class_node.value),  # Значение атрибута
                                "line": class_node.lineno,  # Номер строки
                            }
                            class_data["attributes"].append(attribute_data)  # Добавляем атрибут

            classes.append(class_data)  # Добавляем класс в список классов

    # Формируем чанки с импортами
    if imports:
        chunks.append({
            "id": generate_id(),
            "type": "imports",
            "description": "List of import statements",
            "items": imports,
        })

    # Добавляем функции и классы в чанки
    chunks.extend(functions)
    chunks.extend(classes)

    # Попытка описать файл с помощью LLMAssist
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            file_code = file.read()
    except Exception as e:
        raise RuntimeError(f"Unable to read the file {file_path}: {e}")

    if llm_assist.success:
        description = llm_assist.describe_file(relative_path, file_code)  # Описание файла с помощью LLM
    else:
        description = f"Python file: {file_name}"  # Описание по умолчанию

    # Финальная структура для метаданных файла
    file_metadata = {
        "id": generate_id(),
        "type": "file",
        "name": file_name,
        "description": description,  # Описание файла
        "code": None,  # Исходный код (по умолчанию не включается)
        "metadata": {  # Дополнительные метаданные файла
            "source": relative_path,
            "file_name": file_name,
            "file_extension": file_extension,
            "file_type": "python",
            "timestamp": timestamp
        },
        "chunks": chunks  # Все собранные чанки
    }

    return [file_metadata]  # Возвращаем список с метаданными файла
