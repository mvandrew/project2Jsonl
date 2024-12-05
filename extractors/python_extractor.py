import os
from extractors.base_extractor import BaseExtractor
from parsers.python_parser import parse_python_code
from utils.file_utils import get_all_files
from utils.logger import global_logger as logger


class PythonExtractor(BaseExtractor):
    """
    Обработчик для извлечения данных из Python-кода.
    """

    def __init__(self, project_root, output_dir, prefix, json_manager, chunk_size=5000, excluded_dirs=None):
        """
        Инициализация обработчика Python-кода.
        :param project_root: Путь к корневой директории проекта.
        :param output_dir: Путь к директории для сохранения результатов.
        :param prefix: Префикс для выходных файлов.
        :param json_manager: Экземпляр JSONManager для управления данными.
        :param chunk_size: Максимальный размер чанков (по умолчанию 5000).
        :param excluded_dirs: Список каталогов, которые следует исключить.
        """
        super().__init__(project_root, output_dir, prefix, json_manager, excluded_dirs)
        self.chunk_size = chunk_size

    def extract(self):
        """
        Обрабатывает всю структуру каталогов проекта, за исключением исключенных каталогов.
        """
        logger.info(f"Начало обработки Python-кода в проекте: {self.project_root}")

        for root, dirs, _ in os.walk(self.project_root):
            # Фильтруем исключенные директории
            dirs[:] = [d for d in dirs if not self.is_excluded(os.path.join(root, d))]

            # Определяем, содержит ли каталог Python-файлы
            if self.contains_python_files(root):
                logger.info(f"Обработка каталога: {root}")
                self.process_directory(root)

    def contains_python_files(self, directory):
        """
        Проверяет, есть ли в каталоге Python-файлы.
        :param directory: Путь к каталогу.
        :return: True, если Python-файлы есть, иначе False.
        """
        return any(
            file.endswith(".py") for file in os.listdir(directory)
            if os.path.isfile(os.path.join(directory, file))
        )

    def process_directory(self, directory):
        """
        Обрабатывает файлы Python в указанном каталоге.
        """
        files = get_all_files(directory, extensions=["py"], exclude_dirs=self.excluded_dirs)
        logger.info(f"Найдено {len(files)} Python файлов в каталоге {directory}")

        for file_path in files:
            logger.info(f"Обработка файла: {file_path}")
            try:
                # Парсинг Python файла
                parsed_file_data = parse_python_code(file_path, self.project_root)

                # Проверяем, что парсер вернул корректные данные
                if not parsed_file_data or not isinstance(parsed_file_data, list):
                    logger.warning(f"Некорректный формат данных от парсера для файла {file_path}. Пропуск.")
                    continue

                # Добавляем данные в область через JSONManager
                self.add_chunks("python_files", parsed_file_data)
                logger.info(f"Файл успешно обработан: {file_path}")

            except FileNotFoundError as e:
                logger.error(f"Ошибка: Python файл не найден. {e}")
            except RuntimeError as e:
                logger.error(f"Ошибка выполнения парсера для файла {file_path}: {e}")
            except ValueError as e:
                logger.error(f"Ошибка парсинга файла {file_path}: {e}")
            except Exception as e:
                logger.error(f"Неизвестная ошибка при обработке файла {file_path}: {e}")
