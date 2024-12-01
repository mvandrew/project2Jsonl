import json

def jsonl_to_human_readable_json(jsonl_file, output_json_file):
    """
    Преобразует JSONL в человекопонятный JSON.
    Группирует данные по файлам.
    """
    grouped_data = {}

    # Чтение JSONL-файла
    with open(jsonl_file, 'r', encoding='utf-8') as file:
        for line in file:
            chunk = json.loads(line.strip())

            # Проверить наличие обязательных ключей
            if "metadata" not in chunk or "source" not in chunk["metadata"]:
                raise KeyError(f"Missing required keys in chunk: {chunk}")

            file_path = chunk["metadata"]["source"]

            # Группировка по пути файла
            if file_path not in grouped_data:
                grouped_data[file_path] = {
                    "file_path": file_path,
                    "file_name": chunk["metadata"].get("file_name", ""),
                    "file_extension": chunk["metadata"].get("file_extension", ""),
                    "chunks": []
                }

            # Добавление данных чанка
            grouped_data[file_path]["chunks"].append({
                "id": chunk["id"],
                "type": chunk["type"],
                "name": chunk.get("name"),
                "start_line": chunk.get("start_line"),
                "end_line": chunk.get("end_line"),
                "description": chunk.get("description"),
                "code": chunk.get("code"),
                "timestamp": chunk["metadata"].get("timestamp")
            })

    # Сохранение в человекопонятный JSON
    with open(output_json_file, 'w', encoding='utf-8') as json_file:
        json.dump(list(grouped_data.values()), json_file, ensure_ascii=False, indent=4)
