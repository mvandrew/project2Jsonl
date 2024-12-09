import subprocess
import json
import os
from utils.common import generate_id
from datetime import datetime
from utils.llm_assist import LLMAssist
from utils.qa_manager import QAManager


def get_class_qa(llm_assist, class_chunk):
    """
    Формирует раздел вопросов и ответов для дообучения LLM модели на основе данных о классе.

    :param llm_assist: Экземпляр LLMAssist.
    :param class_chunk: Словарь с информацией о классе.
    :return: Список словарей с вопросами и ответами.
    """
    # Генерация вопросов на основе данных о классе с контекстом
    description = class_chunk.get("description", "")
    properties = class_chunk.get("properties", [])
    methods = class_chunk.get("methods", [])

    # Формирование контекста для свойств и методов
    properties_list = "\n".join([f"- {prop['name']}" for prop in properties])
    methods_list = "\n".join([f"- {method['name']}" for method in methods])

    questions = [
        {
            "question": f"Какая основная цель класса {class_chunk['name']}?",
            "context": f"Описание класса: {description}" if description else ""
        },
        {
            "question": f"Какие свойства есть у класса {class_chunk['name']} и для чего они используются?",
            "context": f"Список свойств:\n{properties_list}" if properties else "У класса нет свойств."
        },
        {
            "question": f"Какие методы предоставляет класс {class_chunk['name']} и как они работают?",
            "context": f"Список методов:\n{methods_list}" if methods else "У класса нет методов."
        }
    ]

    # Сбор модификаторов из свойств и методов
    property_modifiers = [
        modifier for prop in properties for modifier in prop.get("modifiers", [])
    ]
    method_modifiers = [
        modifier for method in methods for modifier in method.get("modifiers", [])
    ]

    # Убираем дубликаты и сортируем список модификаторов
    all_modifiers = sorted(set(property_modifiers + method_modifiers))

    # Формируем контекст на основе собранных модификаторов
    if all_modifiers:
        context = (
            f"В классе {class_chunk['name']} используются следующие модификаторы: "
            f"{', '.join(all_modifiers)}."
        )
    else:
        context = f"В классе {class_chunk['name']} модификаторы не указаны."
    questions.append({
            "question": f"Какие модификаторы используются в свойствах и методах класса {class_chunk['name']}?",
            "context": context
        })

    # Добавляем вопросы для каждого свойства
    if properties:
        for property_chunk in properties:
            description = property_chunk.get("description", "")
            code = property_chunk.get("code", "")

            context = " ".join([
                f"Описание: {description}" if description else "",
                f"Код:\n{code}" if code else ""
            ]).strip()

            questions.append({
                "question": f"Что делает свойство {property_chunk['name']} в классе {class_chunk['name']}?",
                "context": context
            })

            if property_chunk.get("default_value") is not None:
                questions.append({
                    "question": f"Какое значение по умолчанию у свойства {property_chunk['name']} в классе {class_chunk['name']}?",
                    "context": context
                })

    # Добавляем вопросы для каждого метода
    if methods:
        for method_chunk in methods:
            description = method_chunk.get("description", "")
            code = method_chunk.get("code", "")

            context = " ".join([
                f"Описание: {description}" if description else "",
                f"Код:\n{code}" if code else ""
            ]).strip()

            questions.append({
                "question": f"Какова цель метода {method_chunk['name']} в классе {class_chunk['name']}?",
                "context": context
            })

            if method_chunk.get("modifiers"):
                questions.append({
                    "question": f"Какие модификаторы используются в методе {method_chunk['name']} класса {class_chunk['name']}?",
                    "context": context
                })
            if method_chunk.get("start_line") is not None and method_chunk.get("end_line") is not None:
                questions.append({
                    "question": f"В каких строках определён метод {method_chunk['name']} в классе {class_chunk['name']}?",
                    "context": context
                })

    # Подготовка и выполнение запросов к LLM
    qa_results = []
    qa_manager = QAManager()
    try:
        for question_data in questions:
            question = question_data["question"]
            context = question_data["context"]

            # Формируем сообщение для модели
            user_message = (
                f"Вы ассистент, обучающий на основе кода. Сформулируйте ответ на вопрос о классе {class_chunk['name']} "
                f"на русском языке. Вопрос: {question}"
            )
            if context:
                user_message += f"\n\nКонтекст:\n{context}"

            # Отправляем запрос к LLM
            response = llm_assist.query(user_message=user_message, temperature=0.5)

            # Добавляем результат
            qa_results.append({
                "question": question,
                "answer": response.strip()  # Убираем лишние пробелы и переносы строк
            })

            qa_manager.add_qa(question, response.strip())

    except Exception as e:
        raise RuntimeError(f"Ошибка при генерации QA данных: {e}")

    return qa_results

def parse_php_code(file_path, source_dir, php_parser_script="php_parser.php", project_type=None):
    """
    Парсит PHP-файл, вызывая PHP-скрипт, и возвращает извлеченные данные.

    :param project_type: Тип проекта (например, "laravel").
    :param file_path: Путь к файлу, который нужно разобрать.
    :param source_dir: Корень проекта, относительно которого формируется путь.
    :param php_parser_script: Путь к PHP-скрипту.
    :return: Список чанков, извлеченных из PHP-файла.
    """
    # Инициализируем LLMAssist
    llm_assist = LLMAssist(project_type)

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
        if llm_assist.success:
            description = llm_assist.describe_class(class_data["name"], class_data.get("code"), relative_path)
        else:
            description = f"Class definition: {class_data['name']}"

        class_chunk = {
            "id": generate_id(),
            "type": "class",
            "name": class_data["name"],  # Имя класса
            "description": description,
            "code": class_data.get("code"),  # Исходный код класса
            "qa": [],
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
            if llm_assist.success:
                description = llm_assist.describe_class_method(method_data["name"], method_data.get("code"), class_chunk["name"], class_chunk["description"])
            else:
                description = f"Method {method_data['name']} in class {class_data['name']}"

            method_chunk = {
                "id": generate_id(),
                "type": "method",
                "name": method_data["name"],
                "description": description,
                "code": method_data.get("code"),
                "start_line": method_data.get("start_line"),
                "end_line": method_data.get("end_line"),
                "modifiers": method_data.get("modifiers", [])
            }
            class_chunk["methods"].append(method_chunk)

        class_chunk["qa"] = get_class_qa(llm_assist, class_chunk)

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

    # Описание файла с помощью LLMAssist
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            file_code = file.read()
    except Exception as e:
        raise RuntimeError(f"Unable to read the file {file_path}: {e}")

    if llm_assist.success:
        description = llm_assist.describe_file(relative_path, file_code)
    else:
        description = f"PHP file: {file_name}"

    # Формируем итоговую структуру для файла
    file_metadata = {
        "id": generate_id(),
        "type": "file",
        "name": file_name,
        "description": description,
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
        file_metadata["code"] = file_code

    return [file_metadata]
