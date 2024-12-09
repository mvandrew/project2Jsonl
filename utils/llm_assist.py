import json
import requests
import os
from dotenv import load_dotenv
from utils.query_cache import get_cached_response, save_response

class LLMAssist:
    """
    Класс для взаимодействия с LM Studio через эндпоинт /v1/chat/completions.
    """

    def __init__(self, project_type):
        """
        Инициализация LLMAssist с загрузкой параметров из .env файла.

        :param project_type: Тип проекта (например, "php", "python").
        """
        # Загрузка переменных из .env файла
        load_dotenv()

        self.server_url = os.getenv("LLM_SERVER_URL")
        self.model_name = os.getenv("LLM_MODEL_NAME")
        self.project_type = project_type
        self.max_code_length = int(os.getenv("MAX_CODE_LENGTH", 3500))  # Используем значение из .env или значение по умолчанию
        self.max_tokens = int(os.getenv("MAX_TOKENS", 256))

        # Проверка обязательных параметров
        self.success = bool(self.server_url and self.model_name)

    def query(self, user_message, system_message=None, temperature=0.7, max_tokens=None):
        """
        Отправляет запрос на LM Studio сервер через /v1/chat/completions.

        :param user_message: Сообщение пользователя.
        :param system_message: Сообщение системы (контекст, необязательно).
        :param temperature: Уровень случайности генерации ответа.
        :param max_tokens: Максимальное количество токенов в ответе.
        :return: Ответ модели в виде строки.
        """
        if not self.success:
            raise RuntimeError("Не удалось инициализировать LLMAssist.")

        # Формирование сообщений для модели
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": user_message})

        # Если max_tokens не задан, используем self.max_tokens
        if max_tokens is None:
            max_tokens = self.max_tokens

        # Формирование тела запроса
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        # Преобразование payload в строку для использования в кэшировании
        cache_key = json.dumps(payload, sort_keys=True)

        # Проверка необходимости использования кэша
        use_cache = os.getenv("USE_CACHE", "true").lower() == "true"
        if use_cache:
            cached_response = get_cached_response(cache_key)
            if cached_response:
                print("Ответ получен из кэша.")
                return cached_response

        try:
            # Логируем запрос
            print(f"Отправка запроса: {payload}")

            # Отправляем запрос на /v1/chat/completions
            response = requests.post(self.server_url, json=payload)

            # Логируем ответ
            print(f"Ответ сервера: {response.text}")

            # Проверка кода ответа
            if response.status_code != 200:
                raise RuntimeError(f"Ошибка запроса к LLM: {response.status_code} - {response.text}")

            # Парсинг JSON-ответа
            response_data = response.json()

            # Извлечение текста из choices[0]["message"]["content"]
            if "choices" in response_data and len(response_data["choices"]) > 0:
                content = response_data["choices"][0]["message"].get("content", "Нет текста в ответе.")

                # Сохраняем в кэш, если кэширование включено
                if use_cache:
                    save_response(cache_key, content)

                return content
            else:
                raise ValueError(f"Некорректный ответ модели: {response_data}")

        except Exception as e:
            raise RuntimeError(f"Ошибка при взаимодействии с LLM: {e}")

    def describe_file(self, file_name, file_code):
        """
        Описывает назначение файла на основе его имени и содержимого.

        :param file_name: Имя файла.
        :param file_code: Содержимое файла.
        :return: Описание назначения файла.
        """
        if not self.success:
            raise RuntimeError("Не удалось инициализировать LLMAssist.")

        # Если содержимое файла пустое
        if not file_code.strip():
            user_message = f"Определи назначение PHP-файла {file_name} в проекте {self.project_type}. Файл пуст."
        else:
            # Разбиваем код на части
            chunks = [file_code[i:i + self.max_code_length] for i in range(0, len(file_code), self.max_code_length)]
            if len(chunks) == 1:
                # Один чанк, отправляем всё в одном сообщении
                user_message = (
                    f"Опиши на русском языке назначение PHP-файла {file_name} в проекте {self.project_type}.\n"
                    f"Содержимое:\n\n{chunks[0]}"
                )
            else:
                # Несколько чанков, готовим сообщение с разделением
                user_message = f"Опиши на русском языке назначение PHP-файла {file_name}. Содержимое файла разделено на части:\n"
                for idx, chunk in enumerate(chunks):
                    user_message += f"Часть {idx + 1}/{len(chunks)}:\n\n{chunk}\n"

        system_message = (
            f"Вы ассистент для анализа PHP-файлов проекта {self.project_type}. "
            f"Определяйте назначение файлов, классов и методов кратко и по существу."
        )

        return self.query(user_message=user_message, system_message=system_message, temperature=0.4)

    def describe_class(self, class_name, class_code):
        """
        Описывает назначение класса на основе его имени и содержимого.

        :param class_name: Имя класса.
        :param class_code: Содержимое кода класса.
        :return: Описание назначения класса.
        """
        if not self.success:
            raise RuntimeError("Не удалось инициализировать LLMAssist.")

        # Если содержимое класса пустое
        if not class_code.strip():
            user_message = f"Определи назначение PHP-класса {class_name} в проекте {self.project_type}. Код класса отсутствует или пуст."
        else:
            # Разбиваем код на части
            chunks = [class_code[i:i + self.max_code_length] for i in range(0, len(class_code), self.max_code_length)]
            if len(chunks) == 1:
                # Один чанк, отправляем всё в одном сообщении
                user_message = (
                    f"Опиши на русском языке назначение PHP-класса {class_name} в проекте {self.project_type}.\n"
                    f"Содержимое:\n\n{chunks[0]}"
                )
            else:
                # Несколько чанков, готовим сообщение с разделением
                user_message = f"Опиши на русском языке назначение PHP-класса {class_name}. Содержимое класса разделено на части:\n"
                for idx, chunk in enumerate(chunks):
                    user_message += f"Часть {idx + 1}/{len(chunks)}:\n\n{chunk}\n"

        system_message = (
            f"Вы ассистент для анализа PHP-классов проекта {self.project_type}. "
            f"Определяйте назначение классов, методов и их связей кратко и по существу."
        )

        return self.query(user_message=user_message, system_message=system_message, temperature=0.4)

    def describe_class_method(self, method_name, method_code, class_name, class_description):
        """
        Описывает назначение метода класса на основе его имени, содержимого и описания класса.

        :param method_name: Имя метода.
        :param method_code: Содержимое кода метода.
        :param class_name: Имя класса, к которому принадлежит метод.
        :param class_description: Описание назначения класса.
        :return: Описание назначения метода.
        """
        if not self.success:
            raise RuntimeError("Не удалось инициализировать LLMAssist.")

        # Если содержимое метода пустое
        if not method_code.strip():
            user_message = (
                f"Определи назначение метода {method_name} в классе {class_name} проекта {self.project_type}. "
                f"Код метода отсутствует или пуст. Класс описан как: {class_description}."
            )
        else:
            # Разбиваем код на части
            chunks = [method_code[i:i + self.max_code_length] for i in range(0, len(method_code), self.max_code_length)]
            if len(chunks) == 1:
                # Один чанк, отправляем всё в одном сообщении
                user_message = (
                    f"Опиши на русском языке назначение метода {method_name} в классе {class_name} проекта {self.project_type}.\n"
                    f"Описание класса: {class_description}.\nСодержимое:\n\n{chunks[0]}"
                )
            else:
                # Несколько чанков, готовим сообщение с разделением
                user_message = (
                    f"Опиши на русском языке назначение метода {method_name} в классе {class_name}. "
                    f"Описание класса: {class_description}. Содержимое метода разделено на части:\n"
                )
                for idx, chunk in enumerate(chunks):
                    user_message += f"Часть {idx + 1}/{len(chunks)}:\n\n{chunk}\n"

        system_message = (
            f"Вы ассистент для анализа PHP-классов и их методов проекта {self.project_type}. "
            f"Определяйте назначение методов кратко и по существу, с учетом контекста класса."
        )

        return self.query(user_message=user_message, system_message=system_message, temperature=0.4)

    def describe_global_function(self, function_name, function_code, file_name):
        """
        Описывает назначение глобальной функции на основе её имени и содержимого.

        :param function_name: Имя функции.
        :param function_code: Содержимое кода функции.
        :param file_name: Имя файла, в котором определена функция.
        :return: Описание назначения функции.
        """
        if not self.success:
            raise RuntimeError("Не удалось инициализировать LLMAssist.")

        # Если содержимое функции пустое
        if not function_code.strip():
            user_message = (
                f"Определи назначение глобальной функции {function_name}, определённой в файле {file_name} проекта {self.project_type}. "
                f"Код функции отсутствует или пуст."
            )
        else:
            # Разбиваем код на части
            chunks = [function_code[i:i + self.max_code_length] for i in
                      range(0, len(function_code), self.max_code_length)]
            if len(chunks) == 1:
                # Один чанк, отправляем всё в одном сообщении
                user_message = (
                    f"Опиши на русском языке назначение глобальной функции {function_name}, определённой в файле {file_name} проекта {self.project_type}.\n"
                    f"Содержимое:\n\n{chunks[0]}"
                )
            else:
                # Несколько чанков, готовим сообщение с разделением
                user_message = (
                    f"Опиши на русском языке назначение глобальной функции {function_name}, определённой в файле {file_name}. "
                    f"Содержимое функции разделено на части:\n"
                )
                for idx, chunk in enumerate(chunks):
                    user_message += f"Часть {idx + 1}/{len(chunks)}:\n\n{chunk}\n"

        system_message = (
            f"Вы ассистент для анализа PHP-файлов и их глобальных функций в проекте {self.project_type}. "
            f"Определяйте назначение функций кратко и по существу."
        )

        return self.query(user_message=user_message, system_message=system_message, temperature=0.4)
