import ast

def parse_python_code(file_path):
    """Парсит Python-файл и извлекает классы, функции, глобальные переменные."""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    tree = ast.parse(content)
    chunks = []

    # Извлечение классов
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            chunks.append({
                "chunk_type": "class",
                "name": node.name,
                "start_line": node.lineno,
                "end_line": getattr(node, 'end_lineno', None),
                "code": ast.get_source_segment(content, node),
                "description": f"Class definition: {node.name}"
            })

        elif isinstance(node, ast.FunctionDef):
            chunks.append({
                "chunk_type": "function",
                "name": node.name,
                "start_line": node.lineno,
                "end_line": getattr(node, 'end_lineno', None),
                "code": ast.get_source_segment(content, node),
                "description": f"Function definition: {node.name}"
            })

    return chunks
