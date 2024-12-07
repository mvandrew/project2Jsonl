import os
from abc import ABC
from formatters.json_manager import JSONManager
from utils.logger import global_logger as logger


class BaseExtractor(ABC):
    """
    Базовый класс для всех обработчиков исходного кода.
    """

    def __init__(self, project_root, output_dir, prefix, json_manager, chunk_size=5000, excluded_dirs=None, included_files=None):
        """
        Инициализация базового обработчика.

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
        # Каталоги, которые всегда должны игнорироваться
        default_excluded_dirs = [".git", ".idea"]

        # Объединяем переданные исключенные каталоги с дефолтными
        self.excluded_dirs = (excluded_dirs or []) + default_excluded_dirs

        self.project_root = project_root
        self.output_dir = output_dir
        self.prefix = prefix
        self.json_manager = json_manager  # Менеджер для сохранения данных
        self.chunk_size = chunk_size
        self.included_files = included_files

    def is_excluded(self, directory):
        """
        Проверяет, следует ли исключить данный каталог из обработки.

        :param directory: Абсолютный путь к каталогу.
        :return: bool - True, если каталог исключён, иначе False.
        """
        directory = os.path.abspath(directory)  # Путь к проверяемому каталогу
        for excluded in self.excluded_dirs:
            # Преобразуем исключение в абсолютный путь относительно корня проекта
            if not os.path.isabs(excluded):  # Если путь относительный
                excluded_path = os.path.abspath(os.path.join(self.project_root, excluded))
            else:  # Если путь уже абсолютный
                excluded_path = excluded

            # Если исключение указано как имя каталога
            if os.path.basename(directory) == excluded:
                return True

            # Если исключение указано как полный путь
            if directory == excluded_path or directory.startswith(excluded_path + os.sep):
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
