import os
import logging
from abc import ABC, abstractmethod
from formatters.jsonl_formatter import save_to_jsonl

class BaseExtractor(ABC):
    """
    Базовый класс для всех обработчиков исходного кода.
    """
    def __init__(self, project_root, output_dir, prefix):
        """
        Инициализация базового обработчика.
        :param project_root: Путь к корневой директории проекта.
        :param output_dir: Путь к директории для сохранения результатов.
        :param prefix: Префикс для выходных файлов.
        """
        self.project_root = project_root
        self.output_dir = output_dir
        self.prefix = prefix
        self.logger = logging.getLogger(self.__class__.__name__)
        self.setup_logging()

    def setup_logging(self):
        """
        Настройка логирования.
        """
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    @abstractmethod
    def extract(self):
        """
        Абстрактный метод для извлечения данных.
        Должен быть реализован в подклассах.
        """
        pass

    def save_chunks(self, data, file_suffix):
        """
        Сохранение данных в JSONL файл с использованием formatters.jsonl_formatter.
        :param data: Список словарей, представляющих чанки данных.
        :param file_suffix: Суффикс имени файла (например, 'yii2').
        """
        output_file = os.path.join(self.output_dir, f"{self.prefix}_{file_suffix}.jsonl")
        save_to_jsonl(data, output_file)
        self.logger.info(f"Сохранено {len(data)} чанков в файл: {output_file}")
