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
            file_path = chunk['file_path']

            # Группировка по пути файла
            if file_path not in grouped_data:
                grouped_data[file_path] = {
                    "file_path": file_path,
                    "chunks": []
                }
            grouped_data[file_path]["chunks"].append({
                "type": chunk["chunk_type"],
                "name": chunk.get("name"),
                "start_line": chunk.get("start_line"),
                "end_line": chunk.get("end_line"),
                "description": chunk.get("description"),
                "code": chunk.get("code")
            })

    # Сохранение в человекопонятный JSON
    with open(output_json_file, 'w', encoding='utf-8') as json_file:
        json.dump(list(grouped_data.values()), json_file, ensure_ascii=False, indent=4)
