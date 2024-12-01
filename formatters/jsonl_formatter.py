import json

def save_to_jsonl(data, output_file):
    """Сохраняет данные в формате JSONL."""
    with open(output_file, 'w', encoding='utf-8') as file:
        for entry in data:
            file.write(json.dumps(entry, ensure_ascii=False) + '\n')
