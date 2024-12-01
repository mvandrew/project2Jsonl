import os
from abc import ABC

from formatters.json_formatter import jsonl_to_human_readable_json
from formatters.jsonl_formatter import save_to_jsonl
from utils.logger import global_logger as logger

class BaseExtractor(ABC):
    """
    Базовый класс для всех обработчиков исходного кода.
    """
    def __init__(self, project_root, output_dir, prefix, excluded_dirs=None):
        """
        Инициализация базового обработчика.
        :param project_root: Путь к корневой директории проекта.
        :param output_dir: Путь к директории для сохранения результатов.
        :param prefix: Префикс для выходных файлов.
        :param excluded_dirs: Список каталогов, которые следует исключить.
        """
        # Каталоги, которые всегда должны игнорироваться
        default_excluded_dirs = [".git", ".idea"]

        # Объединяем переданные исключенные каталоги с дефолтными
        self.excluded_dirs = (excluded_dirs or []) + default_excluded_dirs

        self.project_root = project_root
        self.output_dir = output_dir
        self.prefix = prefix

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

    def save_chunks(self, data, file_suffix, group_by=None):
        """
        Сохранение данных в JSONL и человекопонятный JSON файл.
        :param data: Список словарей, представляющих чанки данных.
        :param file_suffix: Суффикс имени файла (например, 'yii2').
        :param group_by: Ключ для группировки данных в человекопонятный JSON (например, "file_path").
        """
        # Сохранение в JSONL
        output_file = os.path.join(self.output_dir, f"{self.prefix}_{file_suffix}.jsonl")
        save_to_jsonl(data, output_file)
        logger.info(f"Сохранено {len(data)} чанков в JSONL файл: {output_file}")

        # Сохранение в человекопонятный JSON
        human_readable_dir = os.path.join(self.output_dir, "human_readable")
        os.makedirs(human_readable_dir, exist_ok=True)
        output_human_file = os.path.join(human_readable_dir, f"{self.prefix}_{file_suffix}.json")
        jsonl_to_human_readable_json(output_file, output_human_file, group_by=group_by)
        logger.info(f"Сохранено в человекопонятный JSON файл: {output_human_file}")
