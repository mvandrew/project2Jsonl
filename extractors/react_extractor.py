import os
from extractors.base_extractor import BaseExtractor
from utils.file_utils import get_all_files
from utils.logger import global_logger as logger
from parsers.ts_parser import parse_ts_code  # Предполагается наличие парсера TypeScript

class ReactExtractor(BaseExtractor):
    """
    Обработчик для React проектов на TypeScript.
    """

    def __init__(self, project_root, output_dir, prefix, json_manager, chunk_size=5000, excluded_dirs=None):
        """
        Инициализация обработчика React проектов.
        :param project_root: Путь к корневой директории проекта.
        :param output_dir: Путь к директории для сохранения результатов.
        :param prefix: Префикс для выходных файлов.
        :param json_manager: Экземпляр JSONManager для управления данными.
        :param chunk_size: Максимальный размер чанка (по умолчанию 5000 символов).
        :param excluded_dirs: Список каталогов, которые следует исключить.
        """
        super().__init__(project_root, output_dir, prefix, json_manager, excluded_dirs)

    def extract(self):
        """
        Обрабатывает все файлы проекта, относящиеся к React на TypeScript.
        """
        logger.info(f"Начало обработки React проекта в директории: {self.project_root}")

        # Получаем список файлов с расширениями .ts и .tsx
        files = get_all_files(self.project_root, extensions=["ts", "tsx"], exclude_dirs=self.excluded_dirs)
        logger.info(f"Найдено {len(files)} файлов React (TypeScript) для обработки.")

        for file_path in files:
            logger.info(f"Обработка файла: {file_path}")
            try:
                # Парсим файл с помощью TypeScript парсера
                parsed_data = parse_ts_code(file_path, self.project_root)

                # Проверяем, что парсер вернул корректные данные
                if not parsed_data or not isinstance(parsed_data, list):
                    logger.warning(f"Некорректный формат данных от парсера для файла {file_path}. Пропуск.")
                    continue

                # Добавляем данные в JSONManager
                self.add_chunks("react_ts", parsed_data)
                logger.info(f"Файл успешно обработан: {file_path}")

            except FileNotFoundError as e:
                logger.error(f"Ошибка: TypeScript парсер не найден. {e}")
            except RuntimeError as e:
                logger.error(f"Ошибка выполнения TypeScript парсера для файла {file_path}: {e}")
            except ValueError as e:
                logger.error(f"Ошибка парсинга файла {file_path}: {e}")
            except Exception as e:
                logger.error(f"Неизвестная ошибка при обработке файла {file_path}: {e}")

        logger.info("Обработка React проекта завершена.")
