import os
from datetime import datetime

from extractors.base_extractor import BaseExtractor
from parsers.php_parser import parse_php_code, generate_id
from utils.file_utils import get_all_files
from utils.logger import global_logger as logger

class Yii2Extractor(BaseExtractor):
    def __init__(self, project_root, output_dir, prefix, chunk_size=5000, excluded_dirs=None):
        super().__init__(project_root, output_dir, prefix, excluded_dirs)
        self.chunk_size = chunk_size

    def extract(self):
        """
        Обрабатывает всю структуру каталогов проекта, включая вложенные модули,
        за исключением каталогов, указанных в excluded_dirs.
        """
        logger.info(f"Начало обработки структуры проекта: {self.project_root}")

        for root, dirs, _ in os.walk(self.project_root):
            # Фильтруем исключенные директории
            dirs[:] = [d for d in dirs if not self.is_excluded(os.path.join(root, d))]

            # Определяем тип каталога Yii2 (контроллеры, модели, представления, конфиги)
            directory_type = self.detect_directory_type(root)
            if directory_type:
                logger.info(f"Обработка каталога: {root} как {directory_type}")
                self.process_directory(root, directory_type)

    def detect_directory_type(self, directory):
        """
        Определяет тип каталога по Yii2 структуре.
        :param directory: Путь к каталогу.
        :return: Тип каталога (controllers, models, views, config, migrations, widgets, helpers, modules, assets) или None.
        """
        directory_lower = directory.lower()

        if "controllers" in directory_lower:
            return "controllers"
        elif "models" in directory_lower:
            return "models"
        elif "views" in directory_lower:
            return "views"
        elif "config" in directory_lower:
            return "config"
        elif "migrations" in directory_lower:
            return "migrations"
        elif "widgets" in directory_lower:
            return "widgets"
        elif "helpers" in directory_lower:
            return "helpers"
        elif "modules" in directory_lower:
            return "modules"
        elif "assets" in directory_lower:
            return "assets"
        else:
            return None

    def process_directory(self, directory, directory_type):
        """
        Обрабатывает файлы PHP в указанном каталоге.
        """
        files = get_all_files(directory, extensions=["php"], exclude_dirs=self.excluded_dirs)
        logger.info(f"Найдено {len(files)} PHP файлов в каталоге {directory}")

        for file_path in files:
            logger.info(f"Обработка файла: {file_path}")
            try:
                # Вызываем PHP-парсер
                parsed_data = parse_php_code(file_path, self.project_root)

                # Формируем корневой элемент для файла
                file_metadata = {
                    "id": generate_id(),
                    "type": "file",
                    "name": os.path.basename(file_path),
                    "description": f"{directory_type.capitalize()} file: {os.path.basename(file_path)}",
                    "code": None,  # Исходный код можно опустить, чтобы не перегружать файл
                    "metadata": {
                        "source": os.path.relpath(file_path, self.project_root),
                        "file_name": os.path.splitext(os.path.basename(file_path))[0],
                        "file_extension": ".php",
                        "file_type": "php",
                        "timestamp": datetime.now().isoformat()
                    },
                    "chunks": []  # Здесь будут вложенные классы, функции и зависимости
                }

                # Добавляем классы как вложенные чанки
                for class_data in parsed_data.get("classes", []):
                    class_chunk = {
                        "id": generate_id(),
                        "type": "class",
                        "name": class_data.get("name"),
                        "description": f"Class {class_data.get('name')}",
                        "code": class_data.get("code"),
                        "methods": [],  # Методы будут вложены
                    }

                    # Разделяем методы как вложенные чанки в класс
                    for method_data in class_data.get("methods", []):
                        method_chunk = {
                            "id": generate_id(),
                            "type": "method",
                            "name": method_data.get("name"),
                            "description": f"Method {method_data.get('name')} in class {class_data.get('name')}",
                            "code": method_data.get("code"),
                            "start_line": method_data.get("start_line"),
                            "end_line": method_data.get("end_line"),
                        }
                        class_chunk["methods"].append(method_chunk)

                    file_metadata["chunks"].append(class_chunk)

                # Добавляем глобальные функции как вложенные чанки в файл
                for function_data in parsed_data.get("functions", []):
                    function_chunk = {
                        "id": generate_id(),
                        "type": "function",
                        "name": function_data.get("name"),
                        "description": f"Global function {function_data.get('name')}",
                        "code": function_data.get("code"),
                        "start_line": function_data.get("start_line"),
                        "end_line": function_data.get("end_line"),
                    }
                    file_metadata["chunks"].append(function_chunk)

                # Добавляем зависимости как отдельный список
                dependencies = parsed_data.get("dependencies", [])
                if dependencies:
                    dependency_chunk = {
                        "id": generate_id(),
                        "type": "dependencies",
                        "description": "List of dependencies",
                        "dependencies": dependencies
                    }
                    file_metadata["chunks"].append(dependency_chunk)

                # Сохраняем результат
                self.save_chunks([file_metadata], f"yii2_{directory_type}")
                logger.info(f"Файл успешно обработан: {file_path}")

            except FileNotFoundError as e:
                logger.error(f"Ошибка: PHP парсер не найден. {e}")
            except RuntimeError as e:
                logger.error(f"Ошибка выполнения PHP парсера для файла {file_path}: {e}")
            except ValueError as e:
                logger.error(f"Ошибка парсинга файла {file_path}: {e}")
            except Exception as e:
                logger.error(f"Неизвестная ошибка при обработке файла {file_path}: {e}")
