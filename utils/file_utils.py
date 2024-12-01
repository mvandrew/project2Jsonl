import os

def get_python_files(directory, excluded_dirs):
    """Рекурсивно находит Python файлы, исключая определённые каталоги."""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Исключить каталоги
        dirs[:] = [d for d in dirs if os.path.join(root, d) not in excluded_dirs]
        # Добавить Python файлы
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files
