import os
from extractors.base_extractor import BaseExtractor
from utils.file_utils import get_all_files

class Yii2Extractor(BaseExtractor):
    def __init__(self, project_root, output_dir, prefix, chunk_size=5000, excluded_dirs=None):
        super().__init__(project_root, output_dir, prefix)
        self.chunk_size = chunk_size
        self.excluded_dirs = excluded_dirs or []

    def extract(self):
        # Каталоги Yii2
        directories = ["controllers", "models", "views", "config"]
        for directory in directories:
            path = os.path.join(self.project_root, directory)
            if os.path.exists(path):
                self.process_directory(path, directory)

    def process_directory(self, directory, directory_type):
        files = get_all_files(directory, extensions=["php"], exclude_dirs=self.excluded_dirs)
        for file_path in files:
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

    def split_into_chunks(self, content):
        # Простое разбиение на чанки по размеру
        return [content[i:i+self.chunk_size] for i in range(0, len(content), self.chunk_size)]
