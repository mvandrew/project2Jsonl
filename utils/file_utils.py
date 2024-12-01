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
