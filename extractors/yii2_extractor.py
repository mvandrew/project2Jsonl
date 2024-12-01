import os
from extractors.base_extractor import BaseExtractor
from parsers.php_parser import parse_php_code
from utils.file_utils import get_all_files

class Yii2Extractor(BaseExtractor):
    def __init__(self, project_root, output_dir, prefix, chunk_size=5000, excluded_dirs=None):
        super().__init__(project_root, output_dir, prefix, excluded_dirs)
        self.chunk_size = chunk_size

    def extract(self):
        """
        Обрабатывает всю структуру каталогов проекта, включая вложенные модули,
        за исключением каталогов, указанных в excluded_dirs.
        """
        print(f"Starting extraction in: {self.project_root}")

        for root, dirs, _ in os.walk(self.project_root):
            # Фильтруем исключенные директории
            dirs[:] = [d for d in dirs if not self.is_excluded(os.path.join(root, d))]

            # Определяем тип каталога Yii2 (контроллеры, модели, представления, конфиги)
            directory_type = self.detect_directory_type(root)
            if directory_type:
                print(f"Processing directory: {root} as {directory_type}")
                self.process_directory(root, directory_type)

    def detect_directory_type(self, directory):
        """
        Определяет тип каталога по Yii2 структуре.
        :param directory: Путь к каталогу.
        :return: Тип каталога (controllers, models, views, config) или None.
        """
        if "controllers" in directory.lower():
            return "controllers"
        elif "models" in directory.lower():
            return "models"
        elif "views" in directory.lower():
            return "views"
        elif "config" in directory.lower():
            return "config"
        else:
            return None

    def process_directory(self, directory, directory_type):
        """
        Обрабатывает файлы PHP в указанном каталоге.
        """
        files = get_all_files(directory, extensions=["php"], exclude_dirs=self.excluded_dirs)
        print(f"Processing directory: {directory} ({directory_type})")
        print(f"Found {len(files)} PHP files in {directory}")

        for file_path in files:
            print(f"Processing file: {file_path}")
            try:
                # Вызываем PHP-парсер
                chunks = parse_php_code(file_path, self.project_root)

                # Обновляем метаданные для всех чанков
                for chunk in chunks:
                    chunk["chunk_type"] = directory_type
                    chunk["file_path"] = file_path
                    chunk["description"] = f"{directory_type.capitalize()} code chunk from {os.path.basename(file_path)}"

                # Сохраняем чанки
                self.save_chunks(chunks, f"yii2_{directory_type}")
                print(f"Successfully processed file: {file_path}")
            except FileNotFoundError as e:
                print(f"Error: PHP parser script not found. {e}")
            except RuntimeError as e:
                print(f"Runtime error while parsing file {file_path}: {e}")
            except ValueError as e:
                print(f"Parsing error in file {file_path}: {e}")
            except Exception as e:
                print(f"Unexpected error processing file {file_path}: {e}")
