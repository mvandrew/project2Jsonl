import os
from extractors.base_extractor import BaseExtractor
from parsers.php_parser import parse_php_code
from utils.file_utils import get_all_files
from utils.logger import global_logger as logger


class Yii2Extractor(BaseExtractor):
    """
    Обработчик для извлечения данных из Yii2 проектов.
    """

    def __init__(self, project_root, output_dir, prefix, json_manager, chunk_size=5000, excluded_dirs=None, included_files=None):
        """
        Инициализация обработчика Python-кода.

        :param project_root: str
            Путь к корневой директории проекта.
        :param output_dir: str
            Путь к директории для сохранения результатов.
        :param prefix: str
            Префикс для выходных файлов.
        :param json_manager: JSONManager
            Экземпляр JSONManager для управления данными.
        :param chunk_size: int, optional
            Размер порции данных для обработки (по умолчанию 5000).
        :param excluded_dirs: list[str], optional
            Список каталогов, которые следует исключить при обработке.
            Если не задано, используется пустой список.
            Дополнительно всегда исключаются:
                - ".git"
                - ".idea"
        :param included_files: list[str], optional
            Список файлов для обработки. Если указан, обрабатываются только файлы
            из этого списка (с указанием их относительных путей от корня проекта).
            Если не задан, обрабатываются все файлы, кроме тех, что находятся в excluded_dirs.

        Примечание:
        - excluded_dirs: объединяет переданные исключённые каталоги с дефолтными
          ".git" и ".idea".
        - included_files: предназначен для отладки или частичной обработки проекта.
        """
        super().__init__(project_root, output_dir, prefix, json_manager, chunk_size, excluded_dirs, included_files)

    def extract(self):
        """
        Обрабатывает всю структуру каталогов проекта, включая вложенные модули,
        за исключением каталогов, указанных в excluded_dirs.
        Если включённые файлы (included_files) заданы, обрабатываются только они.
        """
        logger.info(f"Начало обработки структуры проекта: {self.project_root}")

        if self.included_files:
            logger.info("Обработка только указанных файлов.")
            for relative_file_path in self.included_files:
                file_path = os.path.join(self.project_root, relative_file_path)

                # Проверяем существование файла
                if not os.path.isfile(file_path):
                    logger.warning(f"Файл {file_path} не существует. Пропуск.")
                    continue

                # Проверяем расширение файла
                if not file_path.endswith(".php"):
                    logger.warning(f"Файл {file_path} не является PHP файлом. Пропуск.")
                    continue

                logger.info(f"Обработка файла из списка: {file_path}")
                self.process_file(file_path, directory_type=self.detect_directory_type(os.path.dirname(file_path)))
            return

        # Если included_files не заданы, обрабатываем всю структуру проекта
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

        for file_path in files:
            self.process_file(file_path, directory_type)


    def process_file(self, file_path, directory_type):
        logger.info(f"Обработка файла: {file_path}")
        try:
            # Вызываем PHP-парсер для анализа файла
            parsed_file_data = parse_php_code(file_path=file_path, source_dir=self.project_root, project_type="yii2")

            # Проверяем, что парсер вернул корректные данные
            if not parsed_file_data or not isinstance(parsed_file_data, list):
                logger.warning(f"Некорректный формат данных от парсера для файла {file_path}. Пропуск.")
                return

            # Добавляем данные в область через JSONManager
            self.add_chunks(f"yii2_{directory_type}", parsed_file_data)
            logger.info(f"Файл успешно обработан: {file_path}")

        except FileNotFoundError as e:
            logger.error(f"Ошибка: PHP парсер не найден. {e}")
        except RuntimeError as e:
            logger.error(f"Ошибка выполнения PHP парсера для файла {file_path}: {e}")
        except ValueError as e:
            logger.error(f"Ошибка парсинга файла {file_path}: {e}")
        except Exception as e:
            logger.error(f"Неизвестная ошибка при обработке файла {file_path}: {e}")
