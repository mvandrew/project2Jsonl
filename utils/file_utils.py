import os


def get_python_files(directory, excluded_dirs):
    """
    Рекурсивно находит Python файлы, исключая определённые каталоги.

    :param directory: Корневая директория для поиска
    :param excluded_dirs: Список относительных путей для исключения
    :return: Список путей к файлам
    """
    python_files = []

    # Преобразуем исключенные директории в абсолютные пути один раз
    excluded_dirs_abs = {os.path.abspath(os.path.join(directory, ex)) for ex in excluded_dirs}

    for root, dirs, files in os.walk(directory):
        abs_root = os.path.abspath(root)

        # Пропустить текущий каталог, если он в списке исключенных
        if abs_root in excluded_dirs_abs:
            dirs[:] = []  # Прекратить обход поддиректорий
            continue

        # Удалить из обхода подкаталоги, которые входят в список исключенных
        dirs[:] = [d for d in dirs if os.path.abspath(os.path.join(root, d)) not in excluded_dirs_abs]

        # Добавить только Python файлы
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(abs_root, file))

    return python_files


def get_all_files(directory, extensions=None, exclude_dirs=None):
    """
    Рекурсивно получает все файлы из указанной директории, используя генератор.

    :param directory: Путь к корневой директории.
    :param extensions: Список расширений файлов для фильтрации (например, ['php', 'js']).
                       Если None, возвращаются файлы всех типов.
    :param exclude_dirs: Список имён директорий, которые нужно исключить.
                         Например, ['node_modules', '__pycache__'].
    :yield: Путь к файлу.
    """
    exclude_dirs = set(exclude_dirs or [])  # Преобразуем в множество для быстрого поиска

    for root, dirs, filenames in os.walk(directory):
        # Удаляем из обхода директории, которые совпадают с именами в exclude_dirs
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        # Генератор для фильтрации и возврата файлов
        yield from (
            os.path.join(root, filename)
            for filename in filenames
            if extensions is None or any(filename.endswith(f".{ext}") for ext in extensions)
        )
