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
                # Вызываем PHP-парсер для анализа файла
                parsed_file_data = parse_php_code(file_path, self.project_root)

                # Проверяем, что парсер вернул корректные данные
                if not parsed_file_data or not isinstance(parsed_file_data, list):
                    logger.warning(f"Некорректный формат данных от парсера для файла {file_path}. Пропуск.")
                    continue

                # Сохраняем результат в формате JSONL
                self.save_chunks(parsed_file_data, f"yii2_{directory_type}")
                logger.info(f"Файл успешно обработан: {file_path}")

            except FileNotFoundError as e:
                logger.error(f"Ошибка: PHP парсер не найден. {e}")
            except RuntimeError as e:
                logger.error(f"Ошибка выполнения PHP парсера для файла {file_path}: {e}")
            except ValueError as e:
                logger.error(f"Ошибка парсинга файла {file_path}: {e}")
            except Exception as e:
                logger.error(f"Неизвестная ошибка при обработке файла {file_path}: {e}")
