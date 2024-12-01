import json

def jsonl_to_human_readable_json(jsonl_file, output_json_file, group_by=None):
    """
    Универсальная функция для преобразования JSONL в человекопонятный JSON.

    :param jsonl_file: Путь к входному файлу JSONL.
    :param output_json_file: Путь к выходному файлу JSON.
    :param group_by: Ключ для группировки данных (например, "file_path" или "metadata.source").
                     Если None, данные сохраняются как есть.
    """
    grouped_data = {}

    # Чтение JSONL-файла
    with open(jsonl_file, 'r', encoding='utf-8') as file:
        for line in file:
            chunk = json.loads(line.strip())

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
        grouped_data = {"ungrouped": []}  # Добавляем пустую группу, если данные отсутствуют

    # Формирование выходной структуры
    output_data = grouped_data if group_by else grouped_data["ungrouped"]

    # Сохранение в человекопонятный JSON
    with open(output_json_file, 'w', encoding='utf-8') as json_file:
        json.dump(output_data, json_file, ensure_ascii=False, indent=4)
