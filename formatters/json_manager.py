import json
import os
from collections import defaultdict


class JSONManager:
    """
    Класс для работы с JSON и JSONL файлами с поддержкой нескольких областей данных (scopes).
    """

    def __init__(self, output_directory="output"):
        """
        Инициализация менеджера JSON/JSONL с поддержкой нескольких областей.

        :param output_directory: Директория, куда будут сохраняться файлы.
        """
        self.data = defaultdict(list)
        self.output_directory = output_directory
        os.makedirs(self.output_directory, exist_ok=True)

    def add_data(self, scope, entries):
        """
        Добавляет данные в указанную область.

        :param scope: Название области данных (например, "files" или "classes").
        :param entries: Список данных для добавления или структура данных.
        """
        if not isinstance(entries, (list, dict)):
            raise ValueError("Entries must be a list or a dictionary.")

        if isinstance(entries, dict):
            self.data[scope].append(entries)
        else:
            self.data[scope].extend(entries)

    def _save_jsonl(self, scope, output_file):
        """
        Сохраняет данные из указанной области в формате JSONL.

        :param scope: Название области данных.
        :param output_file: Путь к выходному файлу JSONL.
        """
        if scope not in self.data:
            raise KeyError(f"No data found for scope '{scope}'.")

        with open(output_file, 'w', encoding='utf-8') as file:
            for entry in self.data[scope]:
                file.write(json.dumps(entry, ensure_ascii=False) + '\n')

    def _save_json(self, scope, output_file, group_by=None):
        """
        Сохраняет данные из указанной области в человекопонятный JSON.

        :param scope: Название области данных.
        :param output_file: Путь к выходному файлу JSON.
        :param group_by: Ключ для группировки данных (например, "file_path" или "metadata.source").
                         Если None, данные сохраняются как есть.
        """
        if scope not in self.data:
            raise KeyError(f"No data found for scope '{scope}'.")

        grouped_data = {}

        # Группировка данных
        for chunk in self.data[scope]:
            if group_by:
                # Достать значение для группировки
                group_key = chunk
                for part in group_by.split('.'):
                    group_key = group_key.get(part)
                    if group_key is None:
                        raise KeyError(f"Grouping key '{group_by}' not found in chunk: {chunk}")

                # Инициализация группы, если её ещё нет
                if group_key not in grouped_data:
                    grouped_data[group_key] = {
                        "group_key": group_key,
                        "items": []
                    }

                # Добавление текущего чанка в группу
                grouped_data[group_key]["items"].append(chunk)
            else:
                # Если группировка не указана, добавляем в общий список
                grouped_data.setdefault("ungrouped", []).append(chunk)

        # Проверяем, есть ли данные
        if not grouped_data:
            grouped_data = {"ungrouped": []}

        # Формирование выходной структуры
        output_data = grouped_data if group_by else grouped_data["ungrouped"]

        # Сохранение в человекопонятный JSON
        with open(output_file, 'w', encoding='utf-8') as json_file:
            json.dump(output_data, json_file, ensure_ascii=False, indent=4)

    def save_all(self, group_by=None):
        """
        Сохраняет все области данных в соответствующие файлы JSON и JSONL.

        :param group_by: Ключ для группировки данных в человекопонятном JSON (например, "file_path" или "metadata.source").
                         Если None, данные сохраняются как есть.
        """
        for scope, entries in self.data.items():
            # Определяем пути к файлам
            jsonl_file = os.path.join(self.output_directory, f"{scope}.jsonl")
            json_file = os.path.join(self.output_directory, f"{scope}.json")

            # Сохраняем в JSONL
            self._save_jsonl(scope, jsonl_file)

            # Сохраняем в человекопонятный JSON
            self._save_json(scope, json_file, group_by)

    def reset_scope(self, scope):
        """
        Очищает данные в указанной области.

        :param scope: Название области данных.
        """
        if scope in self.data:
            self.data[scope] = []

    def clear_all(self):
        """
        Очищает все области данных.
        """
        self.data.clear()

    def get_data(self, scope):
        """
        Возвращает данные из указанной области.

        :param scope: Название области данных.
        :return: Список данных.
        """
        return self.data.get(scope, [])
