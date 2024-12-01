import os
from abc import ABC
from formatters.json_manager import JSONManager
from utils.logger import global_logger as logger


class BaseExtractor(ABC):
    """
    Базовый класс для всех обработчиков исходного кода.
    """

    def __init__(self, project_root, output_dir, prefix, json_manager, excluded_dirs=None):
        """
        Инициализация базового обработчика.
        :param project_root: Путь к корневой директории проекта.
        :param output_dir: Путь к директории для сохранения результатов.
        :param prefix: Префикс для выходных файлов.
        :param json_manager: Экземпляр JSONManager для управления данными.
        :param excluded_dirs: Список каталогов, которые следует исключить.
        """
        # Каталоги, которые всегда должны игнорироваться
        default_excluded_dirs = [".git", ".idea"]

        # Объединяем переданные исключенные каталоги с дефолтными
        self.excluded_dirs = (excluded_dirs or []) + default_excluded_dirs

        self.project_root = project_root
        self.output_dir = output_dir
        self.prefix = prefix
        self.json_manager = json_manager  # Менеджер для сохранения данных

    def is_excluded(self, path):
        """
        Проверяет, находится ли путь в исключенных директориях.
        :param path: Путь для проверки.
        :return: True, если путь или его родительский каталог исключен.
        """
        abs_path = os.path.abspath(path)
        for excluded in self.excluded_dirs:
            excluded_path = os.path.abspath(os.path.join(self.project_root, excluded))
            if abs_path.startswith(excluded_path):
                return True
        return False

    def add_chunks(self, scope, data):
        """
        Добавляет чанки данных в указанный scope через JSONManager.
        :param scope: Название области данных.
        :param data: Данные для добавления.
        """
        self.json_manager.add_data(scope, data)
        logger.info(f"Добавлено {len(data) if isinstance(data, list) else 1} чанков в область: {scope}")
