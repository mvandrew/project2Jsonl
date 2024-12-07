import unittest
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Установка PYTHONPATH из .env
PYTHONPATH = os.getenv("PYTHONPATH", "")
if PYTHONPATH and PYTHONPATH not in os.sys.path:
    os.sys.path.insert(0, PYTHONPATH)

from extractors.bitrix_extractor import BitrixExtractor  # Импорт после настройки PYTHONPATH
from unittest.mock import MagicMock


class TestBitrixExtractor(unittest.TestCase):
    def setUp(self):
        # Вычисляем путь к корню проекта относительно текущего файла
        tests_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(tests_dir, ".."))
        env_path = os.path.join(project_root, ".env")

        # Загружаем переменные окружения из .env
        load_dotenv(env_path)

        # Загружаем путь к проекту из .env
        self.project_root = os.getenv("SOURCE_DIR", "/default/path/to/project")
        self.excluded_dirs = os.getenv("EXCLUDED_DIRS", "").split(",")

        # Создаем экземпляр BitrixExtractor
        self.extractor = BitrixExtractor(
            project_root=self.project_root,
            output_dir="output",
            prefix="test",
            json_manager=MagicMock(),
            excluded_dirs=self.excluded_dirs
        )

        # Формируем тестовые данные с использованием корня проекта из .env
        self.test_cases = [
            (os.path.join(self.project_root, "bitrix"), True),  # Каталог исключён
            (os.path.join(self.project_root, "upload"), True),  # Каталог исключён
            (os.path.join(self.project_root, "local/.migration"), True),  # Относительный путь исключён
            (os.path.join(self.project_root, "local/php_interface/migrations"), True),  # Вложенный каталог исключён
            (os.path.join(self.project_root, "vendor"), True),  # Абсолютный путь исключён
            (os.path.join(self.project_root, "local"), False),  # Не исключено
            ("vendor", True),  # Имя каталога исключено
        ]

    def test_is_excluded(self):
        # Тестируем каждый случай
        for directory, expected in self.test_cases:
            with self.subTest(directory=directory, expected=expected):
                result = self.extractor.is_excluded(directory)
                self.assertEqual(result, expected, f"Failed for directory: {directory}")


if __name__ == "__main__":
    unittest.main()
