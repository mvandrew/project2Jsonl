import os
from extractors.base_extractor import BaseExtractor
from utils.file_utils import get_all_files

class Yii2Extractor(BaseExtractor):
    def __init__(self, project_root, output_dir, prefix, chunk_size=5000, excluded_dirs=None):
        super().__init__(project_root, output_dir, prefix)
        self.chunk_size = chunk_size
        self.excluded_dirs = excluded_dirs or []

    def extract(self):
        """
        Обрабатывает всю структуру каталогов проекта, включая вложенные модули,
        за исключением каталогов, указанных в excluded_dirs.
        """
        print(f"Starting extraction in: {self.project_root}")

        # Преобразуем исключенные каталоги в набор путей для быстрого поиска
        excluded_names = {name.strip() for name in self.excluded_dirs}

        for root, dirs, _ in os.walk(self.project_root):
            # Отфильтровываем каталоги, которые следует исключить
            dirs[:] = [
                d for d in dirs
                if d not in excluded_names and not any(excluded in os.path.join(root, d) for excluded in excluded_names)
            ]

            # Определяем типы Yii2 (контроллеры, модели, конфиги, представления)
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
        files = get_all_files(directory, extensions=["php"], exclude_dirs=self.excluded_dirs)
        print(f"Processing directory: {directory} ({directory_type})")
        print(f"Found {len(files)} PHP files in {directory}")

        for file_path in files:
            print(f"Processing file: {file_path}")
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    chunks = self.split_into_chunks(content)
                    data = [
                        {
                            "chunk_type": directory_type,
                            "file_path": file_path,
                            "description": f"{directory_type.capitalize()} code chunk from {os.path.basename(file_path)}",
                            "code": chunk,
                        }
                        for chunk in chunks
                    ]
                    self.save_chunks(data, f"yii2_{directory_type}")
                    print(f"Successfully processed file: {file_path}")
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")

    def split_into_chunks(self, content):
        # Простое разбиение на чанки по размеру
        return [content[i:i+self.chunk_size] for i in range(0, len(content), self.chunk_size)]
